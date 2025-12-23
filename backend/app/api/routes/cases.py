from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.core.database import get_db
from app.models.case import (
    CaseCreate, CaseResponse, CaseUpdate, RefreshRequest, 
    BulkRefreshRequest, CaseSearchRequest
)
from app.services.case_service import CaseService
from app.services.scheduler import scheduler
from app.lib.ecourt_client import RetryException

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/cases", response_model=CaseResponse)
async def add_case(
    case_create: CaseCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Add a new case by searching eCourt system
    
    This endpoint searches for a case using the provided search parameters,
    fetches the case data from eCourt, and stores it in the database.
    """
    try:
        case_service = CaseService(db)
        
        # Run the case search in background to avoid blocking
        case = await case_service.search_and_add_case(case_create)
        
        return case
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding case: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/cases", response_model=List[CaseResponse])
async def get_cases(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all cases with pagination"""
    try:
        case_service = CaseService(db)
        cases = case_service.get_cases(skip=skip, limit=limit)
        return cases
    except Exception as e:
        logger.error(f"Error fetching cases: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/cases/{case_id}", response_model=CaseResponse)
async def get_case(case_id: int, db: Session = Depends(get_db)):
    """Get a specific case by ID"""
    try:
        case_service = CaseService(db)
        case = case_service.get_case(case_id)
        
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        
        return case
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching case {case_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/cases/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: int,
    case_update: CaseUpdate,
    db: Session = Depends(get_db)
):
    """Update case settings"""
    try:
        case_service = CaseService(db)
        case = case_service.update_case(case_id, case_update)
        
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        
        return case
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating case {case_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/cases/{case_id}")
async def delete_case(case_id: int, db: Session = Depends(get_db)):
    """Delete a case"""
    try:
        case_service = CaseService(db)
        success = case_service.delete_case(case_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Case not found")
        
        return {"message": "Case deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting case {case_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/cases/{case_id}/refresh", response_model=CaseResponse)
async def refresh_case(
    case_id: int,
    refresh_request: RefreshRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Refresh case data from eCourt
    
    Fetches the latest case information from eCourt and updates the database.
    Only updates if the data has changed unless force_refresh is True.
    """
    try:
        case_service = CaseService(db)
        
        # Run refresh in background for better performance
        case = await case_service.refresh_case(
            case_id, 
            force_refresh=refresh_request.force_refresh
        )
        
        return case
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error refreshing case {case_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/cases/refresh/bulk")
async def bulk_refresh_cases(
    bulk_request: BulkRefreshRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Refresh multiple cases or all cases
    
    If case_ids is provided, refreshes only those cases.
    If case_ids is None, refreshes all cases in the database.
    """
    try:
        # Run bulk refresh in background
        background_tasks.add_task(
            _bulk_refresh_task,
            bulk_request.case_ids,
            bulk_request.force_refresh
        )
        
        return {
            "message": "Bulk refresh started",
            "case_ids": bulk_request.case_ids,
            "force_refresh": bulk_request.force_refresh
        }
    except Exception as e:
        logger.error(f"Error starting bulk refresh: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/cases/refresh/status")
async def get_refresh_status():
    """Get the status of the scheduler and last refresh"""
    try:
        return {
            "scheduler_running": scheduler.running,
            "scheduler_enabled": True,  # From settings
            "last_refresh": "Not implemented yet"  # TODO: Store last refresh time
        }
    except Exception as e:
        logger.error(f"Error getting refresh status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def _bulk_refresh_task(case_ids: Optional[List[int]], force_refresh: bool):
    """Background task for bulk refresh"""
    try:
        results = await scheduler.refresh_cases_manually(case_ids)
        logger.info(f"Bulk refresh completed: {results}")
    except Exception as e:
        logger.error(f"Bulk refresh task failed: {e}")

@router.post("/cases/search")
async def search_case(
    search_request: CaseSearchRequest,
    db: Session = Depends(get_db)
):
    """
    Search for a case without adding it to database
    
    This endpoint is useful for testing connectivity and validating
    case information before actually adding it to the database.
    """
    try:
        from app.lib.ecourt_client import ECourtClient
        from app.lib.entities import Court
        
        court = Court(
            state_code=search_request.court_state_code,
            court_code=search_request.court_code
        )
        
        ecourt_client = ECourtClient(court)
        
        case_data = None
        if search_request.search_type == "cnr" and search_request.cnr_number:
            case_data = ecourt_client.search_case_by_cnr(search_request.cnr_number)
        elif search_request.search_type == "case" and all([
            search_request.case_type, search_request.case_number, search_request.year
        ]):
            case_data = ecourt_client.search_case_by_number(
                search_request.case_type,
                search_request.case_number,
                search_request.year
            )
        
        if not case_data:
            return {
                "found": False,
                "message": "Case not found in eCourt records",
                "case_data": None
            }
        
        return {
            "found": True,
            "case_data": case_data.json() if case_data else None
        }
        
    except RetryException as e:
        logger.error(f"eCourt service error: {e}")
        raise HTTPException(
            status_code=503, 
            detail=f"eCourt service unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error searching case: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Search failed: {str(e)}"
        )