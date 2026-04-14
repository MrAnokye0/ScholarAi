"""
Complete Secure Authentication System for ScholarAI
Implements registration, login, forgot/reset password, and remember me functionality
"""

import os
import secrets
import hashlib
import jwt
import bcrypt
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from fastapi import FastAPI, HTTPException, Depends, Request, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, validator
import psycopg2
from psycopg2.extras import RealDictCursor

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 30
RESET_TOKEN_EXPIRE_MINUTES = 15

# Database connection (configure with your actual database settings)
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "scholarai"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "password")
}

# Email configuration
SMTP_CONFIG = {
    "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
    "port": int(os.getenv("SMTP_PORT", "587")),
    "username": os.getenv("SMTP_USERNAME", ""),
    "password": os.getenv("SMTP_PASSWORD", "")
}

# Pydantic Models
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3 or len(v) > 50:
            raise ValueError('Username must be between 3 and 50 characters')
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        is_valid, errors = PasswordValidator.validate_password_strength(v)
        if not is_valid:
            raise ValueError('; '.join(errors))
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False

class ForgotPassword(BaseModel):
    email: EmailStr

class ResetPassword(BaseModel):
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        is_valid, errors = PasswordValidator.validate_password_strength(v)
        if not is_valid:
            raise ValueError('; '.join(errors))
        return v

class PasswordValidator:
    """Handles password validation and security"""
    
    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
        """Validate password against security requirements."""
        errors = []
        
        # Length validation
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        elif len(password) > 128:
            errors.append("Password must not exceed 128 characters")
        
        # Character requirements
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:"\\|,.<>\/?]', password):
            errors.append("Password must contain at least one special character")
        
        # Common password patterns
        if re.search(r'(.)\1{2,}', password):
            errors.append("Password cannot contain 3 or more repeated characters")
        
        # Check against common weak passwords
        weak_passwords = [
            'password', '123456', 'qwerty', 'admin', 'letmein',
            'welcome', 'monkey', '123456789', 'password123', 'scholarai'
        ]
        if password.lower() in weak_passwords:
            errors.append("Password is too common and weak")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    @staticmethod
    def hash_token(token: str) -> str:
        """Hash token for secure storage."""
        return hashlib.sha256(token.encode()).hexdigest()

