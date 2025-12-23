import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

from app.core.config import settings

logger = logging.getLogger(__name__)

class CalendarService:
    SCOPES = ['https://www.googleapis.com/auth/calendar']

    def __init__(self):
        self.service = None
        if GOOGLE_AVAILABLE:
            self._initialize_service()

    def _initialize_service(self):
        """Initialize Google Calendar service"""
        try:
            creds = None
            
            # Load existing token
            if os.path.exists(settings.GOOGLE_TOKEN_FILE):
                creds = Credentials.from_authorized_user_file(
                    settings.GOOGLE_TOKEN_FILE, self.SCOPES
                )
            
            # If no valid credentials, get new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if os.path.exists(settings.GOOGLE_CREDENTIALS_FILE):
                        flow = InstalledAppFlow.from_client_secrets_file(
                            settings.GOOGLE_CREDENTIALS_FILE, self.SCOPES
                        )
                        creds = flow.run_local_server(port=0)
                    else:
                        logger.warning("Google credentials file not found")
                        return
                
                # Save credentials for next run
                with open(settings.GOOGLE_TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
            
            self.service = build('calendar', 'v3', credentials=creds)
            logger.info("Google Calendar service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Calendar service: {e}")
            self.service = None

    async def create_hearing_event(
        self, 
        case_number: str, 
        hearing_date: datetime,
        case_details: Dict[str, Any]
    ) -> Optional[str]:
        """Create a calendar event for case hearing"""
        if not self.service:
            logger.warning("Google Calendar service not available")
            return None

        try:
            # Check if event already exists
            existing_event = await self._find_existing_event(case_number)
            if existing_event:
                logger.info(f"Event already exists for case {case_number}")
                return existing_event['id']

            # Create event
            event = {
                'summary': f'Court Hearing - {case_number}',
                'description': self._create_event_description(case_details),
                'start': {
                    'date': hearing_date.strftime('%Y-%m-%d'),
                    'timeZone': 'Asia/Kolkata',
                },
                'end': {
                    'date': hearing_date.strftime('%Y-%m-%d'),
                    'timeZone': 'Asia/Kolkata',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60 * 7},  # 1 week before
                        {'method': 'popup', 'minutes': 24 * 60},      # 1 day before
                    ],
                },
                'extendedProperties': {
                    'private': {
                        'caseNumber': case_number,
                        'source': 'case-whisperer'
                    }
                }
            }

            created_event = self.service.events().insert(
                calendarId=settings.GOOGLE_CALENDAR_ID,
                body=event
            ).execute()

            logger.info(f"Created calendar event for case {case_number}: {created_event['id']}")
            return created_event['id']

        except Exception as e:
            logger.error(f"Failed to create calendar event: {e}")
            return None

    async def update_hearing_event(
        self, 
        event_id: str, 
        hearing_date: datetime
    ) -> bool:
        """Update existing calendar event with new hearing date"""
        if not self.service:
            return False

        try:
            # Get existing event
            event = self.service.events().get(
                calendarId=settings.GOOGLE_CALENDAR_ID,
                eventId=event_id
            ).execute()

            # Update dates
            event['start']['date'] = hearing_date.strftime('%Y-%m-%d')
            event['end']['date'] = hearing_date.strftime('%Y-%m-%d')

            # Update event
            updated_event = self.service.events().update(
                calendarId=settings.GOOGLE_CALENDAR_ID,
                eventId=event_id,
                body=event
            ).execute()

            logger.info(f"Updated calendar event {event_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update calendar event {event_id}: {e}")
            return False

    async def delete_event(self, event_id: str) -> bool:
        """Delete calendar event"""
        if not self.service:
            return False

        try:
            self.service.events().delete(
                calendarId=settings.GOOGLE_CALENDAR_ID,
                eventId=event_id
            ).execute()

            logger.info(f"Deleted calendar event {event_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete calendar event {event_id}: {e}")
            return False

    async def _find_existing_event(self, case_number: str) -> Optional[Dict]:
        """Find existing event for case number"""
        if not self.service:
            return None

        try:
            # Search for events with case number in extended properties
            events_result = self.service.events().list(
                calendarId=settings.GOOGLE_CALENDAR_ID,
                privateExtendedProperty=f'caseNumber={case_number}',
                maxResults=1
            ).execute()

            events = events_result.get('items', [])
            return events[0] if events else None

        except Exception as e:
            logger.error(f"Failed to search for existing event: {e}")
            return None

    def _create_event_description(self, case_details: Dict[str, Any]) -> str:
        """Create event description from case details"""
        description_parts = []
        
        if case_details.get('petitioner'):
            description_parts.append(f"Petitioner: {case_details['petitioner']}")
        
        if case_details.get('respondent'):
            description_parts.append(f"Respondent: {case_details['respondent']}")
        
        if case_details.get('court'):
            description_parts.append(f"Court: {case_details['court']}")
        
        description_parts.append("\nGenerated by Case Whisperer")
        
        return "\n".join(description_parts)