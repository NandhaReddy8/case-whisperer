from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class SearchType(str, Enum):
    CNR = "cnr"
    CASE = "case"
    DIARY = "diary"
    PARTY = "party"

class CaseStatus(str, Enum):
    PENDING = "pending"
    DISPOSED = "disposed"
    RESERVED = "reserved"

class CaseSearchRequest(BaseModel):
    search_type: SearchType
    cnr_number: Optional[str] = None
    case_type: Optional[str] = None
    case_number: Optional[str] = None
    year: Optional[str] = None
    diary_number: Optional[str] = None
    party_name: Optional[str] = None
    court_state_code: str = "6"  # Default to Gujarat
    court_code: Optional[str] = None

class CaseHistory(BaseModel):
    id: str
    date: str
    purpose: str
    order: Optional[str] = None
    next_purpose: Optional[str] = None

class Advocate(BaseModel):
    petitioner: str
    respondent: str

class CaseResponse(BaseModel):
    id: int
    cnr_number: str
    case_number: Optional[str] = None
    case_type: Optional[str] = None
    registration_number: Optional[str] = None
    filing_date: Optional[datetime] = None
    current_status: Optional[str] = None
    next_hearing_date: Optional[datetime] = None
    petitioner: Optional[str] = None
    respondent: Optional[str] = None
    court_name: Optional[str] = None
    advocates: Optional[Dict[str, str]] = None
    history: Optional[List[CaseHistory]] = None
    sync_calendar: bool = False
    calendar_event_id: Optional[str] = None
    last_synced_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CaseCreate(BaseModel):
    search_request: CaseSearchRequest
    sync_calendar: bool = False

class CaseUpdate(BaseModel):
    sync_calendar: Optional[bool] = None
    current_status: Optional[str] = None
    next_hearing_date: Optional[datetime] = None

class RefreshRequest(BaseModel):
    case_id: int
    force_refresh: bool = False

class BulkRefreshRequest(BaseModel):
    case_ids: Optional[List[int]] = None  # If None, refresh all cases
    force_refresh: bool = False