class DatabaseManager:
    """Handles database operations"""
    
    def __init__(self):
        self.config = DB_CONFIG
    
    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(**self.config)
    
    def execute_query(self, query: str, params: tuple = None, fetch: bool = False):
        """Execute database query"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                if fetch:
                    result = cursor.fetchall()
                    return result
                conn.commit()
                return cursor.rowcount
        finally:
            conn.close()
    
    def user_exists(self, email: str) -> bool:
        """Check if user exists"""
        query = "SELECT id FROM users WHERE email = %s"
        result = self.execute_query(query, (email,), fetch=True)
        return len(result) > 0
    
    def username_exists(self, username: str) -> bool:
        """Check if username exists"""
        query = "SELECT id FROM users WHERE username = %s"
        result = self.execute_query(query, (username,), fetch=True)
        return len(result) > 0
    
    def create_user(self, username: str, email: str, password_hash: str) -> str:
        """Create new user"""
        user_id = str(secrets.uuid4())
        query = """
        INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        self.execute_query(query, (user_id, username, email, password_hash, datetime.now(), datetime.now()))
        
        # Add to password history
        self.add_password_history(user_id, password_hash)
        return user_id
    
    def add_password_history(self, user_id: str, password_hash: str):
        """Add password to history"""
        query = "INSERT INTO password_history (user_id, password_hash) VALUES (%s, %s)"
        self.execute_query(query, (user_id, password_hash))
    
    def check_password_reuse(self, user_id: str, new_password: str) -> bool:
        """Check if password has been used before"""
        query = """
        SELECT password_hash FROM password_history 
        WHERE user_id = %s 
        ORDER BY created_at DESC 
        LIMIT 5
        """
        old_passwords = self.execute_query(query, (user_id,), fetch=True)
        
        for old_password in old_passwords:
            if PasswordValidator.verify_password(new_password, old_password['password_hash']):
                return True  # Password has been reused
        
        return False
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        query = "SELECT * FROM users WHERE email = %s AND is_active = TRUE"
        result = self.execute_query(query, (email,), fetch=True)
        return result[0] if result else None
    
    def create_reset_token(self, user_id: str) -> str:
        """Create password reset token"""
        token = secrets.urlsafe_b64encode(secrets.token_bytes(32)).decode()
        token_hash = PasswordValidator.hash_token(token)
        expires_at = datetime.now() + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
        
        # Delete any existing tokens for this user
        self.execute_query("DELETE FROM password_reset_tokens WHERE user_id = %s", (user_id,))
        
        # Create new token
        query = """
        INSERT INTO password_reset_tokens (user_id, token, expires_at)
        VALUES (%s, %s, %s)
        """
        self.execute_query(query, (user_id, token_hash, expires_at))
        return token
    
    def validate_reset_token(self, token: str) -> Optional[Dict]:
        """Validate reset token"""
        token_hash = PasswordValidator.hash_token(token)
        query = """
        SELECT pr.*, u.email, u.id as user_id 
        FROM password_reset_tokens pr
        JOIN users u ON pr.user_id = u.id
        WHERE pr.token = %s AND pr.used = FALSE AND pr.expires_at > %s
        """
        result = self.execute_query(query, (token_hash, datetime.now()), fetch=True)
        return result[0] if result else None
    
    def invalidate_reset_token(self, token: str):
        """Mark reset token as used"""
        token_hash = PasswordValidator.hash_token(token)
        query = "UPDATE password_reset_tokens SET used = TRUE WHERE token = %s"
        self.execute_query(query, (token_hash,))
    
    def update_user_password(self, user_id: str, new_password_hash: str):
        """Update user password"""
        query = "UPDATE users SET password_hash = %s, updated_at = %s WHERE id = %s"
        self.execute_query(query, (new_password_hash, datetime.now(), user_id))
        self.add_password_history(user_id, new_password_hash)
    
    def create_refresh_token(self, user_id: str, device_info: str = None, ip_address: str = None) -> str:
        """Create refresh token"""
        token = secrets.token_urlsafe(32)
        token_hash = PasswordValidator.hash_token(token)
        expires_at = datetime.now() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        query = """
        INSERT INTO refresh_tokens (user_id, token_hash, device_info, ip_address, expires_at)
        VALUES (%s, %s, %s, %s, %s)
        """
        self.execute_query(query, (user_id, token_hash, device_info, ip_address, expires_at))
        return token
    
    def validate_refresh_token(self, token: str) -> Optional[Dict]:
        """Validate refresh token"""
        token_hash = PasswordValidator.hash_token(token)
        query = """
        SELECT rt.*, u.username, u.email 
        FROM refresh_tokens rt
        JOIN users u ON rt.user_id = u.id
        WHERE rt.token_hash = %s AND rt.expires_at > %s
        """
        result = self.execute_query(query, (token_hash, datetime.now()), fetch=True)
        return result[0] if result else None
    
    def revoke_refresh_token(self, token: str):
        """Revoke refresh token"""
        token_hash = PasswordValidator.hash_token(token)
        query = "DELETE FROM refresh_tokens WHERE token_hash = %s"
        self.execute_query(query, (token_hash,))
    
    def revoke_all_refresh_tokens(self, user_id: str):
        """Revoke all refresh tokens for user"""
        query = "DELETE FROM refresh_tokens WHERE user_id = %s"
        self.execute_query(query, (user_id,))

