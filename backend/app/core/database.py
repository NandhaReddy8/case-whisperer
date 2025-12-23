from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class CaseModel(Base):
    __tablename__ = "cases"
    
    id = Column(Integer, primary_key=True, index=True)
    cnr_number = Column(String, unique=True, index=True, nullable=False)
    case_number = Column(String, index=True)
    case_type = Column(String)
    registration_number = Column(String)
    filing_date = Column(DateTime)
    current_status = Column(String)
    next_hearing_date = Column(DateTime)
    petitioner = Column(String)
    respondent = Column(String)
    court_name = Column(String)
    advocates = Column(JSON)
    case_data = Column(JSON)  # Raw scraped data
    sync_calendar = Column(Boolean, default=False)
    calendar_event_id = Column(String)  # Google Calendar event ID
    last_synced_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    Base.metadata.create_all(bind=engine)