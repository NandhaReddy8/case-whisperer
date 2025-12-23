from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
import logging

from app.core.database import CaseModel
from app.models.case import CaseSearchRequest, CaseResponse, CaseCreate, CaseUpdate
from app.lib.ecourt_client import ECourtClient, RetryException
from app.lib.entities import Court
from app.services.calendar_service import CalendarService

logger = logging.getLogger(__name__)

class CaseService:
    def __init__(self, db: Session):
        self.db = db
        self.calendar_service = CalendarService()

    async def search_and_add_case(self, case_create: CaseCreate) -> CaseResponse:
        """Search for a case on eCourt and add it to database"""
        search_req = case_create.search_request
        
        # Create court object
        court = Court(
            state_code=search_req.court_state_code,
            court_code=search_req.court_code
        )
        
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
            else:
                raise ValueError("Invalid search parameters")

            if not case_data:
                raise ValueError("Case not found")

            # Check if case already exists
            existing_case = self.db.query(CaseModel).filter(
                CaseModel.cnr_number == case_data.cnr_number
            ).first()
            
            if existing_case:
                return CaseResponse.from_orm(existing_case)

            # Get detailed case history
            case_history = await asyncio.to_thread(
                ecourt_client.get_case_history, 
                case_data
            )

            # Create new case record
            db_case = CaseModel(
                cnr_number=case_data.cnr_number,
                case_number=case_data.case_number,
                case_type=case_data.case_type,
                registration_number=case_data.registration_number,
                filing_date=case_data.filing_date,
                current_status=case_history.get("current_status"),
                next_hearing_date=case_history.get("next_hearing_date"),
                petitioner=case_data.petitioners[0]["name"] if case_data.petitioners else None,
                respondent=case_data.respondents[0]["name"] if case_data.respondents else None,
                court_name=f"High Court - {court.state_code}",
                advocates={
                    "petitioner": "Not available",
                    "respondent": "Not available"
                },
                case_data=case_data.json(),
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
                            "court": db_case.court_name
                        }
                    )
                    db_case.calendar_event_id = event_id
                    self.db.commit()
                except Exception as e:
                    logger.error(f"Failed to create calendar event: {e}")

            return CaseResponse.from_orm(db_case)

        except RetryException as e:
            raise ValueError(f"Failed to fetch case data: {e}")
        except Exception as e:
            logger.error(f"Error adding case: {e}")
            raise ValueError(f"Failed to add case: {e}")

    async def refresh_case(self, case_id: int, force_refresh: bool = False) -> CaseResponse:
        """Refresh case data from eCourt"""
        db_case = self.db.query(CaseModel).filter(CaseModel.id == case_id).first()
        if not db_case:
            raise ValueError("Case not found")

        # Create court and client
        court = Court(state_code="6")  # Default to Gujarat, should be stored in case
        ecourt_client = ECourtClient(court)

        try:
            # Get fresh case data
            case_data = await asyncio.to_thread(
                ecourt_client.search_case_by_cnr,
                db_case.cnr_number
            )

            if not case_data:
                raise ValueError("Case not found on eCourt")

            # Get updated history
            case_history = await asyncio.to_thread(
                ecourt_client.get_case_history,
                case_data
            )

            # Calculate hash to check for changes
            new_hash = ecourt_client.calculate_case_hash(case_history)
            old_hash = ecourt_client.calculate_case_hash(db_case.case_data or {})

            # Update only if data has changed or force refresh
            if force_refresh or new_hash != old_hash:
                old_hearing_date = db_case.next_hearing_date
                
                # Update case data
                db_case.current_status = case_history.get("current_status")
                db_case.next_hearing_date = case_history.get("next_hearing_date")
                db_case.case_data = {**db_case.case_data, **case_history}
                db_case.last_synced_at = datetime.utcnow()

                # Update calendar event if hearing date changed
                if (db_case.sync_calendar and 
                    db_case.next_hearing_date != old_hearing_date and 
                    db_case.next_hearing_date):
                    
                    try:
                        if db_case.calendar_event_id:
                            await self.calendar_service.update_hearing_event(
                                event_id=db_case.calendar_event_id,
                                hearing_date=db_case.next_hearing_date
                            )
                        else:
                            event_id = await self.calendar_service.create_hearing_event(
                                case_number=db_case.case_number or db_case.cnr_number,
                                hearing_date=db_case.next_hearing_date,
                                case_details={
                                    "petitioner": db_case.petitioner,
                                    "respondent": db_case.respondent,
                                    "court": db_case.court_name
                                }
                            )
                            db_case.calendar_event_id = event_id
                    except Exception as e:
                        logger.error(f"Failed to update calendar event: {e}")

                self.db.commit()
                self.db.refresh(db_case)

            return CaseResponse.from_orm(db_case)

        except Exception as e:
            logger.error(f"Error refreshing case {case_id}: {e}")
            raise ValueError(f"Failed to refresh case: {e}")

    def get_case(self, case_id: int) -> Optional[CaseResponse]:
        """Get case by ID"""
        db_case = self.db.query(CaseModel).filter(CaseModel.id == case_id).first()
        if db_case:
            return CaseResponse.from_orm(db_case)
        return None

    def get_cases(self, skip: int = 0, limit: int = 100) -> List[CaseResponse]:
        """Get all cases with pagination"""
        db_cases = self.db.query(CaseModel).offset(skip).limit(limit).all()
        return [CaseResponse.from_orm(case) for case in db_cases]

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

        return CaseResponse.from_orm(db_case)

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