class EmailService:
    """Handles email operations with improved error handling"""
    
    @staticmethod
    def send_password_reset_email(email: str, reset_token: str):
        """Send password reset email with fallback"""
        reset_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:8501')}/reset-password?token={reset_token}"
        
        subject = "Password Reset - ScholarAI"
        body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9;">
            <div style="background-color: #4361EE; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 24px;">🎓 ScholarAI</h1>
                <p style="color: white; margin: 5px 0 0; font-size: 16px;">Password Reset Request</p>
            </div>
            
            <div style="background-color: white; padding: 30px; border-radius: 0 0 8px 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <p style="color: #333; font-size: 16px; line-height: 1.5;">Hello,</p>
                
                <p style="color: #333; font-size: 16px; line-height: 1.5;">
                    We received a request to reset your password for your ScholarAI account. 
                    Click the button below to reset your password:
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" 
                       style="background-color: #4361EE; color: white; padding: 15px 30px; text-decoration: none; 
                              border-radius: 5px; font-size: 16px; font-weight: bold; display: inline-block;">
                        Reset Password
                    </a>
                </div>
                
                <p style="color: #666; font-size: 14px; line-height: 1.5;">
                    If the button doesn't work, copy and paste this link into your browser:
                </p>
                
                <p style="background-color: #f5f5f5; padding: 10px; border-radius: 4px; word-break: break-all; 
                          font-size: 12px; color: #4361EE;">
                    {reset_url}
                </p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                
                <p style="color: #999; font-size: 12px; line-height: 1.5;">
                    <strong>Important:</strong> This link will expire in 15 minutes for security reasons.
                    If you didn't request this password reset, you can safely ignore this email.
                </p>
                
                <p style="color: #666; font-size: 14px; line-height: 1.5;">
                    Best regards,<br>
                    The ScholarAI Team
                </p>
            </div>
        </div>
        """
        
        # Import mailer here to avoid circular imports
        import sys
        import os
        sys.path.append(os.path.dirname(__file__))
        from mailer import send_email_with_fallback
        
        try:
            success, message = send_email_with_fallback(subject, email, body)
            if success:
                print(f"Password reset email sent to {email}: {message}")
                return True
            else:
                print(f"Failed to send password reset email: {message}")
                return False
        except Exception as e:
            print(f"Exception sending password reset email: {e}")
            return False

class RateLimiter:
    """Simple rate limiting implementation"""
    
    def __init__(self):
        self.attempts: Dict[str, List[datetime]] = {}
    
    def is_rate_limited(self, identifier: str, max_attempts: int = 5, window_minutes: int = 15) -> bool:
        """Check if identifier has exceeded rate limit."""
        now = datetime.now()
        window_start = now - timedelta(minutes=window_minutes)
        
        if identifier not in self.attempts:
            self.attempts[identifier] = []
        
        # Clean old attempts
        self.attempts[identifier] = [
            attempt for attempt in self.attempts[identifier] 
            if attempt > window_start
        ]
        
        # Check if limit exceeded
        if len(self.attempts[identifier]) >= max_attempts:
            return True
        
        # Add current attempt
        self.attempts[identifier].append(now)
        return False

class JWTManager:
    """Handles JWT token operations"""
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.PyJWTError:
            return None

# Initialize services
db = DatabaseManager()
email_service = EmailService()
rate_limiter = RateLimiter()
jwt_manager = JWTManager()
security = HTTPBearer()

# FastAPI app
app = FastAPI(title="ScholarAI Authentication API", version="1.0.0")

# Helper functions
def get_client_ip(request: Request) -> str:
    """Get client IP address"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host

def get_device_info(request: Request) -> str:
    """Get device information"""
    user_agent = request.headers.get("User-Agent", "Unknown")
    return user_agent[:200]  # Limit length

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    token = credentials.credentials
    payload = jwt_manager.verify_token(token)
    
    if payload is None or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload

