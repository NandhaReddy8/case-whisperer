import requests
import time
import sys
from typing import Optional, Dict, Any, Iterator
from urllib.parse import urlencode
from app.lib.captcha import Captcha, CaptchaError
from app.lib.entities import Court, Case, CaseType, ActType
from app.lib.parsers import parse_cases, parse_options, CaseDetailsParser
from app.core.config import settings
import hashlib
import json
import logging
from datetime import datetime, date

logger = logging.getLogger(__name__)

class RetryException(Exception):
    pass

def apimethod(path: str, court: bool = False, csrf: bool = False, action: Optional[str] = None):
    """
    Decorator for API methods with automatic retry logic.
    Based on working reference implementation pattern.
    """
    def decorator(func):
        def inner(self, *args, **kwargs):
            params = {"action_code": action} if action else {}
            if court:
                params.update(self.court.queryParams())
            # Note: CSRF not needed for eCourts API

            attempts = self.max_attempts

            while attempts > 0:
                try:
                    extra_params = func(self, *args, **kwargs) or {}
                    if len(extra_params) == 0:
                        params.update(kwargs)
                    else:
                        params.update(extra_params)
                    
                    if 'captcha' in params and params['captcha'] is None:
                        logger.error("Ran out captcha attempts")
                        raise CaptchaError("No captcha solution available")

                    response = self.session.post(
                        self.url(path), 
                        data=params, 
                        allow_redirects=False, 
                        timeout=(5, 10)
                    )
                    
                    self.validate_response(response)
                    
                    if (response.status_code == 302 and 
                        'location' in response.headers and 
                        response.headers['location'].startswith("errormsg")):
                        raise ValueError("Error: " + response.headers['location'])
                    
                    response.raise_for_status()
                    attempts = 0  # Success, exit loop
                    
                except (CaptchaError, ValueError, requests.exceptions.Timeout, 
                        requests.exceptions.ConnectionError) as e:
                    logger.warning(f"Attempt failed: {e}")
                    time.sleep(1)
                    attempts -= 1
                    if attempts == 0:
                        raise RetryException(f"Ran out of {self.max_attempts} attempts, still failed: {e}")
                except requests.exceptions.HTTPError as e:
                    logger.warning(f"HTTP error: {e}")
                    time.sleep(1)
                    attempts -= 1
                    if attempts == 0:
                        raise RetryException(f"HTTP error after {self.max_attempts} attempts: {e}")

            response.encoding = "utf-8-sig"
            return response.text
        return inner
    return decorator

