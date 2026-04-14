"""
Frontend Authentication Components for ScholarAI Streamlit App
Provides login, registration, password reset UI with real-time validation
"""

import streamlit as st
import requests
import re
from typing import Dict, List, Tuple
import time

class AuthenticationUI:
    """Handles authentication UI components"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.setup_session_state()
    
    def setup_session_state(self):
        """Initialize session state variables"""
        if 'access_token' not in st.session_state:
            st.session_state.access_token = None
        if 'user' not in st.session_state:
            st.session_state.user = None
        if 'show_password' not in st.session_state:
            st.session_state.show_password = {}
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return st.session_state.access_token is not None
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API calls"""
        if st.session_state.access_token:
            return {"Authorization": f"Bearer {st.session_state.access_token}"}
        return {}
    
    def render_login_form(self):
        """Render login form with remember me option"""
        st.markdown("### 🔐 Login to ScholarAI")
        
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="Enter your email address")
            password = st.text_input(
                "Password", 
                type="password" if not st.session_state.show_password.get('login', False) else "default",
                placeholder="Enter your password"
            )
            
            col1, col2 = st.columns([1, 3])
            with col1:
                show_password = st.checkbox("Show password")
            with col2:
                remember_me = st.checkbox("Remember me", help="Keep me logged in for 30 days")
            
            if show_password != st.session_state.show_password.get('login', False):
                st.session_state.show_password['login'] = show_password
                st.rerun()
            
            submitted = st.form_submit_button("Login", use_container_width=True)
            
            if submitted:
                self.handle_login(email, password, remember_me)
    
    def render_registration_form(self):
        """Render registration form with real-time validation"""
        st.markdown("### 📝 Create Account")
        
        with st.form("registration_form"):
            username = st.text_input("Username", placeholder="Choose a username")
            email = st.text_input("Email", placeholder="Enter your email address")
            
            # Password input with strength indicator
            password = st.text_input(
                "Password", 
                type="password" if not st.session_state.show_password.get('register', False) else "default",
                placeholder="Create a strong password",
                help="Must contain at least 8 characters with uppercase, lowercase, number, and special character"
            )
            
            show_password = st.checkbox("Show password")
            if show_password != st.session_state.show_password.get('register', False):
                st.session_state.show_password['register'] = show_password
                st.rerun()
            
            # Real-time password strength indicator
            if password:
                self.render_password_strength_indicator(password)
            
            confirm_password = st.text_input(
                "Confirm Password", 
                type="password",
                placeholder="Confirm your password"
            )
            
            # Terms and conditions
            agree_terms = st.checkbox("I agree to the Terms of Service and Privacy Policy")
            
            submitted = st.form_submit_button("Create Account", use_container_width=True)
            
            if submitted:
                self.handle_registration(username, email, password, confirm_password, agree_terms)
    
    def render_password_strength_indicator(self, password: str):
        """Render password strength indicator with visual feedback"""
        strength_info = self.check_password_strength(password)
        
        # Strength bar
        strength_percentage = (strength_info['score'] / 8) * 100
        
        st.markdown("#### Password Strength")
        
        # Color-coded strength bar
        if strength_info['strength']['level'] == 'weak':
            bar_color = "🔴"
        elif strength_info['strength']['level'] == 'fair':
            bar_color = "🟡"
        elif strength_info['strength']['level'] == 'good':
            bar_color = "🔵"
        else:
            bar_color = "🟢"
        
        st.progress(strength_percentage / 100)
        st.markdown(f"{bar_color} **{strength_info['strength']['text'].upper()}** ({strength_info['score']}/8)")
        
        # Requirements checklist
        st.markdown("**Requirements:**")
        for req_name, req_info in strength_info['requirements'].items():
            icon = "✅" if req_info['passed'] else "❌"
            st.markdown(f"{icon} {req_info['message']}")
    
    def render_forgot_password_form(self):
        """Render forgot password form"""
        st.markdown("### 🔑 Reset Password")
        
        with st.form("forgot_password_form"):
            email = st.text_input("Email", placeholder="Enter your registered email address")
            submitted = st.form_submit_button("Send Reset Link", use_container_width=True)
            
            if submitted:
                self.handle_forgot_password(email)
    
    def render_reset_password_form(self, token: str):
        """Render reset password form"""
        st.markdown("### 🔐 Set New Password")
        
        with st.form("reset_password_form"):
            new_password = st.text_input(
                "New Password", 
                type="password" if not st.session_state.show_password.get('reset', False) else "default",
                placeholder="Enter your new password"
            )
            
            show_password = st.checkbox("Show password")
            if show_password != st.session_state.show_password.get('reset', False):
                st.session_state.show_password['reset'] = show_password
                st.rerun()
            
            if new_password:
                self.render_password_strength_indicator(new_password)
            
            confirm_password = st.text_input(
                "Confirm New Password", 
                type="password",
                placeholder="Confirm your new password"
            )
            
            submitted = st.form_submit_button("Reset Password", use_container_width=True)
            
            if submitted:
                self.handle_reset_password(token, new_password, confirm_password)
    
    def check_password_strength(self, password: str) -> Dict:
        """Check password strength and return detailed information"""
        requirements = {
            'length': {
                'regex': r'.{8,}',
                'message': 'At least 8 characters long',
                'passed': False
            },
            'uppercase': {
                'regex': r'[A-Z]',
                'message': 'Contains uppercase letter',
                'passed': False
            },
            'lowercase': {
                'regex': r'[a-z]',
                'message': 'Contains lowercase letter',
                'passed': False
            },
            'number': {
                'regex': r'\d',
                'message': 'Contains number',
                'passed': False
            },
            'special': {
                'regex': r'[!@#$%^&*()_+\-=\[\]{};:"\\|,.<>\/?]',
                'message': 'Contains special character',
                'passed': False
            }
        }
        
        score = 0
        
        # Check each requirement
        for req_name, req_info in requirements.items():
            if re.search(req_info['regex'], password):
                requirements[req_name]['passed'] = True
                score += 1
        
        # Additional strength checks
        if len(password) >= 12:
            score += 1
        
        if not re.search(r'(.)\1{2,}', password):  # No 3+ repeated chars
            score += 1
        
        if not re.search(r'^(.)\1+$', password):  # Not all same char
            score += 1
        
        # Determine strength level
        if score <= 2:
            strength = {'level': 'weak', 'color': '#ef4444', 'text': 'Weak'}
        elif score <= 4:
            strength = {'level': 'fair', 'color': '#f59e0b', 'text': 'Fair'}
        elif score <= 6:
            strength = {'level': 'good', 'color': '#3b82f6', 'text': 'Good'}
        else:
            strength = {'level': 'strong', 'color': '#10b981', 'text': 'Strong'}
        
        return {
            'requirements': requirements,
            'score': score,
            'strength': strength
        }
    
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_username(self, username: str) -> Tuple[bool, str]:
        """Validate username format"""
        if len(username) < 3:
            return False, "Username must be at least 3 characters long"
        if len(username) > 50:
            return False, "Username must not exceed 50 characters"
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "Username can only contain letters, numbers, and underscores"
        return True, ""
    
    def handle_login(self, email: str, password: str, remember_me: bool):
        """Handle login submission"""
        if not email or not password:
            st.error("Please fill in all fields")
            return
        
        if not self.validate_email(email):
            st.error("Please enter a valid email address")
            return
        
        try:
            with st.spinner("Logging in..."):
                response = requests.post(
                    f"{self.api_base_url}/auth/login",
                    json={
                        "email": email,
                        "password": password,
                        "remember_me": remember_me
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.access_token = data['access_token']
                    st.session_state.user = data['user']
                    st.success("Login successful!")
                    time.sleep(1)
                    st.rerun()
                else:
                    error_data = response.json() if response.content else {}
                    st.error(error_data.get('detail', 'Login failed'))
        
        except requests.exceptions.RequestException as e:
            st.error(f"Connection error: {str(e)}")
    
    def handle_registration(self, username: str, email: str, password: str, 
                          confirm_password: str, agree_terms: bool):
        """Handle registration submission"""
        # Validation
        if not all([username, email, password, confirm_password]):
            st.error("Please fill in all fields")
            return
        
        # Validate username
        username_valid, username_error = self.validate_username(username)
        if not username_valid:
            st.error(username_error)
            return
        
        # Validate email
        if not self.validate_email(email):
            st.error("Please enter a valid email address")
            return
        
        # Validate password
        password_valid, password_errors = self.validate_password_strength(password)
        if not password_valid:
            st.error("Password requirements not met:")
            for error in password_errors:
                st.error(f"• {error}")
            return
        
        # Check password confirmation
        if password != confirm_password:
            st.error("Passwords do not match")
            return
        
        # Check terms agreement
        if not agree_terms:
            st.error("Please agree to the Terms of Service and Privacy Policy")
            return
        
        try:
            with st.spinner("Creating account..."):
                response = requests.post(
                    f"{self.api_base_url}/auth/register",
                    json={
                        "username": username,
                        "email": email,
                        "password": password
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    st.success("Account created successfully! Please log in.")
                    time.sleep(2)
                    st.rerun()
                else:
                    error_data = response.json() if response.content else {}
                    st.error(error_data.get('detail', 'Registration failed'))
        
        except requests.exceptions.RequestException as e:
            st.error(f"Connection error: {str(e)}")
    
    def handle_forgot_password(self, email: str):
        """Handle forgot password submission"""
        if not email:
            st.error("Please enter your email address")
            return
        
        if not self.validate_email(email):
            st.error("Please enter a valid email address")
            return
        
        try:
            with st.spinner("Sending reset link..."):
                response = requests.post(
                    f"{self.api_base_url}/auth/forgot-password",
                    json={"email": email},
                    timeout=10
                )
                
                if response.status_code == 200:
                    st.success("If the email exists, a reset link has been sent to your inbox.")
                else:
                    error_data = response.json() if response.content else {}
                    st.error(error_data.get('detail', 'Failed to send reset link'))
        
        except requests.exceptions.RequestException as e:
            st.error(f"Connection error: {str(e)}")
    
    def handle_reset_password(self, token: str, new_password: str, confirm_password: str):
        """Handle password reset submission"""
        if not new_password or not confirm_password:
            st.error("Please fill in all fields")
            return
        
        # Validate password
        password_valid, password_errors = self.validate_password_strength(new_password)
        if not password_valid:
            st.error("Password requirements not met:")
            for error in password_errors:
                st.error(f"• {error}")
            return
        
        # Check password confirmation
        if new_password != confirm_password:
            st.error("Passwords do not match")
            return
        
        try:
            with st.spinner("Resetting password..."):
                response = requests.post(
                    f"{self.api_base_url}/auth/reset-password",
                    json={
                        "token": token,
                        "new_password": new_password
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    st.success("Password reset successfully! Please log in with your new password.")
                    time.sleep(2)
                    st.rerun()
                else:
                    error_data = response.json() if response.content else {}
                    st.error(error_data.get('detail', 'Failed to reset password'))
        
        except requests.exceptions.RequestException as e:
            st.error(f"Connection error: {str(e)}")
    
    def validate_password_strength(self, password: str) -> Tuple[bool, List[str]]:
        """Validate password and return errors if any"""
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
    
    def render_user_menu(self):
        """Render user menu when logged in"""
        if st.session_state.user:
            user = st.session_state.user
            
            with st.sidebar:
                st.markdown("---")
                st.markdown(f"### 👤 {user['username']}")
                st.caption(user['email'])
                
                if st.button("🚪 Logout", use_container_width=True):
                    self.handle_logout()
    
    def handle_logout(self):
        """Handle logout"""
        try:
            # Call logout API endpoint
            response = requests.post(
                f"{self.api_base_url}/auth/logout",
                headers=self.get_auth_headers(),
                timeout=10
            )
        except:
            pass  # Continue with local logout even if API call fails
        
        # Clear session state
        st.session_state.access_token = None
        st.session_state.user = None
        st.success("Logged out successfully!")
        time.sleep(1)
        st.rerun()

def render_auth_page():
    """Render main authentication page"""
    # Initialize auth UI
    auth_ui = AuthenticationUI()
    
    # Check if user is already logged in
    if auth_ui.is_authenticated():
        st.success(f"Welcome back, {st.session_state.user['username']}! 🎓")
        st.markdown("You are now logged in to ScholarAI.")
        
        # Render user menu
        auth_ui.render_user_menu()
        return
    
    # Tab-based authentication interface
    tab1, tab2, tab3 = st.tabs(["🔐 Login", "📝 Register", "🔑 Forgot Password"])
    
    with tab1:
        auth_ui.render_login_form()
    
    with tab2:
        auth_ui.render_registration_form()
    
    with tab3:
        auth_ui.render_forgot_password_form()

def render_reset_page(token: str):
    """Render password reset page"""
    auth_ui = AuthenticationUI()
    auth_ui.render_reset_password_form(token)

# Usage examples:
# 
# # In your main Streamlit app:
# if st.session_state.get('show_reset_page') and 'reset_token' in st.query_params:
#     render_reset_page(st.query_params['reset_token'])
# else:
#     render_auth_page()
#
# # Protect authenticated routes:
# if not auth_ui.is_authenticated():
#     st.error("Please login to access this page")
#     render_auth_page()
#     st.stop()