# API Endpoints
@app.post("/auth/register")
async def register(user: UserRegister):
    """Register new user"""
    # Check rate limiting
    client_ip = "register_endpoint"  # In production, use actual IP
    if rate_limiter.is_rate_limited(client_ip, max_attempts=5, window_minutes=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many registration attempts. Please try again later."
        )
    
    # Validate input
    if db.user_exists(user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    if db.username_exists(user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create user
    password_hash = PasswordValidator.hash_password(user.password)
    user_id = db.create_user(user.username, user.email, password_hash)
    
    return {"message": "User registered successfully", "user_id": user_id}

@app.post("/auth/login")
async def login(user: UserLogin, request: Request, response: Response):
    """User login"""
    client_ip = get_client_ip(request)
    
    # Check rate limiting
    if rate_limiter.is_rate_limited(user.email, max_attempts=5, window_minutes=15):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )
    
    # Get user
    db_user = db.get_user_by_email(user.email)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if account is locked
    if db_user.get('locked_until') and db_user['locked_until'] > datetime.now():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is temporarily locked due to too many failed attempts"
        )
    
    # Verify password
    if not PasswordValidator.verify_password(user.password, db_user['password_hash']):
        # Update failed attempts
        # In production, implement account lockout logic here
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create tokens
    access_token = jwt_manager.create_access_token(
        data={"sub": str(db_user['id']), "username": db_user['username'], "email": db_user['email']}
    )
    
    # Create refresh token if remember me is checked
    if user.remember_me:
        device_info = get_device_info(request)
        refresh_token = db.create_refresh_token(
            str(db_user['id']), device_info, client_ip
        )
        
        # Set secure HTTP-only cookie for refresh token
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            httponly=True,
            secure=True,
            samesite="strict"
        )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(db_user['id']),
            "username": db_user['username'],
            "email": db_user['email']
        }
    }

@app.post("/auth/forgot-password")
async def forgot_password(request: ForgotPassword):
    """Initiate password reset"""
    client_ip = "forgot_password_endpoint"  # In production, use actual IP
    
    # Check rate limiting
    if rate_limiter.is_rate_limited(request.email, max_attempts=3, window_minutes=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many password reset attempts. Please try again later."
        )
    
    # Get user
    db_user = db.get_user_by_email(request.email)
    if not db_user:
        # Don't reveal if email exists or not for security
        return {"message": "If the email exists, a reset link has been sent"}
    
    # Create reset token
    reset_token = db.create_reset_token(str(db_user['id']))
    
    # Send email
    email_sent = email_service.send_password_reset_email(request.email, reset_token)
    
    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send reset email"
        )
    
    return {"message": "Password reset link sent to your email"}

@app.post("/auth/reset-password")
async def reset_password(request: ResetPassword):
    """Reset password using token"""
    # Validate token
    token_data = db.validate_reset_token(request.token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Check password reuse
    if db.check_password_reuse(token_data['user_id'], request.new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot reuse a previous password"
        )
    
    # Update password
    new_password_hash = PasswordValidator.hash_password(request.new_password)
    db.update_user_password(token_data['user_id'], new_password_hash)
    
    # Invalidate token
    db.invalidate_reset_token(request.token)
    
    # Revoke all refresh tokens for security
    db.revoke_all_refresh_tokens(token_data['user_id'])
    
    return {"message": "Password reset successfully"}

@app.post("/auth/refresh-token")
async def refresh_token(request: Request):
    """Refresh access token using refresh token"""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required"
        )
    
    # Validate refresh token
    token_data = db.validate_refresh_token(refresh_token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Create new access token
    access_token = jwt_manager.create_access_token(
        data={
            "sub": str(token_data['user_id']),
            "username": token_data['username'],
            "email": token_data['email']
        }
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.post("/auth/logout")
async def logout(response: Response):
    """Logout user (clear refresh token cookie)"""
    response.delete_cookie(key="refresh_token")
    return {"message": "Logged out successfully"}

@app.post("/auth/logout-all")
async def logout_all(current_user: dict = Depends(get_current_user)):
    """Logout from all devices"""
    user_id = current_user.get("sub")
    db.revoke_all_refresh_tokens(user_id)
    return {"message": "Logged out from all devices"}

@app.get("/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return {
        "user_id": current_user.get("sub"),
        "username": current_user.get("username"),
        "email": current_user.get("email")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
