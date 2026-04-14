"""
Example integration of authentication system with ScholarAI Streamlit app
Shows how to protect routes and integrate with existing functionality
"""

import streamlit as st
import os
from auth_frontend import AuthenticationUI, render_auth_page
from auth_system import app as auth_app
import uvicorn
import threading
import time

# Configuration
API_BASE_URL = os.getenv("AUTH_API_URL", "http://localhost:8000")

def start_auth_server():
    """Start the FastAPI authentication server in a separate thread"""
    def run_server():
        uvicorn.run(auth_app, host="0.0.0.0", port=8000, log_level="info")
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(2)  # Give server time to start

def check_authentication():
    """Check if user is authenticated"""
    return st.session_state.get('access_token') is not None

def require_auth():
    """Decorator to require authentication for a page"""
    if not check_authentication():
        st.error("🔐 Please login to access this page")
        st.markdown("### Login Required")
        st.markdown("You need to be logged in to use the ScholarAI literature review generator.")
        
        # Show login form
        auth_ui = AuthenticationUI(API_BASE_URL)
        auth_ui.render_login_form()
        return False
    return True

def main():
    """Main application with authentication integration"""
    # Start auth server if not already running
    if 'auth_server_started' not in st.session_state:
        start_auth_server()
        st.session_state.auth_server_started = True
    
    # Initialize auth UI
    auth_ui = AuthenticationUI(API_BASE_URL)
    
    # Page configuration
    st.set_page_config(
        page_title="ScholarAI — Literature Review Generator",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    # Handle authentication in sidebar
    with st.sidebar:
        st.markdown("# 🎓 ScholarAI")
        st.markdown("---")
        
        if auth_ui.is_authenticated():
            # Show user info and logout
            user = st.session_state.user
            st.markdown(f"### 👤 {user['username']}")
            st.caption(user['email'])
            
            if st.button("🚪 Logout", use_container_width=True):
                auth_ui.handle_logout()
            
            st.markdown("---")
            st.markdown("### 📚 Features")
            st.markdown("- 📄 Upload PDF/DOCX files")
            st.markdown("- 🔍 Extract and analyze content")
            st.markdown("- 📝 Generate literature reviews")
            st.markdown("- 📊 Export in multiple formats")
            
        else:
            # Show login/register form in sidebar
            tab1, tab2 = st.tabs(["Login", "Register"])
            
            with tab1:
                auth_ui.render_login_form()
            
            with tab2:
                auth_ui.render_registration_form()
            
            st.markdown("---")
            st.markdown("### 🔑 Forgot Password?")
            if st.button("Reset Password", use_container_width=True):
                st.session_state.show_forgot_password = True
            
            if st.session_state.get('show_forgot_password'):
                auth_ui.render_forgot_password_form()
                if st.button("← Back to Login"):
                    st.session_state.show_forgot_password = False
                    st.rerun()
    
    # Main content area
    if auth_ui.is_authenticated():
        # Your existing ScholarAI app content goes here
        render_main_app()
    else:
        # Show landing page for unauthenticated users
        render_landing_page()

def render_main_app():
    """Render the main ScholarAI application (protected)"""
    st.markdown("# 🎓 ScholarAI — Literature Review Generator")
    st.markdown("---")
    
    # Your existing app.py content would go here
    # For example:
    
    # File upload section
    st.markdown("## 📄 Upload Academic Papers")
    
    uploaded_files = st.file_uploader(
        "Choose PDF or DOCX files",
        type=['pdf', 'docx'],
        accept_multiple_files=True,
        help="Upload academic papers to generate literature reviews"
    )
    
    if uploaded_files:
        st.success(f"Uploaded {len(uploaded_files)} file(s)")
        
        # Process files (your existing logic)
        for file in uploaded_files:
            st.markdown(f"📎 **{file.name}**")
            
            # Add your file processing logic here
            # For example: extract_text, generate_review, etc.
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(f"📝 Generate Review", key=f"review_{file.name}"):
                    st.info("Generating literature review...")
                    # Your review generation logic
            
            with col2:
                if st.button(f"📄 Extract Text", key=f"extract_{file.name}"):
                    st.info("Extracting text...")
                    # Your text extraction logic
            
            with col3:
                if st.button(f"📊 Export", key=f"export_{file.name}"):
                    st.info("Preparing export...")
                    # Your export logic
    
    # Settings section
    with st.expander("⚙️ Settings"):
        st.markdown("### Review Settings")
        
        review_style = st.selectbox(
            "Review Style",
            ["Academic", "Summary", "Critical Analysis", "Systematic Review"]
        )
        
        citation_style = st.selectbox(
            "Citation Style",
            ["APA", "MLA", "Chicago", "Harvard", "IEEE"]
        )
        
        max_articles = st.slider(
            "Maximum Articles to Review",
            min_value=1,
            max_value=50,
            value=10
        )
        
        st.markdown("### Export Options")
        export_format = st.selectbox(
            "Export Format",
            ["PDF", "DOCX", "Markdown", "HTML"]
        )
        
        if st.button("💾 Save Settings"):
            st.success("Settings saved successfully!")

def render_landing_page():
    """Render landing page for unauthenticated users"""
    st.markdown("""
    # 🎓 ScholarAI — AI-Powered Literature Reviews
    
    Welcome to ScholarAI, your intelligent companion for academic literature reviews.
    
    ## ✨ Features
    
    - 📄 **Multi-format Support**: Upload PDF and DOCX files
    - 🔍 **Smart Extraction**: Automatically extract and analyze academic content
    - 📝 **AI-Powered Reviews**: Generate comprehensive literature reviews
    - 📊 **Multiple Export Formats**: Export as PDF, DOCX, Markdown, or HTML
    - 🎓 **Academic Standards**: Follow proper citation and formatting guidelines
    
    ## 🚀 Get Started
    
    Please **login** or **register** to access the full features of ScholarAI.
    
    ### Why Choose ScholarAI?
    
    - ⚡ **Fast Processing**: Get reviews in minutes, not hours
    - 🧠 **Intelligent Analysis**: Advanced AI understands academic content
    - 📚 **Comprehensive Coverage**: Analyze multiple papers simultaneously
    - 🔒 **Secure & Private**: Your data is encrypted and protected
    - 🎯 **Accurate Citations**: Automatic formatting in major citation styles
    
    ---
    
    *ScholarAI helps researchers, students, and academics save time while producing high-quality literature reviews.*
    """)

# Example of protecting specific routes
def protected_page_example():
    """Example of a protected page"""
    if not require_auth():
        return
    
    st.markdown("# 🔒 Protected Content")
    st.markdown("This page is only accessible to authenticated users.")
    
    # Your protected content here
    user = st.session_state.user
    st.markdown(f"Welcome, **{user['username']}**!")
    
    # Example of accessing user data
    st.json(st.session_state.user)

# Example middleware for API protection
def api_protected_endpoint():
    """Example of protecting API endpoints"""
    from fastapi import Depends, HTTPException, status
    from auth_system import get_current_user
    
    @app.get("/api/user/profile")
    async def get_user_profile(current_user: dict = Depends(get_current_user)):
        """Get user profile - protected endpoint"""
        return {
            "user_id": current_user.get("sub"),
            "username": current_user.get("username"),
            "email": current_user.get("email")
        }
    
    @app.post("/api/review/generate")
    async def generate_review_endpoint(
        request: dict,
        current_user: dict = Depends(get_current_user)
    ):
        """Generate literature review - protected endpoint"""
        # Your review generation logic here
        return {"message": "Review generated successfully"}

if __name__ == "__main__":
    main()