class ECourtClient:
    """
    Enhanced eCourt client based on working reference implementation.
    Provides comprehensive access to eCourt services with robust error handling.
    """
    
    # Note: eCourts system does not actually use CSRF tokens
    # The hardcoded CSRF was causing errors - removed
    BASE_URL = "https://hcservices.ecourts.gov.in/ecourtindiaHC"

    def __init__(self, court: Court):
        self.session = requests.Session()
        self.court = court
        self.captcha = Captcha(self.session)
        self.max_attempts = settings.ECOURT_MAX_RETRIES

    def set_max_attempts(self, attempts: int):
        """Set maximum retry attempts"""
        self.max_attempts = attempts

    def attempts(self) -> int:
        """Get current max attempts setting"""
        return self.max_attempts

    def url(self, path: str, queryParams: Dict = None) -> str:
        """Build full URL with optional query parameters"""
        if queryParams and len(queryParams) > 0:
            return self.BASE_URL + path + "?" + urlencode(queryParams)
        return self.BASE_URL + path

    def validate_response(self, r: requests.Response):
        """Validate response for common error patterns"""
        t = r.text.upper()[0:30]
        if "ERROR" in t:
            raise ValueError("Got invalid result")
        if "INVALID CAPTCHA" in t:
            raise CaptchaError()

    # Case search methods

    @apimethod("/cases/case_no_qry.php", action="showRecords", court=True)
    def _search_case_by_cnr(self, cnr_number: str, **kwargs):
        """Internal method for CNR search - requires case details"""
        # For CNR search, we need to provide case details too
        # This is a limitation of the eCourt system
        # For now, return minimal parameters and let it fail gracefully
        return {
            "captcha": self.captcha.solve(),
            "cnr_number": cnr_number,
            "caseNoType": "new", 
            "displayOldCaseNo": "NO"
        }

    @apimethod("/cases/case_no_qry.php", action="showRecords", court=True)
    def _search_case_by_number(self, case_type: str, case_number: str, year: str, **kwargs):
        """Internal method for case number search"""
        return {
            "captcha": self.captcha.solve(),
            "case_type": case_type,
            "case_no": case_number.split("/")[0] if "/" in case_number else case_number,
            "rgyear": year,
            "caseNoType": "new",
            "displayOldCaseNo": "NO"
        }

    @apimethod("/cases/s_casetype_qry.php", action="showRecords", court=True)
    def _search_cases_by_case_type(self, case_type: str, status: str, search_year: Optional[str] = None, **kwargs):
        """Internal method for case type search"""
        assert status in ["Pending", "Disposed"]
        
        params = {
            "captcha": self.captcha.solve(),
            "f": status,
            "case_type": str(case_type)
        }
        if search_year:
            params["search_year"] = search_year
        return params

    @apimethod("/cases/s_actwise_qry.php", action="showRecords", court=True, csrf=True)
    def _search_cases_by_act_type(self, act_type: str, status: str, **kwargs):
        """Internal method for act type search"""
        return {
            "captcha": self.captcha.solve(),
            "actcode": act_type,
            "f": status
        }

    @apimethod("/cases/o_civil_case_history.php", court=True, action=None, csrf=False)
    def _get_case_history(self, case: Case, **kwargs):
        """Internal method for case history"""
        return case.expandParams()

    # Public search methods

    def search_case_by_cnr(self, cnr_number: str) -> Optional[Case]:
        """
        Search for a case using CNR number
        Note: eCourts requires case details even for CNR search
        This method will try CNR-only first, then fall back to requiring case details
        """
        try:
            # First try CNR-only search (will likely fail)
            result = self._search_case_by_cnr(cnr_number)
            cases = list(parse_cases(result))
            if cases:
                return cases[0]
            
            # If CNR-only fails, we need case details
            # For now, return None and let the caller handle it
            logger.warning(f"CNR-only search failed for {cnr_number}. eCourts requires case details.")
            return None
            
        except Exception as e:
            logger.error(f"CNR search failed: {e}")
            # Don't raise exception, return None to indicate not found
            return None

    def search_case_by_number(self, case_type: str, case_number: str, year: str) -> Optional[Case]:
        """Search for a case using case type, number and year"""
        try:
            result = self._search_case_by_number(case_type, case_number, year)
            cases = list(parse_cases(result))
            return cases[0] if cases else None
        except Exception as e:
            logger.error(f"Case number search failed: {e}")
            raise RetryException(f"Failed to search case by number: {e}")

    def search_cases_by_case_type(self, case_type: str, status: str, year: Optional[str] = None) -> Iterator[Case]:
        """Search cases by case type"""
        try:
            # Initialize the search page first
            cc = self.court.court_code or "1"
            url = self.url(f"/cases/s_casetype.php?state_cd={self.court.state_code}&dist_cd=1&court_code={cc}")
            self.session.get(url)
            
            result = self._search_cases_by_case_type(case_type, status, year)
            return parse_cases(result)
        except Exception as e:
            logger.error(f"Case type search failed: {e}")
            raise RetryException(f"Failed to search cases by case type: {e}")

    def search_cases_by_act_type(self, act_type: str, status: str) -> Iterator[Case]:
        """Search cases by act type"""
        try:
            result = self._search_cases_by_act_type(act_type, status)
            return parse_cases(result)
        except Exception as e:
            logger.error(f"Act type search failed: {e}")
            raise RetryException(f"Failed to search cases by act type: {e}")

    def get_case_history(self, case: Case) -> Dict[str, Any]:
        """Get detailed case history"""
        try:
            result = self._get_case_history(case)
            parser = CaseDetailsParser(result)
            
            # Extract next hearing date from hearings
            next_hearing_date = None
            if parser.case.hearings:
                for hearing in parser.case.hearings:
                    if hearing.next_date and hearing.next_date != "-":
                        next_hearing_date = hearing.next_date
                        break
            
            return {
                "case_details": parser.case.json(),
                "next_hearing_date": next_hearing_date,
                "current_status": parser.case.case_status or "Unknown",
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Case history failed: {e}")
            raise RetryException(f"Failed to get case history: {e}")

    def expand_case(self, case: Case) -> Case:
        """Expand case with detailed information"""
        try:
            html = self._get_case_history(case)
            parser = CaseDetailsParser(html)
            new_case = parser.case
            
            # Preserve original identifiers
            if case.case_number:
                new_case.case_number = case.case_number
            if case.token:
                new_case.token = case.token
                
            return new_case
        except Exception as e:
            logger.error(f"Case expansion failed: {e}")
            return case

    # Case type and act type methods

    @apimethod("/cases/s_casetype_qry.php", csrf=True, court=True, action="fillCaseType")
    def _get_case_types(self, **kwargs):
        """Internal method to get case types"""
        pass

    @apimethod("/cases/s_actwise_qry.php", csrf=False, court=True, action="fillActType")
    def _get_act_types(self, query: str = "", **kwargs):
        """Internal method to get act types"""
        return {"search_act": query}

    def get_case_types(self) -> Iterator[CaseType]:
        """Get available case types for this court"""
        try:
            result = self._get_case_types()
            for option in parse_options(result)[1:]:  # Skip first option (usually empty)
                if len(option) >= 2:
                    yield CaseType(
                        code=int(option[0]), 
                        description=option[1], 
                        court=self.court
                    )
        except Exception as e:
            logger.error(f"Failed to get case types: {e}")

    def get_act_types(self, query: str = "") -> Iterator[ActType]:
        """Get available act types for this court"""
        try:
            result = self._get_act_types(query)
            for option in parse_options(result)[1:]:  # Skip first option (usually empty)
                if len(option) >= 2:
                    yield ActType(
                        code=int(option[0]), 
                        description=option[1], 
                        court=self.court
                    )
        except Exception as e:
            logger.error(f"Failed to get act types: {e}")

    # Utility methods

    def calculate_case_hash(self, case_data: Dict[str, Any]) -> str:
        """Calculate hash of case data to detect changes"""
        # Remove timestamp fields that change frequently
        filtered_data = {k: v for k, v in case_data.items() 
                        if k not in ['last_updated', 'scraped_at']}
        
        case_str = json.dumps(filtered_data, sort_keys=True, default=str)
        return hashlib.md5(case_str.encode()).hexdigest()

    def download_order(self, order, court_case: Case, filename: str):
        """Download order/judgment PDF"""
        if not order.filename:
            raise ValueError("Order filename not available")
        if not court_case.case_type or not court_case.registration_number or not court_case.cnr_number:
            raise ValueError("Case details incomplete for order download")
            
        query_params = {
            "filename": order.filename,
            "caseno": f"{court_case.case_type}/{court_case.registration_number}",
            "cCode": self.court.court_code or "1",
            "state_code": self.court.state_code,
            "cino": court_case.cnr_number,
        }
        
        url = self.url("/cases/display_pdf.php", query_params)
        r = self.session.get(url)
        r.raise_for_status()
        
        with open(filename, "wb") as f:
            f.write(r.content)
        
        return len(r.content)  # Return file size for verification

    @apimethod("/cases/highcourt_causelist_qry.php", court=True, action="pulishedCauselist", csrf=False)
    def _get_cause_lists(self, date: date, **kwargs):
        """Get cause lists for a specific date"""
        dt_str = date.strftime("%d-%m-%Y")
        return {"causelist_dt": dt_str}

    def get_cause_lists(self, date: date):
        """Get cause lists for a specific date"""
        try:
            from app.lib.parsers import parse_cause_lists
            raw_res = self._get_cause_lists(date)
            return parse_cause_lists(raw_res)
        except Exception as e:
            logger.error(f"Failed to get cause lists: {e}")
            return []