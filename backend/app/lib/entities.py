from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import json

@dataclass
class Court:
    """
    Represents a court entity with state, district, and court codes.
    Based on working reference implementation.
    """
    
    # Valid court combinations from working implementation
    __ALL_COURTS__ = [
        ("1", None), ("1", "2"), ("1", "3"), ("1", "4"), ("1", "5"), ("1", "6"),
        ("2", None), ("3", None), ("3", "2"), ("3", "3"), ("4", None), ("5", None),
        ("6", None), ("6", "2"), ("6", "3"), ("6", "4"), ("7", None), ("8", None),
        ("9", None), ("9", "2"), ("10", None), ("10", "2"), ("11", None), ("12", None),
        ("12", "2"), ("13", None), ("13", "2"), ("15", None), ("16", None), ("16", "2"),
        ("16", "3"), ("16", "4"), ("17", None), ("18", None), ("20", None), ("21", None),
        ("24", None), ("25", None), ("29", None),
    ]
    
    state_code: str
    district_code: str = "1"
    court_code: Optional[str] = None
    state_name: Optional[str] = None
    name: Optional[str] = None

    def __post_init__(self):
        """Validate court combination"""
        if self.district_code is None:
            self.district_code = "1"
        
        # Validate against known courts
        lcc = self.court_code
        if self.court_code == "1":
            lcc = None
        if (self.state_code, lcc) not in Court.__ALL_COURTS__:
            if self.court_code:
                raise ValueError(f"Invalid court: state_code={self.state_code}, court_code={self.court_code}")
            else:
                raise ValueError(f"Invalid court: state_code={self.state_code}")

    @classmethod
    def enumerate(cls):
        """Enumerate all known valid courts"""
        for c in cls.__ALL_COURTS__:
            yield Court(state_code=c[0], court_code=c[1])

    def queryParams(self):
        return {
            "state_code": self.state_code,
            "dist_code": self.district_code,
            "court_code": self.court_code or "1"
        }

    def json(self):
        return {
            "state_code": self.state_code,
            "district_code": self.district_code,
            "court_code": self.court_code,
        }

    def __eq__(self, other):
        return (self.state_code == other.state_code and 
                self.district_code == other.district_code and 
                (self.court_code or "1") == (other.court_code or "1"))

    def __iter__(self):
        for key in ["state_code", "district_code", "court_code"]:
            yield key, getattr(self, key)

@dataclass
class Party:
    """Represents a party (petitioner/respondent) in a case"""
    name: str
    advocate: Optional[str] = None

@dataclass
class Hearing:
    """Represents a hearing in a case"""
    cause_list_type: Optional[str] = None
    judge: Optional[str] = None
    date: Optional[str] = None
    next_date: Optional[str] = None
    purpose: Optional[str] = None
    court_no: Optional[str] = None
    srno: Optional[str] = None

    def expandParams(self):
        """Parameters for expanding hearing details"""
        if not all([self.court_no, self.srno, self.date]):
            raise ValueError("Missing required hearing parameters")
        return {
            "court_no": self.court_no,
            "srno": self.srno,
            "next_date": self.date
        }

@dataclass
class Order:
    """Represents an order/judgment in a case"""
    judge: Optional[str] = None
    date: Optional[str] = None
    filename: Optional[str] = None

@dataclass
class Objection:
    """Represents an objection in a case"""
    scrutiny_date: Optional[str] = None
    objection: Optional[str] = None
    compliance_date: Optional[str] = None
    receipt_date: Optional[str] = None

@dataclass
class FIR:
    """Represents FIR details"""
    state: Optional[str] = None
    district: Optional[str] = None
    police_station: Optional[str] = None
    number: Optional[str] = None
    year: Optional[str] = None

@dataclass
class CaseType:
    """Represents a case type"""
    code: int
    description: str
    court: Court

    def keys(self):
        return ["code", "description", "court_state_code", "court_court_code"]

    def __getitem__(self, key):
        if key in ["code", "description"]:
            return getattr(self, key)
        elif key == "court_state_code":
            return self.court.state_code
        elif key == "court_court_code":
            return self.court.court_code
        else:
            raise KeyError(key)

