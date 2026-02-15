"""
eCourt response parsers based on working reference implementation.
Handles parsing of various eCourt API responses into structured data.
"""

import re
import json
from collections import OrderedDict
from datetime import datetime, date
from typing import Optional, List, Iterator, Dict, Any
from bs4 import BeautifulSoup
import urllib.parse
import logging

from app.lib.entities import Case, Party, Hearing, Order, Objection, FIR, CaseType, ActType, Court
from app.lib.captcha import CaptchaError

logger = logging.getLogger(__name__)

def parse_date(date_str: Optional[str]) -> Optional[date]:
    """Parse date string in various formats"""
    if not date_str or date_str.strip() in ["-", "", "N/A"]:
        return None
        
    date_formats = [
        "%Y%m%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%dth %B %Y",
        "%dst %B %Y",
        "%dnd %B %Y",
        "%drd %B %Y",
        "%d %B %Y",
        "%Y-%m-%d"
    ]
    
    date_str = date_str.strip()
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt).date()
            if 1990 < parsed_date.year < 2030:
                return parsed_date
        except ValueError:
            continue
    
    logger.warning(f"Could not parse date: {date_str}")
    return None

def parse_js_call(js_call: str, signature: OrderedDict) -> Dict[str, Any]:
    """Parse JavaScript function call and return typed arguments"""
    try:
        # Extract arguments from the JavaScript function call
        args_str = re.search(r"\((.*)\)", js_call).group(1)
        args = [arg.strip() for arg in args_str.split(",")]

        # Convert arguments to typed values based on the signature
        typed_args = {}
        signature_copy = signature.copy()
        
        while signature_copy and args:
            key, type_ = signature_copy.popitem(last=False)
            arg = args.pop(0)
            arg = arg.strip("'\"")  # Remove leading and trailing quotes
            try:
                typed_args[key] = type_(arg)
            except ValueError:
                logger.warning(f"Invalid argument type for {arg}: expected {type_}")
                typed_args[key] = arg

        return typed_args
    except Exception as e:
        logger.error(f"Failed to parse JS call: {e}")
        return {}

def clean_html(soup: BeautifulSoup) -> str:
    """Clean HTML by removing unnecessary attributes"""
    for tag in soup.find_all(True):
        for attr in dict(tag.attrs):
            if attr not in ["href", "onclick", "id", "class"]:
                del tag.attrs[attr]
    
    body = soup.select_one("body")
    return str(body) if body else str(soup)

def parse_cases(raw_data: str) -> Iterator[Case]:
    """
    Parse case list response from eCourt API.
    Based on working reference implementation.
    """
    if not raw_data:
        return
        
    starting_str = raw_data[0:15].upper()
    if "ERROR" in starting_str:
        raise ValueError("Got invalid result")
    if "INVALID CAPTCHA" in starting_str:
        raise CaptchaError("Invalid captcha")
    if len(raw_data) == 0:
        return

    for record_block in raw_data.split("##"):
        record_fields = record_block.split("~")
        if len(record_fields) < 8:
            continue

        try:
            # Parse case type, year, and number
            case_parts = record_fields[1].split("/")
            if len(case_parts) >= 3:
                case_type, r_year, r_no = case_parts[0], case_parts[1], case_parts[2]
            else:
                continue
                
            # Parse parties
            parties_text = record_fields[2].replace("<br/>", "").strip()
            if "Versus" in parties_text:
                parties = parties_text.split("Versus", 1)
                petitioner = parties[0].strip()
                respondent = parties[1].strip() if len(parties) > 1 else "Unknown"
            else:
                petitioner = parties_text
                respondent = "Unknown"
            
            cnr = record_fields[3].strip()
            
            case_obj = Case(
                case_type=case_type,
                registration_number=f"{r_year}/{r_no}",
                cnr_number=cnr,
                petitioners=[Party(name=petitioner)],
                respondents=[Party(name=respondent)],
                token=record_fields[7] if len(record_fields) > 7 else None,
                case_number=record_fields[0] if record_fields[0] else None
            )
            
            yield case_obj
            
        except (ValueError, IndexError) as e:
            logger.warning(f"Failed to parse case record: {e}")
            continue

def parse_options(raw_data: str) -> List[List[str]]:
    """Parse options from eCourt dropdown responses"""
    options = []
    try:
        for line in raw_data.split('\n'):
            if '~' in line:
                parts = line.split('~')
                if len(parts) >= 2:
                    options.append([parts[0].strip(), parts[1].strip()])
    except Exception as e:
        logger.error(f"Failed to parse options: {e}")
    return options

