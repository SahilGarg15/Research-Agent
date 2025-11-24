"""
User Authentication System
Handles signup, login, password hashing, JWT tokens, and user management.
"""

import sqlite3
import hashlib
import secrets
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import bcrypt
import jwt
import logging

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Custom exception for authentication errors."""
    pass


class UserDatabase:
    """SQLite database for user management."""
    
    def __init__(self, db_path: str = "data/users.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                tier TEXT DEFAULT 'free',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                email_verified BOOLEAN DEFAULT 0,
                failed_login_attempts INTEGER DEFAULT 0,
                account_locked_until TIMESTAMP
            )
        ''')
        
        # Usage tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usage_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date DATE NOT NULL,
                searches_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, date)
            )
        ''')
        
        # Research history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS research_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                query TEXT NOT NULL,
                tier TEXT NOT NULL,
                word_count INTEGER,
                sources_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                report_path TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized")
    
    def create_user(
        self,
        name: str,
        email: str,
        username: str,
        password: str
    ) -> int:
        """Create a new user."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Hash password with bcrypt
            password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            
            cursor.execute('''
                INSERT INTO users (name, email, username, password_hash)
                VALUES (?, ?, ?, ?)
            ''', (name, email, username, password_hash))
            
            user_id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"User created: {username} (ID: {user_id})")
            return user_id
            
        except sqlite3.IntegrityError as e:
            logger.error(f"User creation failed: {e}")
            if "email" in str(e):
                raise AuthenticationError("Email already registered")
            elif "username" in str(e):
                raise AuthenticationError("Username already taken")
            else:
                raise AuthenticationError("User creation failed")
        finally:
            conn.close()
    
    def verify_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Verify user credentials."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, name, email, username, password_hash, tier, 
                       failed_login_attempts, account_locked_until
                FROM users 
                WHERE username = ? OR email = ?
            ''', (username, username))
            
            row = cursor.fetchone()
            
            if not row:
                return None
            
            user_id, name, email, uname, password_hash, tier, failed_attempts, locked_until = row
            
            # Check if account is locked
            if locked_until:
                lock_time = datetime.fromisoformat(locked_until)
                if datetime.now() < lock_time:
                    remaining = (lock_time - datetime.now()).seconds // 60
                    raise AuthenticationError(f"Account locked. Try again in {remaining} minutes")
            
            # Verify password
            if bcrypt.checkpw(password.encode(), password_hash.encode()):
                # Reset failed attempts
                cursor.execute('''
                    UPDATE users 
                    SET failed_login_attempts = 0, 
                        account_locked_until = NULL,
                        last_login = ?
                    WHERE id = ?
                ''', (datetime.now(), user_id))
                conn.commit()
                
                logger.info(f"User logged in: {uname}")
                
                return {
                    "id": user_id,
                    "name": name,
                    "email": email,
                    "username": uname,
                    "tier": tier
                }
            else:
                # Increment failed attempts
                failed_attempts += 1
                
                if failed_attempts >= 5:
                    # Lock account for 30 minutes
                    locked_until = datetime.now() + timedelta(minutes=30)
                    cursor.execute('''
                        UPDATE users 
                        SET failed_login_attempts = ?,
                            account_locked_until = ?
                        WHERE id = ?
                    ''', (failed_attempts, locked_until, user_id))
                    conn.commit()
                    raise AuthenticationError("Account locked due to too many failed attempts")
                else:
                    cursor.execute('''
                        UPDATE users 
                        SET failed_login_attempts = ?
                        WHERE id = ?
                    ''', (failed_attempts, user_id))
                    conn.commit()
                    
                return None
                
        finally:
            conn.close()
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, name, email, username, tier, created_at, last_login
                FROM users 
                WHERE id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            
            if row:
                return {
                    "id": row[0],
                    "name": row[1],
                    "email": row[2],
                    "username": row[3],
                    "tier": row[4],
                    "created_at": row[5],
                    "last_login": row[6]
                }
            return None
            
        finally:
            conn.close()
    
    def upgrade_user(self, user_id: int, tier: str = "premium"):
        """Upgrade user to premium tier."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE users 
                SET tier = ?
                WHERE id = ?
            ''', (tier, user_id))
            conn.commit()
            logger.info(f"User {user_id} upgraded to {tier}")
            
        finally:
            conn.close()


