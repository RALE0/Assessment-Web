"""
Authentication models and database operations for the crop recommendation API.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
import jwt as PyJWT
import uuid
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class AuthDatabase:
    """Database operations for authentication system."""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
    
    def get_connection(self):
        """Get database connection with timeout."""
        try:
            return psycopg2.connect(**self.db_config)
        except psycopg2.OperationalError as e:
            logger.error(f"Database connection timeout/error: {e}")
            return None
        except psycopg2.Error as e:
            logger.error(f"Database connection error: {e}")
            return None
    
    def create_user(self, username: str, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Create a new user account."""
        try:
            conn = self.get_connection()
            if not conn:
                return None
            
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Check if username or email already exists
            cursor.execute(
                "SELECT id FROM users WHERE username = %s OR email = %s",
                (username, email)
            )
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return None  # User already exists
            
            # Hash password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            user_id = str(uuid.uuid4())
            
            # Insert new user
            cursor.execute("""
                INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, username, email, created_at, last_login_at
            """, (user_id, username, email, password_hash, datetime.now(), datetime.now()))
            
            user = cursor.fetchone()
            conn.commit()
            cursor.close()
            conn.close()
            
            return dict(user) if user else None
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user credentials."""
        try:
            conn = self.get_connection()
            if not conn:
                return None
            
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get user by username
            cursor.execute("""
                SELECT id, username, email, password_hash, failed_login_attempts, 
                       locked_until, is_active, last_login_at
                FROM users 
                WHERE username = %s AND is_active = true
            """, (username,))
            
            user = cursor.fetchone()
            if not user:
                cursor.close()
                conn.close()
                return None
            
            # Check if account is locked
            if user['locked_until'] and user['locked_until'] > datetime.now():
                cursor.close()
                conn.close()
                return None
            
            # Verify password
            if bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                # Successful login - reset failed attempts and update last login
                cursor.execute("""
                    UPDATE users 
                    SET failed_login_attempts = 0, last_login_at = %s, locked_until = NULL
                    WHERE id = %s
                """, (datetime.now(), user['id']))
                conn.commit()
                
                # Return user data without password hash
                user_data = dict(user)
                del user_data['password_hash']
                user_data['last_login_at'] = datetime.now()
                
                cursor.close()
                conn.close()
                return user_data
            else:
                # Failed login - increment failed attempts
                new_attempts = user['failed_login_attempts'] + 1
                locked_until = None
                
                if new_attempts >= 5:
                    locked_until = datetime.now() + timedelta(minutes=15)
                
                cursor.execute("""
                    UPDATE users 
                    SET failed_login_attempts = %s, locked_until = %s
                    WHERE id = %s
                """, (new_attempts, locked_until, user['id']))
                conn.commit()
                
                cursor.close()
                conn.close()
                return None
                
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None
    
    def create_session(self, user_id: str, ip_address: str, user_agent: str) -> Optional[str]:
        """Create a new user session."""
        try:
            conn = self.get_connection()
            if not conn:
                return None
            
            cursor = conn.cursor()
            
            # Generate session token
            session_token = secrets.token_urlsafe(32)
            session_id = str(uuid.uuid4())
            expires_at = datetime.now() + timedelta(hours=24)
            
            cursor.execute("""
                INSERT INTO user_sessions 
                (id, user_id, session_token, ip_address, user_agent, expires_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (session_id, user_id, session_token, ip_address, user_agent, expires_at))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return session_token
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return None
    
    def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Validate session token and return user data."""
        try:
            conn = self.get_connection()
            if not conn:
                return None
            
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT us.*, u.username, u.email 
                FROM user_sessions us
                JOIN users u ON u.id = us.user_id
                WHERE us.session_token = %s 
                  AND us.is_active = true 
                  AND us.expires_at > %s
            """, (session_token, datetime.now()))
            
            session = cursor.fetchone()
            if session:
                # Update last activity
                cursor.execute("""
                    UPDATE user_sessions 
                    SET last_activity_at = %s 
                    WHERE session_token = %s
                """, (datetime.now(), session_token))
                conn.commit()
            
            cursor.close()
            conn.close()
            
            return dict(session) if session else None
            
        except Exception as e:
            logger.error(f"Error validating session: {e}")
            return None
    
    def end_session(self, session_token: str, logout_reason: str = 'user_logout') -> bool:
        """End a user session."""
        try:
            conn = self.get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE user_sessions 
                SET is_active = false, ended_at = %s, logout_reason = %s
                WHERE session_token = %s
            """, (datetime.now(), logout_reason, session_token))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            return False
    
    def log_activity(self, user_id: str, session_id: str, activity_type: str, 
                    details: Dict[str, Any], ip_address: str, user_agent: str) -> bool:
        """Log user activity."""
        try:
            conn = self.get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO session_activities 
                (user_id, session_id, activity_type, activity_details, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, session_id, activity_type, 
                  psycopg2.extras.Json(details), ip_address, user_agent))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error logging activity: {e}")
            return False
    
    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get session history for a user."""
        try:
            conn = self.get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT us.*, 
                       COALESCE(
                           EXTRACT(EPOCH FROM (us.ended_at - us.created_at)),
                           EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - us.created_at))
                       ) as duration_seconds
                FROM user_sessions us
                WHERE us.user_id = %s
                ORDER BY us.created_at DESC
                LIMIT 50
            """, (user_id,))
            
            sessions = cursor.fetchall()
            
            # Get activities for each session
            session_list = []
            for session in sessions:
                cursor.execute("""
                    SELECT * FROM session_activities 
                    WHERE session_id = %s 
                    ORDER BY timestamp DESC
                """, (session['id'],))
                
                activities = cursor.fetchall()
                session_dict = dict(session)
                session_dict['activities'] = [dict(activity) for activity in activities]
                session_list.append(session_dict)
            
            cursor.close()
            conn.close()
            
            return session_list
            
        except Exception as e:
            logger.error(f"Error getting user sessions: {e}")
            return []
    
    def create_password_reset_token(self, email: str, ip_address: str, user_agent: str) -> Optional[str]:
        """Create password reset token."""
        try:
            conn = self.get_connection()
            if not conn:
                return None
            
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE email = %s AND is_active = true", (email,))
            user = cursor.fetchone()
            if not user:
                cursor.close()
                conn.close()
                return None
            
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=1)
            
            cursor.execute("""
                INSERT INTO password_reset_tokens 
                (user_id, token, expires_at, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s)
            """, (user['id'], reset_token, expires_at, ip_address, user_agent))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return reset_token
            
        except Exception as e:
            logger.error(f"Error creating password reset token: {e}")
            return None

class JWTManager:
    """JWT token management."""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    def generate_token(self, user_data: Dict[str, Any], session_token: str) -> str:
        """Generate JWT token."""
        payload = {
            'user_id': user_data['id'],
            'username': user_data['username'],
            'email': user_data.get('email'),
            'session_token': session_token,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        
        return PyJWT.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token."""
        try:
            payload = PyJWT.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except PyJWT.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except PyJWT.InvalidTokenError:
            logger.warning("Invalid token")
            return None