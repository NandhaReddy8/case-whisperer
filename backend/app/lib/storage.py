"""
Storage layer for eCourt data based on working reference implementation.
Provides SQLite-based storage with proper indexing and JSON support.
"""

import sqlite3
import json
import logging
from typing import Optional, List, Iterator, Dict, Any
from collections.abc import Iterator as ABCIterator

from app.lib.entities import CaseType, Court, Case, ActType

logger = logging.getLogger(__name__)

class Storage:
    """
    SQLite-based storage for eCourt entities.
    Based on working reference implementation with improvements.
    """

    def __init__(self, filename: str = "cases.db"):
        self.filename = filename
        self.conn = sqlite3.connect(self.filename, check_same_thread=False)
        self._initialize_database()

    def _initialize_database(self):
        """Initialize database tables and indexes"""
        cursor = self.conn.cursor()
        
        # Case types table
        cursor.execute("CREATE TABLE IF NOT EXISTS case_types (value JSON)")
        cursor.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_case_types ON case_types("
            "json_extract(value, '$.code'), "
            "json_extract(value, '$.court_state_code'), "
            "json_extract(value, '$.court_court_code'))"
        )

        # Act types table
        cursor.execute("CREATE TABLE IF NOT EXISTS act_types (value JSON)")
        cursor.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_act_types ON act_types("
            "json_extract(value, '$.code'), "
            "json_extract(value, '$.court_state_code'), "
            "json_extract(value, '$.court_court_code'))"
        )
        
        # Courts table
        cursor.execute("CREATE TABLE IF NOT EXISTS courts (value JSON)")
        cursor.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_courts ON courts("
            "json_extract(value, '$.state_code'), "
            "json_extract(value, '$.court_code'))"
        )
        
        # Cases table with enhanced indexing
        cursor.execute("CREATE TABLE IF NOT EXISTS cases (state_code, court_code, value JSON)")
        cursor.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_cases_cnr ON cases("
            "json_extract(value, '$.cnr_number'))"
        )
        cursor.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_cases_caseno ON cases("
            "state_code, court_code, "
            "json_extract(value, '$.case_type'), "
            "json_extract(value, '$.registration_number'))"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_cases_category ON cases("
            "json_extract(value, '$.category'))"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_cases_status ON cases("
            "json_extract(value, '$.case_status'))"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_cases_type ON cases("
            "json_extract(value, '$.case_type'))"
        )
        
        cursor.close()
        self.conn.commit()

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    # Case Type methods
    
    def add_case_types(self, records: List[CaseType]):
        """Add case types to storage"""
        cursor = self.conn.cursor()
        for record in records:
            try:
                cursor.execute(
                    "INSERT OR IGNORE INTO case_types VALUES (?)",
                    (json.dumps(dict(record)),),
                )
            except Exception as e:
                logger.error(f"Failed to add case type {record}: {e}")
        cursor.close()
        self.conn.commit()

    def get_case_types(self, court: Optional[Court] = None) -> Iterator[CaseType]:
        """Get case types, optionally filtered by court"""
        query = "SELECT value FROM case_types"
        params = []
        
        if court:
            query += " WHERE json_extract(value, '$.court_state_code') = ?"
            params.append(court.state_code)
            if court.court_code:
                query += " AND json_extract(value, '$.court_court_code') = ?"
                params.append(court.court_code)
        
        cursor = self.conn.cursor()
        for record in cursor.execute(query, params):
            try:
                j = json.loads(record[0])
                court_obj = Court(
                    state_code=j["court_state_code"], 
                    court_code=j["court_court_code"]
                )
                yield CaseType(
                    code=j["code"], 
                    description=j["description"], 
                    court=court_obj
                )
            except Exception as e:
                logger.error(f"Failed to parse case type record: {e}")
        cursor.close()

    def find_case_type(self, court: Court, case_type: str) -> Optional[CaseType]:
        """Find case type by description"""
        for ct in self.get_case_types(court):
            if case_type == ct.description:
                return ct
            if ct.description.startswith(case_type + " - "):
                return ct
        return None

    # Act Type methods
    
    def add_act_types(self, records: List[ActType]):
        """Add act types to storage"""
        cursor = self.conn.cursor()
        for record in records:
            try:
                cursor.execute(
                    "INSERT OR IGNORE INTO act_types VALUES (?)",
                    (json.dumps(dict(record)),),
                )
            except Exception as e:
                logger.error(f"Failed to add act type {record}: {e}")
        cursor.close()
        self.conn.commit()

    def get_act_types(self, court: Optional[Court] = None) -> Iterator[ActType]:
        """Get act types, optionally filtered by court"""
        query = "SELECT value FROM act_types"
        params = []
        
        if court:
            query += " WHERE json_extract(value, '$.court_state_code') = ?"
            params.append(court.state_code)
            if court.court_code:
                query += " AND json_extract(value, '$.court_court_code') = ?"
                params.append(court.court_code)
        
        cursor = self.conn.cursor()
        for record in cursor.execute(query, params):
            try:
                j = json.loads(record[0])
                court_obj = Court(
                    state_code=j["court_state_code"], 
                    court_code=j["court_court_code"]
                )
                yield ActType(
                    code=j["code"], 
                    description=j["description"], 
                    court=court_obj
                )
            except Exception as e:
                logger.error(f"Failed to parse act type record: {e}")
        cursor.close()

    # Court methods
    
    def add_courts(self, records: List[Court]):
        """Add courts to storage"""
        cursor = self.conn.cursor()
        for record in records:
            try:
                cursor.execute(
                    "INSERT OR IGNORE INTO courts VALUES (?)", 
                    (json.dumps(record.json()),)
                )
            except Exception as e:
                logger.error(f"Failed to add court {record}: {e}")
        cursor.close()
        self.conn.commit()

    def get_courts(self) -> Iterator[Court]:
        """Get all courts"""
        cursor = self.conn.cursor()
        for record in cursor.execute("SELECT value FROM courts"):
            try:
                j = json.loads(record[0])
                yield Court(
                    state_code=j["state_code"],
                    district_code=j.get("district_code", "1"),
                    court_code=j.get("court_code")
                )
            except Exception as e:
                logger.error(f"Failed to parse court record: {e}")
        cursor.close()

    # Case methods
    
    def add_cases(self, court: Court, cases: List[Case], extra_fields: Dict[str, Any] = None):
        """Add or update cases in storage"""
        if extra_fields is None:
            extra_fields = {}
            
        cursor = self.conn.cursor()
        for case in cases:
            try:
                # Search for existing record using CNR
                search_result = cursor.execute(
                    "SELECT value FROM cases WHERE json_extract(value, '$.cnr_number') = ?", 
                    (case.cnr_number,)
                ).fetchone()
                
                case_data = case.json()
                case_data.update(extra_fields)
                
                if search_result:
                    # Update existing record
                    existing_row = json.loads(search_result[0])
                    
                    # Merge with existing data, preserving important fields
                    for key in ['status', 'year', 'act_type', 'case_type']:
                        if key not in case_data and key in existing_row:
                            case_data[key] = existing_row[key]
                    
                    cursor.execute(
                        "UPDATE cases SET value = ? WHERE json_extract(value, '$.cnr_number') = ?", 
                        (json.dumps(case_data, default=str), case.cnr_number)
                    )
                else:
                    # Insert new record
                    cursor.execute(
                        "INSERT INTO cases VALUES (?, ?, ?)", 
                        (court.state_code, court.court_code or "1", json.dumps(case_data, default=str))
                    )
            except Exception as e:
                logger.error(f"Failed to add/update case {case.cnr_number}: {e}")
        
        cursor.close()
        self.conn.commit()

    def get_cases(self, court: Optional[Court] = None, limit: Optional[int] = None) -> Iterator[Dict[str, Any]]:
        """Get cases, optionally filtered by court"""
        query = "SELECT state_code, court_code, value FROM cases"
        params = []
        
        if court:
            query += " WHERE state_code = ?"
            params.append(court.state_code)
            if court.court_code:
                query += " AND court_code = ?"
                params.append(court.court_code)
        
        query += " ORDER BY json_extract(value, '$.registration_date') DESC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor = self.conn.cursor()
        for state_code, court_code, value in cursor.execute(query, params):
            try:
                case_data = json.loads(value)
                case_data.update({
                    "state_code": state_code, 
                    "court_code": court_code
                })
                yield case_data
            except Exception as e:
                logger.error(f"Failed to parse case record: {e}")
        cursor.close()

    def get_case_by_cnr(self, cnr_number: str) -> Optional[Dict[str, Any]]:
        """Get case by CNR number"""
        cursor = self.conn.cursor()
        result = cursor.execute(
            "SELECT state_code, court_code, value FROM cases WHERE json_extract(value, '$.cnr_number') = ?",
            (cnr_number,)
        ).fetchone()
        cursor.close()
        
        if result:
            try:
                state_code, court_code, value = result
                case_data = json.loads(value)
                case_data.update({
                    "state_code": state_code,
                    "court_code": court_code
                })
                return case_data
            except Exception as e:
                logger.error(f"Failed to parse case record: {e}")
        
        return None

    def delete_case(self, cnr_number: str) -> bool:
        """Delete case by CNR number"""
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM cases WHERE json_extract(value, '$.cnr_number') = ?",
            (cnr_number,)
        )
        deleted = cursor.rowcount > 0
        cursor.close()
        self.conn.commit()
        return deleted

    def search_cases(self, query: str, field: str = "petitioners") -> Iterator[Dict[str, Any]]:
        """Search cases by field content"""
        sql_query = f"SELECT state_code, court_code, value FROM cases WHERE json_extract(value, '$.{field}') LIKE ?"
        params = [f"%{query}%"]
        
        cursor = self.conn.cursor()
        for state_code, court_code, value in cursor.execute(sql_query, params):
            try:
                case_data = json.loads(value)
                case_data.update({
                    "state_code": state_code,
                    "court_code": court_code
                })
                yield case_data
            except Exception as e:
                logger.error(f"Failed to parse case record: {e}")
        cursor.close()

    def get_cases_by_status(self, status: str, court: Optional[Court] = None) -> Iterator[Dict[str, Any]]:
        """Get cases by status"""
        query = "SELECT state_code, court_code, value FROM cases WHERE json_extract(value, '$.case_status') = ?"
        params = [status]
        
        if court:
            query += " AND state_code = ?"
            params.append(court.state_code)
            if court.court_code:
                query += " AND court_code = ?"
                params.append(court.court_code)
        
        cursor = self.conn.cursor()
        for state_code, court_code, value in cursor.execute(query, params):
            try:
                case_data = json.loads(value)
                case_data.update({
                    "state_code": state_code,
                    "court_code": court_code
                })
                yield case_data
            except Exception as e:
                logger.error(f"Failed to parse case record: {e}")
        cursor.close()

    def stats(self) -> Dict[str, int]:
        """Get storage statistics"""
        tables = ["case_types", "act_types", "courts", "cases"]
        stats = {}
        cursor = self.conn.cursor()
        
        for table in tables:
            try:
                result = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
                stats[table] = result[0] if result else 0
            except Exception as e:
                logger.error(f"Failed to get stats for {table}: {e}")
                stats[table] = 0
        
        cursor.close()
        return stats

    def vacuum(self):
        """Optimize database"""
        try:
            self.conn.execute("VACUUM")
            self.conn.commit()
        except Exception as e:
            logger.error(f"Failed to vacuum database: {e}")

    def backup(self, backup_filename: str):
        """Create database backup"""
        try:
            backup_conn = sqlite3.connect(backup_filename)
            self.conn.backup(backup_conn)
            backup_conn.close()
            return True
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            return False