@dataclass
class ActType:
    """Represents an act type"""
    code: int
    description: str
    court: Court

    def keys(self):
        return ["code", "description", "court_state_code", "court_court_code"]

    def __getitem__(self, key):
        if key in ["code", "description"]:
            return getattr(self, key)
        elif key == "court_state_code":
            return self.court.state_code
        elif key == "court_court_code":
            return self.court.court_code
        else:
            raise KeyError(key)

@dataclass
class Case:
    case_type: str
    registration_number: str
    cnr_number: str
    filing_number: Optional[str] = None
    registration_date: Optional[date] = None
    first_hearing_date: Optional[date] = None
    decision_date: Optional[date] = None
    case_status: Optional[str] = None
    nature_of_disposal: Optional[str] = None
    coram: Optional[str] = None
    bench: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    judicial: Optional[str] = None
    petitioners: Optional[List[Party]] = None
    respondents: Optional[List[Party]] = None
    orders: Optional[List[Order]] = None
    case_number: Optional[str] = None
    hearings: Optional[List[Hearing]] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    objections: Optional[List[Objection]] = None
    not_before_me: Optional[str] = None
    filing_date: Optional[date] = None
    fir: Optional[FIR] = None
    token: Optional[str] = None
    # Additional fields for compatibility
    status: Optional[str] = None
    next_hearing_date: Optional[date] = None

    def __post_init__(self):
        # Clean CNR number (remove hyphens)
        if self.cnr_number:
            self.cnr_number = self.cnr_number.replace("-", "")
            
        # Validate CNR length
        if len(self.cnr_number) != 16:
            raise ValueError(f"Invalid CNR Number length: {len(self.cnr_number)}")
        
        # Initialize empty lists if None
        if self.petitioners is None:
            self.petitioners = []
        if self.respondents is None:
            self.respondents = []
        if self.hearings is None:
            self.hearings = []
        if self.orders is None:
            self.orders = []
        if self.objections is None:
            self.objections = []
            
        # Clean up empty values
        if self.not_before_me == "":
            self.not_before_me = None
        if self.nature_of_disposal == "--":
            self.nature_of_disposal = None
            
        # Validate case number year if present
        if self.case_number:
            try:
                year = int(self.case_number[-4:])
                assert 1990 < year < 2030
            except (ValueError, AssertionError):
                pass  # Don't fail on invalid year format

    def expandParams(self):
        """Parameters for expanding case details"""
        if not (self.token and self.case_number):
            raise ValueError("Token/case_number not set in Case entity")
        return {
            "cino": self.cnr_number,
            "token": self.token,
            "case_no": self.case_number
        }

    @property
    def name(self):
        """Generate case name from parties"""
        if len(self.petitioners) > 0 and len(self.respondents) > 0:
            return f"{self.petitioners[0].name} vs {self.respondents[0].name}"
        return None

    def json(self):
        """Generate JSON representation"""
        return {
            "case_type": self.case_type,
            "registration_number": self.registration_number,
            "cnr_number": self.cnr_number,
            "filing_number": self.filing_number,
            "registration_date": self.registration_date.isoformat() if self.registration_date else None,
            "first_hearing_date": self.first_hearing_date.isoformat() if self.first_hearing_date else None,
            "decision_date": self.decision_date.isoformat() if self.decision_date else None,
            "case_status": self.case_status,
            "nature_of_disposal": self.nature_of_disposal,
            "coram": self.coram,
            "bench": self.bench,
            "state": self.state,
            "district": self.district,
            "judicial": self.judicial,
            "petitioners": [asdict(p) for p in self.petitioners] if self.petitioners else [],
            "respondents": [asdict(r) for r in self.respondents] if self.respondents else [],
            "orders": [asdict(o) for o in self.orders] if self.orders else [],
            "case_number": self.case_number,
            "hearings": [asdict(h) for h in self.hearings] if self.hearings else [],
            "category": self.category,
            "sub_category": self.sub_category,
            "objections": [asdict(o) for o in self.objections] if self.objections else [],
            "not_before_me": self.not_before_me,
            "filing_date": self.filing_date.isoformat() if self.filing_date else None,
            "fir": asdict(self.fir) if self.fir else None,
            "token": self.token,
            "status": self.status or self.case_status,
            "next_hearing_date": self.next_hearing_date.isoformat() if self.next_hearing_date else None
        }