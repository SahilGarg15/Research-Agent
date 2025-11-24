"""SQLite database for storing research history."""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import config


class ResearchDatabase:
    """Manages research history in SQLite."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database connection."""
        
        self.db_path = db_path or config.DATABASE_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
        
    def _init_database(self):
        """Create tables if they don't exist."""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Research sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS research_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    status TEXT DEFAULT 'running',
                    coverage_score REAL,
                    sources_count INTEGER,
                    facts_count INTEGER,
                    output_files TEXT,
                    metadata TEXT
                )
            """)
            
            # Sources table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    url TEXT NOT NULL,
                    title TEXT,
                    summary TEXT,
                    confidence_score REAL,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES research_sessions (id)
                )
            """)
            
            # Facts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    fact TEXT NOT NULL,
                    confidence_score REAL,
                    supporting_sources INTEGER,
                    has_contradiction BOOLEAN,
                    verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES research_sessions (id)
                )
            """)
            
            conn.commit()
            
    def create_session(self, query: str) -> int:
        """
        Create a new research session.
        
        Args:
            query: Research query
            
        Returns:
            Session ID
        """
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO research_sessions (query) VALUES (?)",
                (query,)
            )
            conn.commit()
            return cursor.lastrowid
            
    def update_session(
        self,
        session_id: int,
        status: str = None,
        coverage_score: float = None,
        sources_count: int = None,
        facts_count: int = None,
        output_files: Dict = None,
        metadata: Dict = None
    ):
        """Update a research session."""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if status:
                updates.append("status = ?")
                params.append(status)
                
                if status == "completed":
                    updates.append("completed_at = ?")
                    params.append(datetime.now())
                    
            if coverage_score is not None:
                updates.append("coverage_score = ?")
                params.append(coverage_score)
                
            if sources_count is not None:
                updates.append("sources_count = ?")
                params.append(sources_count)
                
            if facts_count is not None:
                updates.append("facts_count = ?")
                params.append(facts_count)
                
            if output_files is not None:
                updates.append("output_files = ?")
                params.append(json.dumps(output_files))
                
            if metadata is not None:
                updates.append("metadata = ?")
                params.append(json.dumps(metadata))
                
            if updates:
                params.append(session_id)
                query = f"UPDATE research_sessions SET {', '.join(updates)} WHERE id = ?"
                cursor.execute(query, params)
                conn.commit()
                
    def add_source(
        self,
        session_id: int,
        url: str,
        title: str = None,
        summary: str = None,
        confidence_score: float = None
    ):
        """Add a source to a session."""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO sources 
                   (session_id, url, title, summary, confidence_score)
                   VALUES (?, ?, ?, ?, ?)""",
                (session_id, url, title, summary, confidence_score)
            )
            conn.commit()
            
    def add_fact(
        self,
        session_id: int,
        fact: str,
        confidence_score: float,
        supporting_sources: int = 1,
        has_contradiction: bool = False
    ):
        """Add a verified fact to a session."""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO facts 
                   (session_id, fact, confidence_score, supporting_sources, has_contradiction)
                   VALUES (?, ?, ?, ?, ?)""",
                (session_id, fact, confidence_score, supporting_sources, has_contradiction)
            )
            conn.commit()
            
    def get_session(self, session_id: int) -> Optional[Dict]:
        """Get a research session by ID."""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM research_sessions WHERE id = ?",
                (session_id,)
            )
            
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
            
    def get_recent_sessions(self, limit: int = 10) -> List[Dict]:
        """Get recent research sessions."""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                """SELECT * FROM research_sessions 
                   ORDER BY created_at DESC 
                   LIMIT ?""",
                (limit,)
            )
            
            return [dict(row) for row in cursor.fetchall()]
            
    def search_sessions(self, query: str) -> List[Dict]:
        """Search sessions by query text."""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                """SELECT * FROM research_sessions 
                   WHERE query LIKE ? 
                   ORDER BY created_at DESC""",
                (f"%{query}%",)
            )
            
            return [dict(row) for row in cursor.fetchall()]