class UsageTracker:
    """Track user research usage and enforce limits."""
    
    def __init__(self, db_path: str = "data/users.db"):
        self.db_path = db_path
    
    def get_usage_today(self, user_id: int) -> int:
        """Get user's search count for today."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            today = datetime.now().date()
            
            cursor.execute('''
                SELECT searches_count 
                FROM usage_tracking 
                WHERE user_id = ? AND date = ?
            ''', (user_id, today))
            
            row = cursor.fetchone()
            return row[0] if row else 0
            
        finally:
            conn.close()
    
    def increment_usage(self, user_id: int):
        """Increment user's daily usage count."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            today = datetime.now().date()
            
            cursor.execute('''
                INSERT INTO usage_tracking (user_id, date, searches_count)
                VALUES (?, ?, 1)
                ON CONFLICT(user_id, date) 
                DO UPDATE SET searches_count = searches_count + 1
            ''', (user_id, today))
            
            conn.commit()
            
        finally:
            conn.close()
    
    def can_search(self, user_id: int, tier: str) -> tuple[bool, str]:
        """Check if user can perform a search."""
        if tier == "premium":
            return True, ""
        
        usage_today = self.get_usage_today(user_id)
        
        if usage_today >= 5:
            return False, "Daily free search limit reached (5/5). Upgrade to Premium for unlimited searches!"
        
        return True, f"Searches used today: {usage_today}/5"
    
    def add_research_history(
        self,
        user_id: int,
        query: str,
        tier: str,
        word_count: int,
        sources_count: int,
        report_path: str
    ):
        """Add research to user's history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO research_history 
                (user_id, query, tier, word_count, sources_count, report_path)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, query, tier, word_count, sources_count, report_path))
            
            conn.commit()
            
        finally:
            conn.close()
    
    def get_research_history(self, user_id: int, limit: int = 20) -> list:
        """Get user's research history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT query, tier, word_count, sources_count, created_at, report_path
                FROM research_history
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (user_id, limit))
            
            rows = cursor.fetchall()
            
            return [{
                "query": row[0],
                "tier": row[1],
                "word_count": row[2],
                "sources_count": row[3],
                "created_at": row[4],
                "report_path": row[5]
            } for row in rows]
            
        finally:
            conn.close()


class JWTManager:
    """Manage JWT tokens for session management."""
    
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or secrets.token_hex(32)
    
    def generate_token(self, user_id: int, username: str, tier: str) -> str:
        """Generate JWT token."""
        payload = {
            "user_id": user_id,
            "username": username,
            "tier": tier,
            "exp": datetime.utcnow() + timedelta(days=7)
        }
        
        return jwt.encode(payload, self.secret_key, algorithm="HS256")
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None


class PasswordValidator:
    """Validate password strength."""
    
    @staticmethod
    def validate(password: str) -> tuple[bool, str]:
        """
        Validate password strength.
        
        Requirements:
        - At least 8 characters
        - Contains uppercase and lowercase
        - Contains at least one digit
        - Contains at least one special character
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r"\d", password):
            return False, "Password must contain at least one digit"
        
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return False, "Password must contain at least one special character"
        
        return True, "Password is strong"


class EmailValidator:
    """Validate email format."""
    
    @staticmethod
    def validate(email: str) -> tuple[bool, str]:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if re.match(pattern, email):
            return True, "Valid email"
        else:
            return False, "Invalid email format"


# Singleton instances
_user_db = None
_usage_tracker = None
_jwt_manager = None


def get_user_db() -> UserDatabase:
    """Get singleton UserDatabase instance."""
    global _user_db
    if _user_db is None:
        _user_db = UserDatabase()
    return _user_db


def get_usage_tracker() -> UsageTracker:
    """Get singleton UsageTracker instance."""
    global _usage_tracker
    if _usage_tracker is None:
        _usage_tracker = UsageTracker()
    return _usage_tracker


def get_jwt_manager() -> JWTManager:
    """Get singleton JWTManager instance."""
    global _jwt_manager
    if _jwt_manager is None:
        _jwt_manager = JWTManager()
    return _jwt_manager