class CaseDetailsParser:
    """
    Comprehensive case details parser based on working reference implementation.
    Handles parsing of detailed case information from HTML responses.
    """
    
    # Known valid key checks for case details
    KNOWN_VALID_KEY_CHECKS = [
        "Number", "Key", "Station", "District", "Year", "State", "Type", "Date"
    ]

    def __init__(self, html_content: str):
        if "session expired" in html_content.lower():
            raise ValueError("Session expired")

        self.soup = BeautifulSoup(html_content, "html.parser")
        
        # Replace <br> tags with newlines for better text parsing
        for br in self.soup.find_all("br"):
            br.replace_with("\n")

        self.case = self._parse_case()
        self.html = clean_html(self.soup)

    def _parse_case(self) -> Case:
        """Parse complete case information"""
        try:
            case_details = self._extract_case_details()
            fir_details = self._extract_fir_details()
            case_status = self._extract_case_status()
            petitioners = self._extract_parties("Petitioner_Advocate_table")
            respondents = self._extract_parties("Respondent_Advocate_table")
            hearings = self._extract_hearings()
            category_details = self._extract_category_details()
            objections = self._extract_objections()
            orders = self._extract_orders()

            # Create FIR object if details exist
            fir = None
            if fir_details:
                fir = FIR(
                    state=fir_details.get("State"),
                    district=fir_details.get("District"),
                    police_station=fir_details.get("Police Station"),
                    number=fir_details.get("FIR Number"),
                    year=fir_details.get("Year"),
                )

            return Case(
                case_type=case_details.get("Case Type", ""),
                filing_number=case_details.get("Filing Number"),
                filing_date=parse_date(case_details.get("Filing Date")),
                registration_number=case_details.get("Registration Number", ""),
                registration_date=parse_date(case_details.get("Registration Date")),
                cnr_number=case_details.get("CNR Number", ""),
                first_hearing_date=parse_date(case_status.get("First Hearing Date")),
                decision_date=parse_date(case_status.get("Decision Date")),
                case_status=case_status.get("Case Status", case_status.get("Stage of Case")),
                nature_of_disposal=case_status.get("Nature of Disposal"),
                coram=case_status.get("Coram"),
                bench=case_status.get("Bench"),
                state=case_status.get("State"),
                district=case_status.get("District"),
                judicial=case_status.get("Judicial"),
                not_before_me=case_status.get("Not Before Me"),
                petitioners=petitioners,
                respondents=respondents,
                hearings=hearings,
                category=category_details.get("Category"),
                sub_category=category_details.get("Sub Category"),
                objections=objections,
                orders=orders,
                fir=fir,
            )
        except Exception as e:
            logger.error(f"Failed to parse case details: {e}")
            # Return minimal case object
            return Case(
                case_type="Unknown",
                registration_number="Unknown",
                cnr_number="Unknown"
            )

    def _extract_case_details(self) -> Dict[str, str]:
        """Extract case details from spans with labels"""
        details = {}
        
        for label in self.soup.select('.case_details_table label'):
            key = label.text.strip()
            
            # Validate key contains at least one known check string
            if not any(check in key for check in self.KNOWN_VALID_KEY_CHECKS):
                continue
            
            value = ""
            
            # Method 1: Check for next named sibling label
            next_named_sibling = None
            for sibling in label.next_siblings:
                if sibling.name:
                    next_named_sibling = sibling
                    break
            
            if next_named_sibling and next_named_sibling.name == "label":
                value = next_named_sibling.text.replace(":", "").strip()
            # Method 2: Split parent text by ":"
            elif ":" in label.parent.text:
                parts = label.parent.text.split(":", 1)
                if len(parts) > 1:
                    value = parts[1].strip()
            # Method 3: Check parent's next siblings
            else:
                for sibling in label.parent.next_siblings:
                    if hasattr(sibling, 'text') and ":" in sibling.text:
                        parts = sibling.text.split(":", 1)
                        if len(parts) > 1:
                            value = parts[1].strip()
                            break
            
            # Clean up value
            details[key] = value.replace("\xa0", "").strip()
        
        return details

    def _extract_fir_details(self) -> Dict[str, str]:
        """Extract FIR details if present"""
        fir_details = {}
        d = self.soup.select_one("span.FIR_details_table")
        if d:
            s = d.text.replace("\xa0", "").strip()
            regex = r"(?P<k>.*):\s?(?P<v>(\w|\d| )+)\s?"
            matches = re.finditer(regex, s, re.MULTILINE)
            for match in matches:
                fir_details[match.group("k")] = match.group("v").strip()
        return fir_details

    def _extract_case_status(self) -> Dict[str, str]:
        """Extract case status information"""
        case_status = {}
        case_status_div = self.soup.find("h2", string=re.compile("Case Status"))
        
        if not case_status_div:
            return case_status

        next_sibling = None
        for next_sibling in case_status_div.next_siblings:
            if next_sibling.name:
                break

        if next_sibling:
            for row in next_sibling.select("label"):
                strong_tags = row.find_all("strong")
                if len(strong_tags) >= 2:
                    key = strong_tags[0].text.strip()
                    value_text = strong_tags[1].text
                    value = value_text.split(":")[1].strip() if ":" in value_text else value_text.strip()
                    case_status[key] = value
        
        return case_status

    def _extract_parties(self, span_class: str) -> List[Party]:
        """Extract parties (petitioners/respondents) with advocates"""
        parties = []
        table = self.soup.find("span", class_=span_class)
        if not table:
            return parties
        
        s = table.text.replace("\xa0", "").strip()
        regex = r"\d\)\s+(?P<party>[^\n]+)(?:(?:\s|\n)+Advocate\s*-\s*(?P<advocate>[^\n]+))?"
        matches = re.finditer(regex, s, re.MULTILINE)
        
        for match in matches:
            party = Party(name=match.group("party").strip())
            if match.group("advocate"):
                party.advocate = match.group("advocate").strip()
            parties.append(party)
        
        return parties

    def _extract_hearings(self) -> List[Hearing]:
        """Extract hearing history"""
        hearings = []
        f = self.soup.find("table", id="historyheading")
        if f:
            history_table = f.find_next("table")
        else:
            return hearings
        
        if history_table:
            for row in history_table.find_all("tr")[1:]:
                cells = row.find_all("td")
                if len(cells) < 5:
                    continue
                
                cause_list_type = cells[0].text.strip()
                if len(cause_list_type) < 4:
                    cause_list_type = None
                if cause_list_type == "Order Number":
                    break
                
                hearing = Hearing(
                    cause_list_type=cause_list_type,
                    judge=cells[1].text.strip(),
                    date=cells[2].text.strip() if len(cells) > 2 else None,
                    next_date=cells[3].text.strip() if len(cells) > 3 else None,
                    purpose=cells[4].text.strip() if len(cells) > 4 else None,
                )
                
                # Extract additional parameters from onclick if available
                if cells[2].select_one("a"):
                    signature = OrderedDict([
                        ("court_code", str),
                        ("district_code", str),
                        ("next_date", str),
                        ("case_number", str),
                        ("state_code", str),
                        ("disposal_flag", str),
                        ("business_date", str),
                        ("court_no", str),
                        ("srno", str),
                    ])
                    try:
                        res = parse_js_call(cells[2].select_one("a")["onclick"], signature)
                        hearing.court_no = res.get("court_no")
                        hearing.srno = res.get("srno")
                    except Exception as e:
                        logger.warning(f"Failed to parse hearing onclick: {e}")
                
                hearings.append(hearing)
        
        return hearings

    def _extract_orders(self) -> List[Order]:
        """Extract orders/judgments"""
        orders = []
        order_table = self.soup.find("table", class_="order_table")
        if not order_table:
            return orders
        
        for row in order_table.find_all("tr")[1:]:
            try:
                cells = row.find_all("td")
                if len(cells) < 5:
                    continue
                    
                _, caseno, judge, date, details = cells
                
                link = details.select_one("a")
                filename = None
                if link and link.get("href"):
                    url = link["href"]
                    query = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
                    filename = query.get("filename", [None])[0]
                
                orders.append(Order(
                    judge=judge.text.strip(),
                    date=date.text.strip(),
                    filename=filename
                ))
            except Exception as e:
                logger.warning(f"Failed to parse order row: {e}")
                continue
        
        return orders

    def _extract_category_details(self) -> Dict[str, str]:
        """Extract category details"""
        category_details = {}
        for t in self.soup.find_all("table"):
            if "Category Details" in t.text:
                category_table = t.find_next("table")
                if category_table:
                    for row in category_table.find_all("tr"):
                        cells = row.find_all("td")
                        if len(cells) >= 2:
                            key = cells[0].text.strip()
                            value = cells[1].text.strip()
                            category_details[key] = value
        return category_details

    def _extract_objections(self) -> List[Objection]:
        """Extract objections"""
        objections = []
        for t in self.soup.find_all("table"):
            if "OBJECTION" in t.text:
                objection_table = t.find_next("table")
                if objection_table:
                    for row in objection_table.find_all("tr")[1:]:
                        cells = row.find_all("td")
                        if len(cells) >= 5:
                            objections.append(Objection(
                                scrutiny_date=cells[1].text.strip(),
                                objection=cells[2].text.strip(),
                                compliance_date=cells[3].text.strip(),
                                receipt_date=cells[4].text.strip(),
                            ))
        return objections