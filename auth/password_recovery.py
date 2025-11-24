"""
Password Recovery System
Provides token-based password reset functionality.
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class PasswordRecovery:
    """Handle password recovery with secure tokens."""
    
    def __init__(self, db):
        """
        Initialize password recovery system.
        
        Args:
            db: UserDatabase instance
        """
        self.db = db
        self.token_validity_hours = 1  # Reset tokens valid for 1 hour
        self._create_table()
    
    def _create_table(self):
        """Create password recovery tokens table."""
        import sqlite3
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                used INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        conn.commit()
        conn.close()
    
    def generate_reset_token(self, email: str) -> Optional[str]:
        """
        Generate password reset token for user.
        
        Args:
            email: User email address
            
        Returns:
            Reset token or None if user not found
        """
        # Check if user exists
        user = self.db.get_user_by_email(email)
        if not user:
            logger.warning(f"Reset token requested for non-existent email: {email}")
            return None
        
        user_id = user["id"]
        
        # Generate secure token
        token = secrets.token_urlsafe(32)
        
        # Calculate expiry
        created_at = datetime.now()
        expires_at = created_at + timedelta(hours=self.token_validity_hours)
        
        # Store token
        try:
            import sqlite3
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO password_reset_tokens (user_id, token, created_at, expires_at)
                VALUES (?, ?, ?, ?)
            """, (
                user_id,
                token,
                created_at.isoformat(),
                expires_at.isoformat()
            ))
            conn.commit()
            conn.close()
            
            logger.info(f"Reset token generated for user {user_id}")
            return token
        
        except Exception as e:
            logger.error(f"Failed to generate reset token: {e}")
            return None
    
    def validate_token(self, token: str) -> Optional[int]:
        """
        Validate reset token and return user_id if valid.
        
        Args:
            token: Reset token to validate
            
        Returns:
            User ID if valid, None otherwise
        """
        try:
            import sqlite3
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, expires_at, used
                FROM password_reset_tokens
                WHERE token = ?
            """, (token,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                logger.warning("Invalid reset token")
                return None
            
            user_id, expires_at, used = result
            
            # Check if already used
            if used:
                logger.warning("Reset token already used")
                return None
            
            # Check expiry
            expires_at_dt = datetime.fromisoformat(expires_at)
            if datetime.now() > expires_at_dt:
                logger.warning("Reset token expired")
                return None
            
            return user_id
        
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return None
    
    def reset_password(self, token: str, new_password: str) -> bool:
        """
        Reset password using valid token.
        
        Args:
            token: Valid reset token
            new_password: New password
            
        Returns:
            True if successful, False otherwise
        """
        # Validate token
        user_id = self.validate_token(token)
        if not user_id:
            return False
        
        try:
            # Update password
            success = self.db.update_password(user_id, new_password)
            
            if success:
                # Mark token as used
                import sqlite3
                conn = sqlite3.connect(self.db.db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE password_reset_tokens
                    SET used = 1
                    WHERE token = ?
                """, (token,))
                conn.commit()
                conn.close()
                
                logger.info(f"Password reset successful for user {user_id}")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Password reset failed: {e}")
            return False
    
    def cleanup_expired_tokens(self):
        """Remove expired and used tokens."""
        try:
            import sqlite3
            now = datetime.now().isoformat()
            
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM password_reset_tokens
                WHERE expires_at < ? OR used = 1
            """, (now,))
            
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"Cleaned up {deleted} expired/used reset tokens")
        
        except Exception as e:
            logger.error(f"Token cleanup failed: {e}")
    
    def send_reset_email(self, email: str, token: str) -> bool:
        """
        Send password reset email (placeholder for actual email integration).
        
        Args:
            email: User email
            token: Reset token
            
        Returns:
            True if email sent successfully
        """
        # In production, integrate with email service (SendGrid, AWS SES, etc.)
        # For now, just log the reset link
        
        reset_link = f"http://localhost:8000/reset-password?token={token}"
        
        logger.info(f"""
        ===== PASSWORD RESET EMAIL =====
        To: {email}
        
        You requested a password reset for your Auto-Research Agent account.
        
        Click the link below to reset your password (valid for {self.token_validity_hours} hour):
        {reset_link}
        
        If you didn't request this, please ignore this email.
        
        ================================
        """)
        
        # TODO: Replace with actual email sending
        # For demo, display in console
        print(f"\n🔐 Password Reset Link: {reset_link}\n")
        
        return True
    
    def request_password_reset(self, email: str) -> bool:
        """
        Complete password reset request (generate token + send email).
        
        Args:
            email: User email address
            
        Returns:
            True if request processed successfully
        """
        # Generate token
        token = self.generate_reset_token(email)
        if not token:
            # Return True anyway to prevent email enumeration
            logger.warning(f"Password reset requested for unknown email: {email}")
            return True
        
        # Send email
        return self.send_reset_email(email, token)


class PasswordResetGUI:
    """GUI for password reset flow (optional)."""
    
    @staticmethod
    def show_forgot_password_dialog():
        """Show forgot password dialog."""
        import tkinter as tk
        from tkinter import messagebox
        
        dialog = tk.Toplevel()
        dialog.title("Forgot Password")
        dialog.geometry("400x200")
        dialog.configure(bg="#1e1e1e")
        
        # Email input
        tk.Label(
            dialog,
            text="Enter your email address:",
            bg="#1e1e1e",
            fg="white",
            font=("Segoe UI", 11)
        ).pack(pady=(20, 10))
        
        email_entry = tk.Entry(
            dialog,
            font=("Segoe UI", 11),
            width=35
        )
        email_entry.pack(pady=10)
        
        def submit():
            email = email_entry.get().strip()
            if not email:
                messagebox.showwarning("Input Required", "Please enter your email address.")
                return
            
            # Import here to avoid circular dependency
            from auth.authentication import UserDatabase
            
            db = UserDatabase()
            recovery = PasswordRecovery(db)
            
            success = recovery.request_password_reset(email)
            
            if success:
                messagebox.showinfo(
                    "Email Sent",
                    "If an account exists with this email, you will receive password reset instructions."
                )
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to process request. Please try again.")
        
        # Submit button
        tk.Button(
            dialog,
            text="Send Reset Link",
            bg="#007acc",
            fg="white",
            font=("Segoe UI", 11),
            command=submit,
            cursor="hand2"
        ).pack(pady=20)
        
        dialog.transient()
        dialog.grab_set()
    
    @staticmethod
    def show_reset_password_dialog(token: str):
        """Show reset password dialog."""
        import tkinter as tk
        from tkinter import messagebox
        
        dialog = tk.Toplevel()
        dialog.title("Reset Password")
        dialog.geometry("400x250")
        dialog.configure(bg="#1e1e1e")
        
        # New password
        tk.Label(
            dialog,
            text="New Password:",
            bg="#1e1e1e",
            fg="white",
            font=("Segoe UI", 11)
        ).pack(pady=(20, 5))
        
        password_entry = tk.Entry(
            dialog,
            font=("Segoe UI", 11),
            width=35,
            show="*"
        )
        password_entry.pack(pady=5)
        
        # Confirm password
        tk.Label(
            dialog,
            text="Confirm Password:",
            bg="#1e1e1e",
            fg="white",
            font=("Segoe UI", 11)
        ).pack(pady=(10, 5))
        
        confirm_entry = tk.Entry(
            dialog,
            font=("Segoe UI", 11),
            width=35,
            show="*"
        )
        confirm_entry.pack(pady=5)
        
        def submit():
            password = password_entry.get()
            confirm = confirm_entry.get()
            
            if not password or not confirm:
                messagebox.showwarning("Input Required", "Please fill in all fields.")
                return
            
            if password != confirm:
                messagebox.showerror("Error", "Passwords do not match.")
                return
            
            # Import here to avoid circular dependency
            from auth.authentication import UserDatabase
            
            db = UserDatabase()
            recovery = PasswordRecovery(db)
            
            success = recovery.reset_password(token, password)
            
            if success:
                messagebox.showinfo(
                    "Success",
                    "Password reset successfully! You can now login with your new password."
                )
                dialog.destroy()
            else:
                messagebox.showerror(
                    "Error",
                    "Invalid or expired reset token. Please request a new password reset."
                )
        
        # Submit button
        tk.Button(
            dialog,
            text="Reset Password",
            bg="#007acc",
            fg="white",
            font=("Segoe UI", 11),
            command=submit,
            cursor="hand2"
        ).pack(pady=20)
        
        dialog.transient()
        dialog.grab_set()


if __name__ == "__main__":
    # Test password recovery
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from auth.authentication import UserDatabase
    
    db = UserDatabase()
    recovery = PasswordRecovery(db)
    
    # Test: Generate token for existing user
    token = recovery.generate_reset_token("test@example.com")
    print(f"Generated token: {token}")
    
    if token:
        # Validate token
        user_id = recovery.validate_token(token)
        print(f"Validated user ID: {user_id}")
        
        # Test reset
        # success = recovery.reset_password(token, "newpassword123")
        # print(f"Reset success: {success}")
