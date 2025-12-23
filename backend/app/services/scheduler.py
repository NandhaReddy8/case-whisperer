import asyncio
import logging
from datetime import datetime, time
from typing import List
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, CaseModel
from app.services.case_service import CaseService
from app.core.config import settings

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self):
        self.running = False
        self.task = None

    async def start(self):
        """Start the scheduler"""
        if not settings.SCHEDULER_ENABLED:
            logger.info("Scheduler is disabled")
            return

        if self.running:
            logger.warning("Scheduler is already running")
            return

        self.running = True
        self.task = asyncio.create_task(self._scheduler_loop())
        logger.info("Scheduler started")

    async def stop(self):
        """Stop the scheduler"""
        if not self.running:
            return

        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Scheduler stopped")

    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                now = datetime.now()
                target_time = time(settings.REFRESH_HOUR, 0)  # 3:00 AM by default
                
                # Check if it's time to run the refresh
                if now.time().hour == target_time.hour and now.time().minute == target_time.minute:
                    logger.info("Starting scheduled case refresh")
                    await self._refresh_all_cases()
                    
                    # Sleep for 60 seconds to avoid running multiple times in the same minute
                    await asyncio.sleep(60)
                else:
                    # Check every minute
                    await asyncio.sleep(60)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(60)

    async def _refresh_all_cases(self):
        """Refresh all cases in the database"""
        db = SessionLocal()
        try:
            case_service = CaseService(db)
            
            # Get all cases
            cases = db.query(CaseModel).all()
            logger.info(f"Refreshing {len(cases)} cases")
            
            success_count = 0
            error_count = 0
            
            for case in cases:
                try:
                    await case_service.refresh_case(case.id, force_refresh=False)
                    success_count += 1
                    logger.debug(f"Refreshed case {case.cnr_number}")
                    
                    # Small delay between requests to avoid overwhelming the server
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"Failed to refresh case {case.cnr_number}: {e}")
            
            logger.info(f"Case refresh completed. Success: {success_count}, Errors: {error_count}")
            
        except Exception as e:
            logger.error(f"Error during scheduled refresh: {e}")
        finally:
            db.close()

    async def refresh_cases_manually(self, case_ids: List[int] = None) -> dict:
        """Manually trigger case refresh"""
        db = SessionLocal()
        try:
            case_service = CaseService(db)
            
            if case_ids:
                cases = db.query(CaseModel).filter(CaseModel.id.in_(case_ids)).all()
            else:
                cases = db.query(CaseModel).all()
            
            logger.info(f"Manually refreshing {len(cases)} cases")
            
            results = {
                "total": len(cases),
                "success": 0,
                "errors": 0,
                "details": []
            }
            
            for case in cases:
                try:
                    await case_service.refresh_case(case.id, force_refresh=True)
                    results["success"] += 1
                    results["details"].append({
                        "case_id": case.id,
                        "cnr_number": case.cnr_number,
                        "status": "success"
                    })
                except Exception as e:
                    results["errors"] += 1
                    results["details"].append({
                        "case_id": case.id,
                        "cnr_number": case.cnr_number,
                        "status": "error",
                        "error": str(e)
                    })
            
            return results
            
        finally:
            db.close()

# Global scheduler instance
scheduler = SchedulerService()