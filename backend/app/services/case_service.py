from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import asyncio
import logging

from app.core.database import CaseModel
from app.models.case import CaseSearchRequest, CaseResponse, CaseCreate, CaseUpdate
from app.lib.ecourt_client import ECourtClient, RetryException
from app.lib.entities import Court, Case, CaseType, ActType
from app.lib.parsers import parse_date
from app.services.calendar_service import CalendarService

logger = logging.getLogger(__name__)

class CaseService:
    def __init__(self, db: Session):
        self.db = db
        self.calendar_service = CalendarService()

    async def search_and_add_case(self, case_create: CaseCreate) -> CaseResponse:
        """Search for a case on eCourt and add it to database"""
        search_req = case_create.search_request
        
        # Log the search request for debugging
        logger.info(f"Search request: type={search_req.search_type}, "
                   f"case_type={search_req.case_type}, "
                   f"case_number={search_req.case_number}, "
                   f"year={search_req.year}, "
                   f"cnr={search_req.cnr_number}, "
                   f"court={search_req.court_state_code}")
        
        # Create court object with validation
        try:
            court = Court(
                state_code=search_req.court_state_code,
                court_code=search_req.court_code
            )
        except ValueError as e:
            raise ValueError(f"Invalid court configuration: {e}")
        
        # Initialize eCourt client
        ecourt_client = ECourtClient(court)
        
        try:
            # Search based on search type
            case_data = None
            if search_req.search_type == "cnr" and search_req.cnr_number:
                case_data = await asyncio.to_thread(
                    ecourt_client.search_case_by_cnr, 
                    search_req.cnr_number
                )
            elif search_req.search_type == "case" and all([
                search_req.case_type, search_req.case_number, search_req.year
            ]):
                case_data = await asyncio.to_thread(
                    ecourt_client.search_case_by_number,
                    search_req.case_type,
                    search_req.case_number,
                    search_req.year
                )
            elif search_req.search_type == "filing" and search_req.filing_number:
                # Enhanced: Support filing number search
                case_data = await asyncio.to_thread(
                    self._search_by_filing_number,
                    ecourt_client,
                    search_req.filing_number,
                    search_req.year
                )
            else:
                raise ValueError("Invalid search parameters")

            if not case_data:
                raise ValueError("Case not found")

            # Check if case already exists
            existing_case = self.db.query(CaseModel).filter(
                CaseModel.cnr_number == case_data.cnr_number
            ).first()
            
            if existing_case:
                return self._convert_to_response(existing_case)

            # Get detailed case history using enhanced parser
            expanded_case = await asyncio.to_thread(
                ecourt_client.expand_case, 
                case_data
            )

            # Create database record with enhanced data
            from app.lib.court_names import get_court_name
            
            db_case = CaseModel(
                cnr_number=expanded_case.cnr_number,
                case_number=expanded_case.case_number,
                case_type=expanded_case.case_type,
                registration_number=expanded_case.registration_number,
                filing_date=expanded_case.filing_date,
                current_status=expanded_case.case_status,
                next_hearing_date=self._extract_next_hearing_date(expanded_case),
                petitioner=expanded_case.petitioners[0].name if expanded_case.petitioners else None,
                respondent=expanded_case.respondents[0].name if expanded_case.respondents else None,
                court_name=get_court_name(court.state_code, court.court_code),
                advocates=self._extract_advocates(expanded_case),
                case_data=expanded_case.json(),
                sync_calendar=case_create.sync_calendar,
                last_synced_at=datetime.utcnow()
            )

            self.db.add(db_case)
            self.db.commit()
            self.db.refresh(db_case)

            # Sync with Google Calendar if requested
            if case_create.sync_calendar and db_case.next_hearing_date:
                try:
                    event_id = await self.calendar_service.create_hearing_event(
                        case_number=db_case.case_number or db_case.cnr_number,
                        hearing_date=db_case.next_hearing_date,
                        case_details={
                            "petitioner": db_case.petitioner,
                            "respondent": db_case.respondent,
                            "court": db_case.court_name,
                            "case_type": db_case.case_type
                        }
                    )
                    db_case.calendar_event_id = event_id
                    self.db.commit()
                except Exception as e:
                    logger.error(f"Failed to create calendar event: {e}")

            return self._convert_to_response(db_case)

        except RetryException as e:
            raise ValueError(f"Failed to fetch case data: {e}")
        except Exception as e:
            logger.error(f"Error adding case: {e}")
            raise ValueError(f"Failed to add case: {e}")

    async def refresh_case(self, case_id: int, force_refresh: bool = False) -> CaseResponse:
        """Refresh case data from eCourt with enhanced functionality"""
        db_case = self.db.query(CaseModel).filter(CaseModel.id == case_id).first()
        if not db_case:
            raise ValueError("Case not found")

        # Extract court info from stored case data
        case_data_dict = db_case.case_data or {}
        court = Court(
            state_code=case_data_dict.get("state_code", "6"),  # Default to Gujarat
            court_code=case_data_dict.get("court_code")
        )
        
        ecourt_client = ECourtClient(court)

        try:
            # Get fresh case data
            case_data = await asyncio.to_thread(
                ecourt_client.search_case_by_cnr,
                db_case.cnr_number
            )

            if not case_data:
                raise ValueError("Case not found on eCourt")

            # Get expanded case details
            expanded_case = await asyncio.to_thread(
                ecourt_client.expand_case,
                case_data
            )

            # Calculate hash to check for changes
            new_case_json = expanded_case.json()
            new_hash = ecourt_client.calculate_case_hash(new_case_json)
            old_hash = ecourt_client.calculate_case_hash(db_case.case_data or {})

            # Update only if data has changed or force refresh
            if force_refresh or new_hash != old_hash:
                old_hearing_date = db_case.next_hearing_date
                new_hearing_date = self._extract_next_hearing_date(expanded_case)
                
                # Update case data with enhanced information
                db_case.current_status = expanded_case.case_status
                db_case.next_hearing_date = new_hearing_date
                db_case.case_data = new_case_json
                db_case.last_synced_at = datetime.utcnow()

                # Update calendar event if hearing date changed
                if (db_case.sync_calendar and 
                    new_hearing_date != old_hearing_date and 
                    new_hearing_date):
                    
                    try:
                        if db_case.calendar_event_id:
                            await self.calendar_service.update_hearing_event(
                                event_id=db_case.calendar_event_id,
                                hearing_date=new_hearing_date
                            )
                        else:
                            event_id = await self.calendar_service.create_hearing_event(
                                case_number=db_case.case_number or db_case.cnr_number,
                                hearing_date=new_hearing_date,
                                case_details={
                                    "petitioner": db_case.petitioner,
                                    "respondent": db_case.respondent,
                                    "court": db_case.court_name,
                                    "case_type": db_case.case_type
                                }
                            )
                            db_case.calendar_event_id = event_id
                    except Exception as e:
                        logger.error(f"Failed to update calendar event: {e}")

                self.db.commit()
                self.db.refresh(db_case)

            return self._convert_to_response(db_case)

        except Exception as e:
            logger.error(f"Error refreshing case {case_id}: {e}")
            raise ValueError(f"Failed to refresh case: {e}")

    async def bulk_refresh_cases(self, court_filter: Optional[str] = None) -> Dict[str, int]:
        """Bulk refresh all cases with enhanced error handling"""
        query = self.db.query(CaseModel)
        if court_filter:
            query = query.filter(CaseModel.court_name.contains(court_filter))
        
        cases = query.all()
        stats = {"total": len(cases), "updated": 0, "failed": 0, "unchanged": 0}
        
        for db_case in cases:
            try:
                result = await self.refresh_case(db_case.id, force_refresh=False)
                if result:
                    stats["updated"] += 1
                else:
                    stats["unchanged"] += 1
            except Exception as e:
                logger.error(f"Failed to refresh case {db_case.id}: {e}")
                stats["failed"] += 1
        
        return stats

    def get_case(self, case_id: int) -> Optional[CaseResponse]:
        """Get case by ID"""
        db_case = self.db.query(CaseModel).filter(CaseModel.id == case_id).first()
        if db_case:
            return self._convert_to_response(db_case)
        return None

    def get_cases(self, skip: int = 0, limit: int = 100, status_filter: Optional[str] = None) -> List[CaseResponse]:
        """Get all cases with pagination and filtering"""
        query = self.db.query(CaseModel)
        
        if status_filter:
            query = query.filter(CaseModel.current_status.contains(status_filter))
        
        db_cases = query.offset(skip).limit(limit).all()
        return [self._convert_to_response(case) for case in db_cases]

    def search_cases(self, query: str, search_field: str = "petitioner") -> List[CaseResponse]:
        """Search cases by various fields"""
        db_query = self.db.query(CaseModel)
        
        if search_field == "petitioner":
            db_query = db_query.filter(CaseModel.petitioner.contains(query))
        elif search_field == "respondent":
            db_query = db_query.filter(CaseModel.respondent.contains(query))
        elif search_field == "case_number":
            db_query = db_query.filter(CaseModel.case_number.contains(query))
        elif search_field == "cnr":
            db_query = db_query.filter(CaseModel.cnr_number.contains(query))
        
        db_cases = db_query.limit(50).all()  # Limit search results
        return [self._convert_to_response(case) for case in db_cases]

    def update_case(self, case_id: int, case_update: CaseUpdate) -> Optional[CaseResponse]:
        """Update case settings"""
        db_case = self.db.query(CaseModel).filter(CaseModel.id == case_id).first()
        if not db_case:
            return None

        # Update fields
        if case_update.sync_calendar is not None:
            db_case.sync_calendar = case_update.sync_calendar
        if case_update.current_status is not None:
            db_case.current_status = case_update.current_status
        if case_update.next_hearing_date is not None:
            db_case.next_hearing_date = case_update.next_hearing_date

        db_case.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_case)

        return self._convert_to_response(db_case)

    def delete_case(self, case_id: int) -> bool:
        """Delete case"""
        db_case = self.db.query(CaseModel).filter(CaseModel.id == case_id).first()
        if not db_case:
            return False

        # Delete calendar event if exists
        if db_case.calendar_event_id:
            try:
                asyncio.create_task(
                    self.calendar_service.delete_event(db_case.calendar_event_id)
                )
            except Exception as e:
                logger.error(f"Failed to delete calendar event: {e}")

        self.db.delete(db_case)
        self.db.commit()
        return True

    # Enhanced utility methods

    async def get_case_types(self, court_state_code: str, court_code: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available case types for a court"""
        try:
            court = Court(state_code=court_state_code, court_code=court_code)
            ecourt_client = ECourtClient(court)
            
            case_types = await asyncio.to_thread(
                lambda: list(ecourt_client.get_case_types())
            )
            
            return [{"code": ct.code, "description": ct.description} for ct in case_types]
        except Exception as e:
            logger.error(f"Failed to get case types: {e}")
            return []

    async def get_act_types(self, court_state_code: str, court_code: Optional[str] = None, query: str = "") -> List[Dict[str, Any]]:
        """Get available act types for a court"""
        try:
            court = Court(state_code=court_state_code, court_code=court_code)
            ecourt_client = ECourtClient(court)
            
            act_types = await asyncio.to_thread(
                lambda: list(ecourt_client.get_act_types(query))
            )
            
            return [{"code": at.code, "description": at.description} for at in act_types]
        except Exception as e:
            logger.error(f"Failed to get act types: {e}")
            return []

    def get_storage_stats(self) -> Dict[str, int]:
        """Get storage statistics from SQLAlchemy database"""
        try:
            total_cases = self.db.query(CaseModel).count()
            pending_cases = self.db.query(CaseModel).filter(
                CaseModel.current_status.contains("Pending")
            ).count()
            disposed_cases = self.db.query(CaseModel).filter(
                CaseModel.current_status.contains("Disposed")
            ).count()
            
            return {
                "cases": total_cases,
                "pending_cases": pending_cases,
                "disposed_cases": disposed_cases,
                "case_types": 0,  # Not stored separately in SQLAlchemy model
                "act_types": 0,   # Not stored separately in SQLAlchemy model
                "courts": 0       # Not stored separately in SQLAlchemy model
            }
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {"cases": 0, "pending_cases": 0, "disposed_cases": 0, "case_types": 0, "act_types": 0, "courts": 0}

    def _extract_next_hearing_date(self, case: Case) -> Optional[date]:
        """Extract next hearing date from case hearings"""
        if not case.hearings:
            return case.next_hearing_date
            
        for hearing in case.hearings:
            if hearing.next_date and hearing.next_date != "-":
                parsed_date = parse_date(hearing.next_date)
                if parsed_date:
                    return parsed_date
        
        return case.next_hearing_date

    def _extract_advocates(self, case: Case) -> Dict[str, str]:
        """Extract advocate information from case parties"""
        advocates = {"petitioner": "Not available", "respondent": "Not available"}
        
        if case.petitioners and case.petitioners[0].advocate:
            advocates["petitioner"] = case.petitioners[0].advocate
        
        if case.respondents and case.respondents[0].advocate:
            advocates["respondent"] = case.respondents[0].advocate
        
        return advocates

    async def _search_by_filing_number(self, ecourt_client: ECourtClient, filing_number: str, year: Optional[str]) -> Optional[Case]:
        """Search case by filing number (enhanced functionality)"""
        # This would need to be implemented based on eCourt API
        # For now, return None as it's not in the reference implementation
        logger.warning("Filing number search not yet implemented")
        return None

    def _convert_to_response(self, db_case: CaseModel) -> CaseResponse:
        """Convert database model to response object"""
        return CaseResponse(
            id=db_case.id,
            cnr_number=db_case.cnr_number,
            case_number=db_case.case_number,
            case_type=db_case.case_type,
            registration_number=db_case.registration_number,
            filing_date=db_case.filing_date,
            current_status=db_case.current_status,
            next_hearing_date=db_case.next_hearing_date,
            petitioner=db_case.petitioner,
            respondent=db_case.respondent,
            court_name=db_case.court_name,
            advocates=db_case.advocates,
            history=self._extract_history_from_case_data(db_case.case_data),
            sync_calendar=db_case.sync_calendar,
            calendar_event_id=db_case.calendar_event_id,
            last_synced_at=db_case.last_synced_at,
            created_at=db_case.created_at,
            updated_at=db_case.updated_at
        )

    def _extract_history_from_case_data(self, case_data: Optional[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
        """Extract case history from stored case data"""
        if not case_data or not isinstance(case_data, dict):
            return None
        
        hearings = case_data.get("hearings", [])
        if not hearings:
            return None
        
        history = []
        for hearing in hearings:
            if isinstance(hearing, dict):
                history.append({
                    "id": hearing.get("id", ""),
                    "date": hearing.get("date", ""),
                    "purpose": hearing.get("purpose", ""),
                    "order": hearing.get("order", ""),
                    "next_purpose": hearing.get("next_purpose", "")
                })
        
        return history if history else None