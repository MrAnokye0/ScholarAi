"""
ScholarAI — Academic Literature Review Generator
Main Streamlit application entry point.
"""

import os
import io
import re
import json
from pathlib import Path
import time
from datetime import datetime
from urllib import request as urlrequest
from urllib import error as urlerror

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
import secrets
from pathlib import Path

# Load .env from the same directory as this script
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# ── Page config (must be first Streamlit call) ─────────────────────
st.set_page_config(
    page_title="ScholarAI — Literature Review Generator",
    page_icon="≡ƒÄô",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Imports (after page config) ────────────────────────────────────
from home import render_home
from extractor import extract_text, truncate_text
from reviewer  import generate_review
from exporter  import generate_pdf, generate_docx
from reference_formatter import STYLES, format_all_references
from utils import (new_session_id, format_bytes, estimate_read_time,
                   now_str, validate_api_key, test_api_connection, slugify)
# Use PostgreSQL-compatible database adapter (auto-detects PostgreSQL or SQLite)
import database_postgres as db
import mailer


# ── Initialise DB ──────────────────────────────────────────────────
db.init_db()

# ── Pricing Component ──────────────────────────────────────────────
def render_paywall():
    # ── Overlay background ──
    html_paywall = r"""<style>@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&display=swap'); body { margin: 0; background: transparent; font-family: sans-serif; color: white; }</style><div style="width:100%;min-height:100vh;background:rgba(2,6,23,0.9);backdrop-filter:blur(24px);-webkit-backdrop-filter:blur(24px);display:flex;justify-content:center;align-items:center;padding:40px 0;"><div style="width:100%;max-width:1100px;padding:20px;"><div style="text-align:center;margin-bottom:48px;"><h1 style="font-family:'Syne',sans-serif;color:white;font-size:3rem;margin-bottom:12px;">ScholarAI Platinum</h1><p style="color:#94a3b8;font-size:1.2rem;">You've hit your free limit. Upgrade to continue.</p></div><div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:32px;"><div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);border-radius:24px;text-align:center;padding:48px 32px;"><div style="font-size:0.75rem;font-weight:800;color:#4361EE;margin-bottom:20px;letter-spacing:0.1em;">WEEKLY</div><div style="font-size:3rem;font-weight:800;color:white;margin-bottom:8px;">GHS 10</div><div style="text-align:left;color:white;font-size:0.9rem;line-height:1.8;margin-top:20px;">✅ Unlimited generations<br>✅ Up to 15 articles/review</div></div><div style="background:rgba(67,97,238,0.1);border:2px solid #4361EE;border-radius:24px;text-align:center;padding:48px 32px;transform:scale(1.05);"><div style="font-size:0.75rem;font-weight:800;color:#4361EE;margin-bottom:20px;letter-spacing:0.1em;">MONTHLY</div><div style="font-size:3.5rem;font-weight:800;color:white;margin-bottom:8px;">GHS 30</div><div style="text-align:left;color:white;font-size:0.9rem;line-height:1.8;margin-top:20px;">✅ Priority process<br>✅ Best Value</div></div><div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);border-radius:24px;text-align:center;padding:48px 32px;"><div style="font-size:0.75rem;font-weight:800;color:#4361EE;margin-bottom:20px;letter-spacing:0.1em;">YEARLY</div><div style="font-size:3rem;font-weight:800;color:white;margin-bottom:8px;">GHS 300</div><div style="text-align:left;color:white;font-size:0.9rem;line-height:1.8;margin-top:20px;">✅ Master access<br>✅ Save 20%</div></div></div></div></div>"""
    components.html(html_paywall, height=800, scrolling=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("≡ƒÜÇ Buy Weekly", key="buy_w", use_container_width=True):
            db.update_user_tier(st.session_state.auth_username, "premium")
            st.session_state.user_tier = "premium"
            st.session_state.show_paywall = False
            st.success("✅ WELCOME TO SCHOLARAI PLATINUM!")
            st.rerun()
    with col2:
        if st.button("✨ Buy Monthly (GHS 30)", key="buy_m", type="primary", use_container_width=True):
            db.update_user_tier(st.session_state.auth_username, "premium")
            st.session_state.user_tier = "premium"
            st.session_state.show_paywall = False
            st.success("✅ WELCOME TO SCHOLARAI PLATINUM!")
            st.rerun()
    with col3:
        if st.button("≡ƒææ Buy Yearly", key="buy_y", use_container_width=True):
            db.update_user_tier(st.session_state.auth_username, "premium")
            st.session_state.user_tier = "premium"
            st.session_state.show_paywall = False
            st.success("✅ WELCOME TO SCHOLARAI PLATINUM!")
            st.rerun()
    
    if st.button("❌ Close Pricing", use_container_width=True):
        st.session_state.show_paywall = False
        st.rerun()


# ── Load CSS ───────────────────────────────────────────────────────
def load_css():
    css_path = Path(__file__).parent / "assets" / "style.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

load_css()


# ── Session state initialisation ───────────────────────────────────
def init_session():
    defaults = {
        "session_id":         new_session_id(),
        "api_key":            os.getenv("OPENAI_API_KEY", ""),
        "gemini_api_key":     os.getenv("GOOGLE_API_KEY", ""),
        "ai_provider":        "google", # Default to free Gemini
        "api_key_valid":      False,
        "citation_style":     "APA 7th",
        "topic":              "",
        "articles":           [],      # [{filename, text, info, metadata}]
        "result":             None,    # generated review dict
        "review_id":          None,
        "generating":         False,
        "history":            [],      # last 3 results
        "error":              None,
        "user_authenticated": False,
        "auth_mode":          "login", # login, signup, verify, forgot_pass
        "auth_username":      None,
        "auth_email":         None,
        "user_tier":          "free",
        "user_credits":       0,
        "show_paywall":       False,
        "allow_openai_fallback": False,
        "backend_api_url":    os.getenv("PRIVATE_API_URL", ""),
        "backend_api_token":  os.getenv("PRIVATE_API_TOKEN", ""),
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Register session in DB once
    if "db_registered" not in st.session_state:
        db.upsert_session(st.session_state.session_id)
        st.session_state.db_registered = True

# ── Persistence Logic ──────────────────────────────────────────────
def render_remember_me_js(action: str, token: str = ""):
    """JS Bridge to handle localStorage since Streamlit is stateless."""
    if action == "save" and token:
        js_code = f"""
            <script>
                window.parent.localStorage.setItem('scholarai_remember_token', '{token}');
            </script>
        """
        components.html(js_code, height=0)
    elif action == "clear":
        js_code = """
            <script>
                window.parent.localStorage.removeItem('scholarai_remember_token');
            </script>
        """
        components.html(js_code, height=0)
    elif action == "check":
        js_code = """
            <script>
                const token = localStorage.getItem('scholarai_remember_token');
                const urlParams = new URLSearchParams(window.parent.location.search);
                const lockKey = 'scholarai_remember_redirecting';
                const isRedirecting = sessionStorage.getItem(lockKey) === '1';
                if (token && !urlParams.has('remember_token') && !isRedirecting) {
                    sessionStorage.setItem(lockKey, '1');
                    urlParams.set('remember_token', token);
                    window.parent.location.search = urlParams.toString();
                } else if (urlParams.has('remember_token')) {
                    // Landing after redirect, clear lock to allow future resumes.
                    sessionStorage.removeItem(lockKey);
                }
            </script>
        """
        components.html(js_code, height=0)

# ── Session state initialisation ───────────────────────────────────
def init_session():
    defaults = {
        "session_id":         new_session_id(),
        "api_key":            os.getenv("OPENAI_API_KEY", ""),
        "gemini_api_key":     os.getenv("GOOGLE_API_KEY", ""),
        "ai_provider":        "google", 
        "api_key_valid":      False,
        "citation_style":     "APA 7th",
        "topic":              "",
        "articles":           [],
        "result":             None,
        "review_id":          None,
        "generating":         False,
        "history":            [],
        "error":              None,
        "user_authenticated": False,
        "username":           None,
        "auth_username":      None,
        "auth_email":         None,
        "auth_mode":          "login",
        "reset_step":         None,
        "user_tier":          "free",
        "user_credits":       0,
        "show_paywall":       False,
        "allow_openai_fallback": False,
        "backend_api_url":    os.getenv("PRIVATE_API_URL", ""),
        "backend_api_token":  os.getenv("PRIVATE_API_TOKEN", ""),
        "show_home":          True,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Auto-Login Logic (from query params)
    if not st.session_state.user_authenticated:
        r_token = st.query_params.get("remember_token")
        if r_token:
            user = db.get_user_by_remember_token(r_token)
            if user:
                st.session_state.user_authenticated = True
                st.session_state.username = user["username"]
                st.session_state.auth_username = user["username"]
                st.session_state.auth_email = user["email"]
                st.session_state.user_tier = user.get("tier", "free")
                st.query_params.clear()
            else:
                render_remember_me_js("clear")
        else:
            render_remember_me_js("check")

    if "db_registered" not in st.session_state:
        db.upsert_session(st.session_state.session_id)
        st.session_state.db_registered = True

init_session()

# ── Early query param handler for OTP verification ─────────────────────────
_early_action = st.query_params.get("pr_action", "")
# If auth=1 is in URL, skip home page
if st.query_params.get("auth") == "1":
    st.session_state.show_home = False
if _early_action:
    _early_otp = st.query_params.get("pr_otp", "").strip()
    st.query_params.clear()
    if _early_action == "verify":
        _em = st.session_state.get("auth_email", "")
        _user = db.get_user_by_email(_em) if _em else None
        _stored = _user.get("reset_token", "") if _user else ""
        if _user and _stored and _early_otp == _stored:
            st.session_state.reset_step = "password"
            st.session_state.pr_error = ""
        else:
            st.session_state.pr_error = "Invalid code. Please try again."
    elif _early_action == "back":
        st.session_state.reset_step = "email"
        st.session_state.pr_error = ""
    elif _early_action == "resend":
        _em = st.session_state.get("auth_email", "")
        if _em:
            _rc = mailer.generate_6_digit_code()
            db.update_reset_token(_em, _rc)
            # Send synchronously for Streamlit Cloud
            mailer.send_password_reset(_em, _rc)
            st.session_state.last_code_sent_at = time.time()
            st.session_state.pr_error = ""
    st.rerun()


def render_generation_avatar():
    """Animated waiting card shown while synthesis is running."""
    holder = st.empty()
    holder.markdown(
        """
        <style>
        .gen-wait-card {
            border: 1px solid rgba(67,97,238,0.28);
            background: linear-gradient(135deg, rgba(67,97,238,0.10), rgba(114,9,183,0.08));
            border-radius: 14px;
            padding: 14px 16px;
            margin: 10px 0 14px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
        }
        .gen-wait-left { display: flex; align-items: center; gap: 10px; color: #dbe4ff; }
        .gen-avatar {
            width: 34px; height: 34px; border-radius: 50%;
            display: inline-flex; align-items: center; justify-content: center;
            background: rgba(67,97,238,0.25);
            animation: pulseAvatar 1.4s ease-in-out infinite;
        }
        .gen-dots span {
            display: inline-block; width: 6px; height: 6px; border-radius: 50%;
            background: #8fb1ff; margin-left: 4px; opacity: 0.35;
            animation: bounceDot 1s infinite;
        }
        .gen-dots span:nth-child(2) { animation-delay: 0.15s; }
        .gen-dots span:nth-child(3) { animation-delay: 0.30s; }
        @keyframes pulseAvatar {
            0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(67,97,238,0.45); }
            70% { transform: scale(1.06); box-shadow: 0 0 0 10px rgba(67,97,238,0); }
            100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(67,97,238,0); }
        }
        @keyframes bounceDot {
            0%, 80%, 100% { transform: translateY(0); opacity: 0.35; }
            40% { transform: translateY(-4px); opacity: 1; }
        }
        </style>
        <div class="gen-wait-card">
          <div class="gen-wait-left">
            <div class="gen-avatar"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#8fb1ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg></div>
            <div><strong>ScholarAI is building your review</strong><br/><span style="font-size:0.82rem;opacity:0.9;">Reading sources, organizing themes, and drafting citations.</span></div>
          </div>
          <div class="gen-dots" aria-label="loading">
            <span></span><span></span><span></span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    return holder


def generate_review_via_private_api(
    topic: str,
    articles: list[dict],
    citation_style: str,
    provider: str,
) -> dict:
    """Call self-hosted backend so provider keys stay server-side."""
    backend_url = (st.session_state.get("backend_api_url") or "").strip()
    if not backend_url:
        raise ValueError("Private API URL is not configured.")

    payload = {
        "topic": topic,
        "articles": [
            {"filename": a.get("filename", "article.txt"), "text": a.get("text", "")}
            for a in articles
        ],
        "citation_style": citation_style,
        "provider": provider,
    }
    body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    token = (st.session_state.get("backend_api_token") or "").strip()
    if token:
        headers["X-API-Token"] = token

    req = urlrequest.Request(
        backend_url.rstrip("/") + "/api/generate-review",
        data=body,
        headers=headers,
        method="POST",
    )
    try:
        with urlrequest.urlopen(req, timeout=180) as resp:
            raw = resp.read().decode("utf-8")
    except urlerror.HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore")
        raise Exception(f"Private API error {e.code}: {detail}")
    except Exception as e:
        raise Exception(f"Private API request failed: {e}")

    parsed = json.loads(raw)
    if not parsed.get("ok"):
        raise Exception(parsed.get("error", "Unknown private API error"))
    return parsed.get("review", {})

# ── Error Display ──────────────────────────────────────────────────
if st.session_state.error:
    st.error(f"⚠️ {st.session_state.error}")
    if st.button("Clear Error"):
        st.session_state.error = None
        st.rerun()

# ══════════════════════════════════════════════════════════════════
#  HOME PAGE GATE
# ══════════════════════════════════════════════════════════════════
# ?go=app skips home and goes straight to auth
if st.query_params.get('go') == 'app':
    st.query_params.clear()
    st.session_state.show_home = False

# Show home page if not authenticated and show_home is True
if st.session_state.get('show_home', True) and not st.session_state.user_authenticated:
    render_home()
    st.stop()

if not st.session_state.user_authenticated:

    # ── Terms / Privacy pages ──────────────────────────────────────
    _page = st.query_params.get("page")
    if _page in ("terms", "privacy"):
        st.markdown("""<style>
        .stApp{background:#0B0F19!important}
        [data-testid="stSidebar"],[data-testid="stHeader"],[data-testid="stToolbar"],
        .stMainHeader,footer,#MainMenu{display:none!important}
        .main .block-container{max-width:720px!important;margin:0 auto!important;padding:3rem 1.5rem!important}
        p,li,h1,h2,h3,h4{color:#E2E8F0!important}
        </style>""", unsafe_allow_html=True)
        if _page == "terms":
            st.markdown("""## Terms of Use
**Last Updated:** April 16, 2026

By accessing ScholarAI you agree to use it ethically for academic research,
provide accurate information, and review all AI-generated content before
submission. You retain rights to uploaded content. The service is provided
"as is" without warranties.""")
        else:
            st.markdown("""## Privacy Policy
**Last Updated:** April 16, 2026

We collect your email address for authentication only. Documents are
processed temporarily and never stored permanently. We do not sell or share
your data. Authentication is OTP-based — no passwords stored.""")
        if st.button("Back", use_container_width=True):
            st.query_params.clear()
            st.rerun()
        st.stop()

    if st.query_params.get("auth_back") == "1":
        st.query_params.clear()
        st.session_state.show_home = True
        st.rerun()

    #  Hide Streamlit chrome, set dark background 
    st.markdown("""<style>
    .stApp{background:#0B0F1A!important}
    [data-testid="stSidebar"],[data-testid="stHeader"],[data-testid="stToolbar"],
    .stMainHeader,footer,#MainMenu,[data-testid="stDecoration"]{display:none!important}
    .main .block-container{padding:0!important;max-width:100%!important;margin:0!important}
    div[data-testid="stTextInput"] input{
        background:rgba(255,255,255,.06)!important;
        border:1.5px solid rgba(255,255,255,.12)!important;
        border-radius:10px!important;color:#F1F5F9!important;
        font-size:.95rem!important;padding:13px 16px!important;
        caret-color:#818cf8!important;
    }
    div[data-testid="stTextInput"] input:focus{
        border-color:#4361EE!important;
        box-shadow:0 0 0 3px rgba(67,97,238,.22)!important;
        background:rgba(67,97,238,.08)!important;
    }
    div[data-testid="stTextInput"] input::placeholder{color:rgba(148,163,184,.5)!important}
    div[data-testid="stTextInput"] label{
        color:#94A3B8!important;font-size:.78rem!important;
        font-weight:700!important;letter-spacing:.06em!important;text-transform:uppercase!important;
    }
    div.stButton>button[kind="primary"]{
        background:linear-gradient(135deg,#4361EE,#7209B7)!important;
        border:none!important;border-radius:10px!important;color:#fff!important;
        font-weight:700!important;font-size:.95rem!important;padding:13px 0!important;
        box-shadow:0 4px 20px rgba(67,97,238,.4)!important;
        transition:transform .15s,box-shadow .15s!important;
    }
    div.stButton>button[kind="primary"]:hover{
        transform:translateY(-1px)!important;
        box-shadow:0 8px 28px rgba(67,97,238,.55)!important;
    }
    div.stButton>button{
        background:rgba(255,255,255,.05)!important;
        border:1.5px solid rgba(255,255,255,.1)!important;
        border-radius:10px!important;color:#94A3B8!important;
        font-weight:500!important;padding:10px 0!important;
        transition:background .2s,border-color .2s,color .2s!important;
    }
    div.stButton>button:hover{
        background:rgba(255,255,255,.09)!important;
        border-color:rgba(255,255,255,.22)!important;color:#E2E8F0!important;
    }
    p,label,.stMarkdown{color:#E2E8F0!important}
    div[data-testid="stAlert"]{
        background:rgba(239,68,68,.12)!important;
        border:1px solid rgba(239,68,68,.3)!important;
        border-radius:10px!important;
    }
    /* Modal overlay */
    .sai-modal-overlay{
        display:none;position:fixed;inset:0;z-index:9999;
        background:rgba(0,0,0,.75);backdrop-filter:blur(6px);
        align-items:center;justify-content:center;padding:20px;
        animation:fadeIn .2s ease;
    }
    .sai-modal-overlay.open{display:flex}
    .sai-modal{
        background:#0F172A;border:1px solid rgba(255,255,255,.1);
        border-radius:20px;width:100%;max-width:640px;max-height:80vh;
        overflow:hidden;display:flex;flex-direction:column;
        box-shadow:0 32px 64px rgba(0,0,0,.6);
        animation:slideUp .25s cubic-bezier(.16,1,.3,1);
    }
    .sai-modal-header{
        display:flex;align-items:center;justify-content:space-between;
        padding:20px 24px;border-bottom:1px solid rgba(255,255,255,.08);
        flex-shrink:0;
    }
    .sai-modal-title{color:#F1F5F9;font-size:1.1rem;font-weight:700;margin:0}
    .sai-modal-close{
        width:32px;height:32px;border-radius:8px;border:none;cursor:pointer;
        background:rgba(255,255,255,.06);color:#94A3B8;font-size:1.1rem;
        display:flex;align-items:center;justify-content:center;
        transition:background .2s,color .2s;
    }
    .sai-modal-close:hover{background:rgba(255,255,255,.12);color:#F1F5F9}
    .sai-modal-body{
        padding:24px;overflow-y:auto;flex:1;
        scrollbar-width:thin;scrollbar-color:rgba(255,255,255,.15) transparent;
    }
    .sai-modal-body h3{color:#818cf8;font-size:.85rem;font-weight:700;
        letter-spacing:.06em;text-transform:uppercase;margin:20px 0 8px}
    .sai-modal-body h3:first-child{margin-top:0}
    .sai-modal-body p{color:#94A3B8;font-size:.88rem;line-height:1.7;margin:0 0 12px}
    .sai-modal-body ul{color:#94A3B8;font-size:.88rem;line-height:1.7;
        margin:0 0 12px;padding-left:18px}
    .sai-modal-body li{margin-bottom:4px}
    @keyframes fadeIn{from{opacity:0}to{opacity:1}}
    @keyframes slideUp{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:none}}
    </style>""", unsafe_allow_html=True)

    #  Terms modal 
    st.markdown("""
    <div class="sai-modal-overlay" id="modal-terms">
      <div class="sai-modal">
        <div class="sai-modal-header">
          <p class="sai-modal-title">Terms of Use</p>
          <button class="sai-modal-close" onclick="document.getElementById('modal-terms').classList.remove('open')">&#x2715;</button>
        </div>
        <div class="sai-modal-body">
          <p><strong style="color:#E2E8F0">Last Updated: April 16, 2026</strong></p>
          <h3>1. Acceptance</h3>
          <p>By accessing ScholarAI you agree to these Terms. If you disagree, do not use the service.</p>
          <h3>2. Use of Service</h3>
          <ul>
            <li>ScholarAI is for academic research and literature review purposes only.</li>
            <li>You must review and verify all AI-generated content before academic submission.</li>
            <li>You may not use the service for any illegal or unauthorized purpose.</li>
            <li>You are responsible for maintaining the security of your account.</li>
          </ul>
          <h3>3. Intellectual Property</h3>
          <p>You retain all rights to content you upload. ScholarAI retains rights to the platform and its technology. Generated content is provided for your personal academic use.</p>
          <h3>4. Disclaimer</h3>
          <p>AI-generated content may contain errors. ScholarAI is not responsible for academic consequences arising from use of generated content. The service is provided "as is" without warranties of any kind.</p>
          <h3>5. Limitation of Liability</h3>
          <p>ScholarAI shall not be liable for any indirect, incidental, special, or consequential damages arising from your use of the service.</p>
          <h3>6. Changes</h3>
          <p>We reserve the right to modify these terms at any time. Continued use of the service constitutes acceptance of updated terms.</p>
          <h3>7. Contact</h3>
          <p>For questions about these terms, contact us through the application.</p>
        </div>
      </div>
    </div>

    <div class="sai-modal-overlay" id="modal-privacy">
      <div class="sai-modal">
        <div class="sai-modal-header">
          <p class="sai-modal-title">Privacy Policy</p>
          <button class="sai-modal-close" onclick="document.getElementById('modal-privacy').classList.remove('open')">&#x2715;</button>
        </div>
        <div class="sai-modal-body">
          <p><strong style="color:#E2E8F0">Last Updated: April 16, 2026</strong></p>
          <h3>1. What We Collect</h3>
          <ul>
            <li><strong style="color:#E2E8F0">Email address</strong>  used only for OTP authentication.</li>
            <li><strong style="color:#E2E8F0">Usage data</strong>  documents processed temporarily, generation history.</li>
            <li><strong style="color:#E2E8F0">Technical data</strong>  browser type, session identifiers.</li>
          </ul>
          <h3>2. How We Use It</h3>
          <ul>
            <li>To authenticate you via one-time codes.</li>
            <li>To provide and improve the literature review service.</li>
            <li>To ensure security and prevent abuse.</li>
          </ul>
          <h3>3. Data Storage</h3>
          <p>Uploaded documents are processed in memory and never stored permanently. Your email and session data are stored securely. Passwords are never stored  we use OTP-only authentication.</p>
          <h3>4. Data Sharing</h3>
          <p>We do <strong style="color:#E2E8F0">not</strong> sell your data. We do <strong style="color:#E2E8F0">not</strong> share your data with third parties for marketing. Data may be disclosed only when required by law.</p>
          <h3>5. Your Rights</h3>
          <ul>
            <li>Access your account data at any time.</li>
            <li>Request deletion of your account and all associated data.</li>
            <li>Export your generated reviews.</li>
          </ul>
          <h3>6. Cookies</h3>
          <p>We use only essential session cookies for authentication. No third-party tracking cookies are used.</p>
          <h3>7. Contact</h3>
          <p>For privacy concerns or data requests, contact us through the application.</p>
        </div>
      </div>
    </div>

    <script>
    document.addEventListener('click', function(e) {
        var overlay = e.target.closest('.sai-modal-overlay');
        if (overlay && e.target === overlay) {
            overlay.classList.remove('open');
        }
    });
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            document.querySelectorAll('.sai-modal-overlay.open').forEach(function(m) {
                m.classList.remove('open');
            });
        }
    });
    function openModal(id) {
        document.getElementById(id).classList.add('open');
    }
    </script>
    """, unsafe_allow_html=True)

    #  Centered layout 
    _, col, _ = st.columns([1, 2, 1])
    with col:

        #  Top bar: Back to Home 
        if st.button(" Back to Home", key="auth_back_home_btn", use_container_width=False):
            st.session_state.show_home = True
            st.rerun()

        #  STEP 1  Enter email 
        if st.session_state.auth_mode in ("login", "signup", "verify", "forgot_pass"):

            st.markdown("""
            <div style="background:rgba(15,23,42,.97);border:1px solid rgba(255,255,255,.08);
                border-radius:20px;padding:44px 40px 36px;margin-top:8px;
                box-shadow:0 32px 64px rgba(0,0,0,.55);position:relative;overflow:hidden;">
              <div style="position:absolute;top:0;left:15%;right:15%;height:1px;
                background:linear-gradient(90deg,transparent,rgba(99,120,255,.6),transparent)"></div>
              <div style="text-align:center;margin-bottom:32px">
                <div style="width:52px;height:52px;border-radius:14px;
                    background:linear-gradient(135deg,#4361EE,#7209B7);
                    display:flex;align-items:center;justify-content:center;
                    margin:0 auto 18px;box-shadow:0 0 28px rgba(67,97,238,.5)">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none"
                       stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M22 10v6M2 10l10-5 10 5-10 5z"/>
                    <path d="M6 12v5c3.33 1.67 8.67 1.67 12 0v-5"/>
                  </svg>
                </div>
                <h2 style="color:#F1F5F9;font-size:1.5rem;font-weight:800;margin:0 0 8px;letter-spacing:-.02em">
                  Welcome to ScholarAI
                </h2>
                <p style="color:#64748B;font-size:.87rem;margin:0;line-height:1.5">
                  Enter your email to receive a one-time sign-in code.
                </p>
              </div>
            </div>
            """, unsafe_allow_html=True)

            _err = st.session_state.get("login_error", "")
            if _err:
                st.error(_err)
                st.session_state.login_error = ""

            email_input = st.text_input("Email address", placeholder="you@example.com", key="auth_email_input")

            if st.button("Continue with Email", key="auth_continue_btn", use_container_width=True, type="primary"):
                email = email_input.strip().lower()
                if not email or "@" not in email or "." not in email.split("@")[-1]:
                    st.session_state.login_error = "Please enter a valid email address."
                elif not mailer.is_smtp_configured():
                    st.session_state.login_error = "Email service not configured. Set SMTP_USER and SMTP_PASSWORD in .env"
                else:
                    user = db.get_user_by_email(email)
                    if not user:
                        import random as _rand
                        base = email.split("@")[0]
                        username = base
                        for _ in range(10):
                            ok, _ = db.create_user(username, email, "", "")
                            if ok:
                                break
                            username = base + str(_rand.randint(100, 999))
                        db.update_user_verification(username, True)
                    otp = mailer.generate_6_digit_code()
                    db.update_verification_code(email, otp)
                    with st.spinner("Sending your code..."):
                        sent = mailer.send_verification_code(email, otp)
                    if sent:
                        st.session_state.auth_email = email
                        st.session_state.auth_mode  = "verify_otp"
                        st.session_state.last_code_sent_at = time.time()
                        st.rerun()
                    else:
                        st.session_state.login_error = "Could not send email. Check SMTP settings in .env."
                st.rerun()

            st.markdown("""
            <p style="text-align:center;font-size:.75rem;color:#475569;margin-top:18px;margin-bottom:0;line-height:1.7">
              By continuing you agree to our
              <a href="#" onclick="openModal('modal-terms');return false;"
                 style="color:#818cf8;text-decoration:underline;cursor:pointer">Terms of Use</a>
              and
              <a href="#" onclick="openModal('modal-privacy');return false;"
                 style="color:#818cf8;text-decoration:underline;cursor:pointer">Privacy Policy</a>.
            </p>
            """, unsafe_allow_html=True)

        #  STEP 2  Enter OTP 
        elif st.session_state.auth_mode == "verify_otp":

            _em = st.session_state.get("auth_email", "")
            try:
                _at = _em.index("@")
                _masked = _em[:2] + chr(8226) * max(1, _at - 2) + _em[_at:]
            except Exception:
                _masked = _em

            COOLDOWN = 120
            _last = st.session_state.get("last_code_sent_at", 0)
            _rem  = max(0, int(COOLDOWN - (time.time() - _last))) if _last else 0

            st.markdown(f"""
            <div style="background:rgba(15,23,42,.97);border:1px solid rgba(255,255,255,.08);
                border-radius:20px;padding:44px 40px 36px;margin-top:8px;
                box-shadow:0 32px 64px rgba(0,0,0,.55);position:relative;overflow:hidden;">
              <div style="position:absolute;top:0;left:15%;right:15%;height:1px;
                background:linear-gradient(90deg,transparent,rgba(99,120,255,.6),transparent)"></div>
              <div style="text-align:center;margin-bottom:28px">
                <div style="width:56px;height:56px;border-radius:50%;
                    background:rgba(67,97,238,.15);border:1.5px solid rgba(67,97,238,.35);
                    display:flex;align-items:center;justify-content:center;
                    margin:0 auto 18px;box-shadow:0 0 24px rgba(67,97,238,.2)">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none"
                       stroke="#818cf8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                    <polyline points="22,6 12,13 2,6"/>
                  </svg>
                </div>
                <h2 style="color:#F1F5F9;font-size:1.4rem;font-weight:800;margin:0 0 8px">Check your inbox</h2>
                <p style="color:#64748B;font-size:.87rem;margin:0 0 6px">We sent a 6-digit code to</p>
                <p style="color:#818cf8;font-weight:600;font-size:.93rem;margin:0 0 4px">{_masked}</p>
                <p style="color:#475569;font-size:.75rem;margin:0">Expires in 10 min &middot; check spam if not received</p>
              </div>
            </div>
            """, unsafe_allow_html=True)

            _v_err = st.session_state.get("v_error", "")
            if _v_err:
                st.error(_v_err)
                st.session_state.v_error = ""

            otp_in = st.text_input("6-digit code", placeholder="Enter your code", max_chars=6, key="verify_otp_input")

            if st.button("Verify & Sign In", key="verify_otp_btn", use_container_width=True, type="primary"):
                user = db.get_user_by_email(_em)
                if user:
                    stored    = (user.get("verification_code") or "").strip()
                    entered   = otp_in.strip()
                    issued_at = float(user.get("verification_code_sent_at") or 0)
                    if not stored:
                        st.session_state.v_error = "No active code. Please request a new one."
                    elif mailer.is_otp_expired(issued_at):
                        st.session_state.v_error = "Code expired. Please request a new one."
                    elif stored != entered:
                        st.session_state.v_error = "Incorrect code. Please try again."
                    else:
                        db.update_verification_code(_em, "")
                        db.update_user_verification(user["username"], True)
                        st.session_state.user_authenticated = True
                        st.session_state.username      = user["username"]
                        st.session_state.auth_username = user["username"]
                        st.session_state.auth_email    = _em
                        st.session_state.user_tier     = user.get("tier", "free")
                        st.session_state.auth_mode     = "login"
                        st.rerun()
                else:
                    st.session_state.v_error = "Account not found. Go back and try again."
                st.rerun()

            if _rem > 0:
                components.html(f"""
                <div id="tw" style="text-align:center;margin-top:14px">
                  <p style="color:#475569;font-size:.82rem;margin:0;font-family:sans-serif">
                    Resend available in
                    <span id="tv" style="color:#818cf8;font-weight:700">{_rem//60:02d}:{_rem%60:02d}</span>
                  </p>
                </div>
                <script>
                (function(){{
                  var r={_rem},el=document.getElementById('tv'),w=document.getElementById('tw');
                  function fmt(s){{return String(Math.floor(s/60)).padStart(2,'0')+':'+String(s%60).padStart(2,'0');}}
                  function tick(){{
                    if(r<=0){{w.innerHTML='<p style="color:#818cf8;font-size:.82rem;font-family:sans-serif;text-align:center;cursor:pointer" onclick="window.parent.location.reload()">Click to resend code</p>';return;}}
                    if(el)el.textContent=fmt(r);r--;setTimeout(tick,1000);
                  }}
                  tick();
                }})();
                </script>
                """, height=40)
            else:
                if st.button("Resend code", key="resend_otp_btn", use_container_width=True):
                    new_otp = mailer.generate_6_digit_code()
                    db.update_verification_code(_em, new_otp)
                    with st.spinner("Resending..."):
                        sent = mailer.send_verification_code(_em, new_otp)
                    if sent:
                        st.session_state.last_code_sent_at = time.time()
                        st.toast("New code sent!")
                    else:
                        st.error("Failed to send email. Check SMTP settings.")
                    st.rerun()

            st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)
            if st.button("Use a different email", key="back_to_email_btn", use_container_width=True):
                st.session_state.auth_mode = "login"
                st.session_state.v_error   = ""
                st.rerun()

    st.stop()





# ══════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════
def render_sidebar():
    st.sidebar.markdown(f"""
    <div class="sidebar-glass animate-up">
      <div style="font-size:0.7rem; font-weight:800; color:var(--indigo); letter-spacing:0.1em; margin-bottom:8px;">ACTIVE SESSION</div>
      <div style="font-weight:700; color:var(--white); font-size:1.1rem;">{st.session_state.auth_username}</div>
      <div style="font-size:0.8rem; color:var(--muted);">{st.session_state.auth_email}</div>
      <div style="margin-top:12px; display:flex; align-items:center; gap:8px;">
        <span class="pill pill-gold">{st.session_state.user_tier.upper()}</span>
        <span style="font-size:0.75rem; color:var(--muted);">Credits: {st.session_state.user_credits} Used</span>
      </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.user_tier == "free":
        if st.sidebar.button("Upgrade to Premium", use_container_width=True, type="primary"):
            st.session_state.show_paywall = True
            st.rerun()

    st.sidebar.markdown("---")
    
    # Existing sidebar items: API Key, Style, etc.
    with st.sidebar:
        # Brand
        st.markdown("""
        <div style="padding:16px 0 8px; border-bottom:1px solid rgba(255,255,255,0.08); margin-bottom:16px;">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
            <div style="width:28px;height:28px;border-radius:7px;background:linear-gradient(135deg,#4361EE,#7209B7);display:flex;align-items:center;justify-content:center;flex-shrink:0;">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3.33 1.67 8.67 1.67 12 0v-5"/></svg>
            </div>
            <div style="font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:800;color:#F8F9FC;">ScholarAI</div>
          </div>
          <div style="font-size:0.72rem;color:#6B7A99;margin-top:2px;">Academic Literature Review Generator</div>
        </div>
        """, unsafe_allow_html=True)

        # ── User Profile ───────────────────────────────────────────
        st.markdown(f"Logged in as: **{st.session_state.get('username', 'User')}**")
        st.markdown("---")

        # ── AI Provider & API Key ──────────────────────────────────
        st.markdown('<div class="sidebar-section-title">🤖 AI Provider</div>',
                    unsafe_allow_html=True)
        provider = st.selectbox(
            "AI Provider",
            ["google", "openai"],
            index=0 if st.session_state.ai_provider == "google" else 1,
            format_func=lambda x: "Google Gemini (Free)" if x == "google" else "OpenAI GPT-4",
            label_visibility="collapsed",
        )
        st.session_state.ai_provider = provider

        if provider == "google":
            gemini_key = st.text_input(
                "Google Gemini API Key",
                value=st.session_state.gemini_api_key,
                type="password",
                placeholder="AIzaSy...",
                help="Get a free key at https://aistudio.google.com/app/apikey",
            )
            if gemini_key != st.session_state.gemini_api_key:
                st.session_state.gemini_api_key = gemini_key.strip()
            if not st.session_state.gemini_api_key:
                st.caption("🔑 [Get free Gemini key →](https://aistudio.google.com/app/apikey)")
        else:
            openai_key = st.text_input(
                "OpenAI API Key",
                value=st.session_state.api_key,
                type="password",
                placeholder="sk-...",
            )
            if openai_key != st.session_state.api_key:
                st.session_state.api_key = openai_key.strip()

        st.markdown("---")

        # ── Citation Style ─────────────────────────────────────────
        st.markdown('<div class="sidebar-section-title">📚 Citation Style</div>',
                    unsafe_allow_html=True)
        style = st.selectbox(
            "Citation Style", STYLES,
            index=STYLES.index(st.session_state.citation_style),
            label_visibility="collapsed",
        )
        st.session_state.citation_style = style

        style_notes = {
            "APA 7th":     "Social sciences, psychology, education",
            "Harvard":     "UK & African universities, natural sciences",
            "MLA 9th":     "Humanities, literature, language studies",
            "Chicago 17th":"History, arts, some social sciences",
            "Vancouver":   "Medicine, nursing, biomedical sciences",
            "IEEE":        "Engineering, computer science, technology",
        }
        st.caption(f"📌 {style_notes.get(style, '')}")

        st.markdown("---")

        # ── History ───────────────────────────────────────────────
        if st.session_state.history:
            st.markdown('<div class="sidebar-section-title">📣 Session History</div>',
                        unsafe_allow_html=True)
            for i, h in enumerate(reversed(st.session_state.history)):
                with st.expander(f"Review {len(st.session_state.history)-i}: {h['topic'][:30]}..."):
                    st.caption(f"Style: {h['citation_style']} ┬╖ {h['word_count']} words")
                    if st.button("🔄 Reload", key=f"reload_{i}"):
                        st.session_state.result = h
                        st.rerun()
            st.markdown("---")

        # ── Reset ─────────────────────────────────────────────────
        if st.button("Generate Literature Review", type="primary", use_container_width=True):
            # ≡ƒÆ╕ MONETIZATION CHECK
            if st.session_state.user_tier == "free" and st.session_state.user_credits >= 30: # relax for dev
                st.session_state.show_paywall = True
                st.rerun()
                
            if not st.session_state.topic:
                st.error("❌ Please enter a research topic in Phase 01.")
            elif not st.session_state.articles:
                st.error("❌ Please upload at least one academic article in Phase 02.")
            elif st.session_state.ai_provider == "google" and not st.session_state.gemini_api_key:
                st.error("❌ Please enter a Google Gemini API Key in the sidebar.")
            elif st.session_state.ai_provider == "openai" and not st.session_state.api_key:
                st.error("❌ Please enter an OpenAI API Key in the sidebar.")
            else:
                st.session_state.generating = True
                st.rerun()

        st.markdown("---")
        if st.button("Sign Out", use_container_width=True):
            # Clear persistent token
            db.update_remember_token(st.session_state.username, None)
            render_remember_me_js("clear")
            
            st.session_state.user_authenticated = False
            st.session_state.username = None
            st.rerun()

        st.markdown("---")
        st.caption("ScholarAI v1.0 ┬╖ Powered by GPT-4o")
        st.caption("⚠ AI draft — review before submission")


render_sidebar()

if st.session_state.show_paywall:
    render_paywall()


# ══════════════════════════════════════════════════════════════════
#  MAIN CONTENT
# ══════════════════════════════════════════════════════════════════

# ── Floating Glass Header ─────────────────────────────────────────
st.markdown("""
<div class="scholar-platinum-header">
  <div class="platinum-logo">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3.33 1.67 8.67 1.67 12 0v-5"/></svg>
  </div>
  <div class="platinum-title">ScholarAI Platinum</div>
  <div style="width:1px; height:20px; background:rgba(255,255,255,0.1); margin:0 4px;"></div>
  <div style="font-size:0.75rem; color:rgba(255,255,255,0.5); letter-spacing:0.05em; text-transform:uppercase;">v2.0 PRO</div>
</div>
""", unsafe_allow_html=True)


# ── Onboarding (shown when no articles) ─────────────
def render_onboarding():
    st.markdown("""
    <div class="platinum-card animate-up" style="background: linear-gradient(135deg, rgba(67, 97, 238, 0.1), rgba(114, 9, 183, 0.1)); border-color: rgba(67, 97, 238, 0.3);">
      <div style="font-size:0.7rem; font-weight:800; color:var(--indigo); letter-spacing:0.15em; margin-bottom:12px; text-transform:uppercase;">System Initialized</div>
      <div class="step-heading" style="font-size:2rem; margin-bottom:16px;">Welcome to the Future of Research.</div>
      <div class="step-description" style="font-size:1.05rem; color:var(--white); margin-bottom:32px;">
        Generate a professional, cited academic literature review from your sources in seconds.
      </div>
      <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:20px; margin-bottom:32px;">
        <div style="padding:20px; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">
          <div style="width:32px;height:32px;border-radius:8px;background:rgba(67,97,238,0.15);display:flex;align-items:center;justify-content:center;margin-bottom:12px;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#818cf8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
          </div>
          <div style="font-weight:700; color:var(--white); font-size:0.88rem; margin-bottom:4px;">1. Define Topic</div>
          <div style="font-size:0.75rem; color:var(--muted);">Set your research scope and objective.</div>
        </div>
        <div style="padding:20px; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">
          <div style="width:32px;height:32px;border-radius:8px;background:rgba(114,9,183,0.15);display:flex;align-items:center;justify-content:center;margin-bottom:12px;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#c77dff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          </div>
          <div style="font-weight:700; color:var(--white); font-size:0.88rem; margin-bottom:4px;">2. Upload Sources</div>
          <div style="font-size:0.75rem; color:var(--muted);">Upload academic PDFs or Docs (tier-based limit).</div>
        </div>
        <div style="padding:20px; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">
          <div style="width:32px;height:32px;border-radius:8px;background:rgba(6,214,160,0.12);display:flex;align-items:center;justify-content:center;margin-bottom:12px;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#06D6A0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
          </div>
          <div style="font-weight:700; color:var(--white); font-size:0.88rem; margin-bottom:4px;">3. Generate</div>
          <div style="font-size:0.75rem; color:var(--muted);">Get a verified synthesis with real citations.</div>
        </div>
      </div>
      <div style="padding:14px 16px; background:rgba(6,214,160,0.05); border:1px solid rgba(6,214,160,0.2); border-radius:10px; display:flex; align-items:center; gap:12px;">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#06D6A0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        <div style="font-size:0.82rem; color:var(--teal); font-weight:500;">
          <strong>ScholarAI Integrity:</strong> Our AI only writes from YOUR uploaded articles to prevent hallucinations and ensure academic rigor.
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

if not st.session_state.articles:
    render_onboarding()


# ══════════════════════════════════════════════════════════════════
#  STEP 1 — RESEARCH TOPIC
# ══════════════════════════════════════════════════════════════════
# ── STEP 1 ────────────────────────────────────────────────────────
st.markdown("""
<div class="platinum-card animate-up">
  <span class="step-number">Phase 01</span>
  <h2 class="step-heading">Research Objective</h2>
  <p class="step-description">Enter your approved research topic or hypothesis title.</p>
</div>
""", unsafe_allow_html=True)

topic_input = st.text_area(
    "Research Topic",
    value=st.session_state.topic,
    placeholder="e.g. The impact of climate change on agricultural productivity in Sub-Saharan Africa",
    height=90,
    max_chars=300,
    label_visibility="collapsed",
)
st.session_state.topic = topic_input.strip()

char_count = len(topic_input)
col_a, col_b = st.columns([3,1])
with col_a:
    if char_count < 20:
        st.caption(f"≡ƒÆí {char_count}/300 chars — more detail = better review (aim for 30+ chars)")
    elif char_count < 100:
        st.caption(f"✏ {char_count}/300 chars — good topic length")
    else:
        st.caption(f"✏ {char_count}/300 chars — detailed topic")


# ══════════════════════════════════════════════════════════════════
#  STEP 2 — ARTICLE UPLOAD
# ══════════════════════════════════════════════════════════════════
# ── STEP 2 ────────────────────────────────────────────────────────
st.markdown("""
<div class="platinum-card animate-up" style="margin-top:12px;">
  <span class="step-number">Phase 02</span>
  <h2 class="step-heading">Source Configuration</h2>
  <p class="step-description">Upload your core academic articles (PDF/DOCX/TXT/MD) that will serve as the exclusive knowledge base for your AI synthesis.</p>
</div>
""", unsafe_allow_html=True)

# MAX_ARTICLES based on tier
MAX_ARTICLES = 12 if st.session_state.user_tier == "free" else 30

# File upload widget
slots_used = len(st.session_state.articles)
slots_left = MAX_ARTICLES - slots_used

if slots_left > 0:
    uploaded_files = st.file_uploader(
        f"Upload up to {slots_left} more article(s)",
        type=["pdf", "docx", "txt", "md"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )
    if uploaded_files:
        new_count = 0
        for uf in uploaded_files:
            # Check for duplicates
            existing_names = [a["filename"] for a in st.session_state.articles]
            if uf.name in existing_names:
                st.warning(f"⚠ '{uf.name}' is already uploaded — skipped.")
                continue
            if len(st.session_state.articles) >= MAX_ARTICLES:
                st.warning(f"⚠ Maximum {MAX_ARTICLES} articles reached.")
                break
            if uf.size > 15 * 1024 * 1024:
                st.error(f"⚠ '{uf.name}' exceeds 15 MB — please use a smaller file.")
                continue

            with st.spinner(f"Extracting text from {uf.name}..."):
                file_bytes = uf.read()
                text, info = extract_text(file_bytes, uf.name)

            if not info["success"]:
                st.error(f"❌ Could not extract text from **{uf.name}**: {info['error']}")
                continue

            st.session_state.articles.append({
                "filename": uf.name,
                "text":     text,
                "info":     info,
                "size":     uf.size,
                "metadata": None,   # filled during generation
            })
            new_count += 1

        if new_count:
            st.rerun()
else:
    st.info(f"✏ Maximum {MAX_ARTICLES} articles uploaded. Remove one to add another.")

# ── Display uploaded article cards ────────────────────────────────
if st.session_state.articles:
    st.markdown(f"**{len(st.session_state.articles)} article(s) uploaded:**")
    for i, art in enumerate(st.session_state.articles):
        info = art["info"]
        col1, col2 = st.columns([6, 1])
        with col1:
            ext = art["filename"].rsplit(".", 1)[-1].upper()
            st.markdown(f"""
            <div class="article-card">
              <div>
                <div class="article-card-title">
                  <span class="article-badge">{ext}</span>&nbsp;&nbsp;{art["filename"]}
                </div>
                <div class="article-card-meta">
                  {info["pages"]} page(s) ┬╖ {info["word_count"]:,} words ┬╖
                  {format_bytes(art["size"])} ┬╖ {estimate_read_time(info["word_count"])}
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            if st.button("🗑", key=f"remove_{i}", help="Remove this article"):
                st.session_state.articles.pop(i)
                st.rerun()


# ── Processing logic ───────────────────────────────────────────────
if st.session_state.generating:
    avatar_loader = render_generation_avatar()
    with st.spinner("ScholarAI is synthesizing your research..."):
        try:
            active_provider = st.session_state.ai_provider
            if st.session_state.backend_api_url:
                result = generate_review_via_private_api(
                    topic=st.session_state.topic,
                    articles=st.session_state.articles,
                    citation_style=st.session_state.citation_style,
                    provider=active_provider,
                )
            else:
                # Initialize direct provider client
                if active_provider == "google":
                    client = st.session_state.gemini_api_key  # pass key directly
                else:
                    from openai import OpenAI
                    client = OpenAI(api_key=st.session_state.api_key)
                try:
                    result = generate_review(
                        client,
                        st.session_state.topic,
                        st.session_state.articles,
                        st.session_state.citation_style,
                        provider=active_provider,
                        progress_cb=st.toast
                    )
                except Exception as gen_err:
                    err_text = str(gen_err).lower()
                    if (
                        active_provider == "google"
                        and st.session_state.api_key
                        and st.session_state.get("allow_openai_fallback", False)
                    ):
                        st.warning("⚠ Gemini failed. Retrying automatically with OpenAI...")
                        from openai import OpenAI
                        fallback_client = OpenAI(api_key=st.session_state.api_key)
                        result = generate_review(
                            fallback_client,
                            st.session_state.topic,
                            st.session_state.articles,
                            st.session_state.citation_style,
                            provider="openai",
                            progress_cb=st.toast
                        )
                    elif active_provider == "openai" and st.session_state.gemini_api_key and (
                        "invalid_api_key" in err_text
                        or "401" in err_text
                        or "authentication" in err_text
                        or "insufficient_quota" in err_text
                        or "429" in err_text
                        or "exceeded your current quota" in err_text
                    ):
                        st.warning("⚠ OpenAI unavailable/quota reached. Retrying automatically with Gemini...")
                        fallback_client = st.session_state.gemini_api_key
                        result = generate_review(
                            fallback_client,
                            st.session_state.topic,
                            st.session_state.articles,
                            st.session_state.citation_style,
                            provider="google",
                            progress_cb=st.toast
                        )
                    else:
                        raise gen_err

            result["topic"] = st.session_state.topic
            result["citation_style"] = st.session_state.citation_style
            review_id = db.log_review(
                session_id=st.session_state.session_id,
                topic=st.session_state.topic,
                article_count=len(st.session_state.articles),
                citation_style=st.session_state.citation_style,
                word_count=result["word_count"],
            )
            result["review_id"] = review_id
            st.session_state.review_id = review_id
            st.session_state.result = result
            st.session_state.history.append(result)

            if st.session_state.auth_username:
                db.increment_user_credits(st.session_state.auth_username)
                status = db.get_user_status(st.session_state.auth_username)
                st.session_state.user_credits = status.get("credits_used", st.session_state.user_credits)

        except Exception as e:
            st.error(f"Generation failed: {e}")
        finally:
            st.session_state.generating = False
            avatar_loader.empty()
            st.rerun()


# ══════════════════════════════════════════════════════════════════
#  STEP 3 — GENERATE
# ══════════════════════════════════════════════════════════════════
# ── STEP 3 ────────────────────────────────────────────────────────
st.markdown("""
<div class="platinum-card animate-up" style="margin-top:12px;">
  <span class="step-number">Phase 03</span>
  <h2 class="step-heading">✨ Synthesis Engine</h2>
  <p class="step-description">Initiate the AI-powered literature review generation. Ensure your citation style is correctly set in the glass sidebar.</p>
</div>
""", unsafe_allow_html=True)

# Citation style confirm badge
st.markdown(
    f'<div class="style-confirm">📖 Citation style: <strong>{st.session_state.citation_style}</strong>'
    f' — change in sidebar if needed.</div>',
    unsafe_allow_html=True
)

# Readiness checks
topic_ok    = len(st.session_state.topic) >= 10
articles_ok = len(st.session_state.articles) >= 1
if st.session_state.backend_api_url:
    key_ok = True
elif st.session_state.ai_provider == "google":
    key_ok = bool(st.session_state.gemini_api_key)
else:
    key_ok = bool(st.session_state.api_key)
ready       = topic_ok and articles_ok and key_ok

if not ready:
    missing = []
    if not topic_ok:   missing.append("research topic (min 10 chars)")
    if not articles_ok:missing.append("at least 1 article")
    if missing:
        st.warning(f"⚠ Before generating, please add: {', '.join(missing)}.")
    if not key_ok:
        if st.session_state.backend_api_url:
            st.error("❌ Private API URL is invalid or backend is not running.")
        elif st.session_state.ai_provider == "google":
            st.error("❌ Google Gemini key missing. Set GOOGLE_API_KEY in .env.")
        else:
            st.error("❌ OpenAI key missing. Set OPENAI_API_KEY in .env.")

col_gen, col_regen = st.columns([3, 1])
with col_gen:
    generate_clicked = st.button(
        "✨ Generate Literature Review",
        disabled=not (ready and key_ok),
        use_container_width=True,
        type="primary",
    )
    
    # 📖 MONETIZATION: Intercept free user first generation
    if generate_clicked and st.session_state.user_tier == "free" and st.session_state.user_credits >= 1:
        st.session_state.show_paywall = True
        st.rerun()
with col_regen:
    if st.session_state.result:
        regen_clicked = st.button("🔁 Regenerate", use_container_width=True,
                                   help="Re-run with same inputs")
        if regen_clicked:
            generate_clicked = True
            st.session_state.result = None


# ══════════════════════════════════════════════════════════════════
#  GENERATION PIPELINE
# ══════════════════════════════════════════════════════════════════
if generate_clicked and ready:
    st.session_state.result  = None
    st.session_state.error   = None
    avatar_loader = render_generation_avatar()

    client = None
    if not st.session_state.backend_api_url:
        if st.session_state.ai_provider == "google":
            client = st.session_state.gemini_api_key  # pass key directly
        else:
            from openai import OpenAI
            client = OpenAI(api_key=st.session_state.api_key)

    progress_msgs = []

    with st.status("≡ƒö¼ Generating your literature review...", expanded=True) as status:
        try:
            def update_progress(msg: str):
                st.write(msg)
                progress_msgs.append(msg)

            active_provider = st.session_state.ai_provider
            try:
                if st.session_state.backend_api_url:
                    result = generate_review_via_private_api(
                        topic=st.session_state.topic,
                        articles=st.session_state.articles,
                        citation_style=st.session_state.citation_style,
                        provider=active_provider,
                    )
                    update_progress("≡ƒöÉ Generated via private backend API.")
                else:
                    result = generate_review(
                        client=client,
                        topic=st.session_state.topic,
                        articles=st.session_state.articles,
                        citation_style=st.session_state.citation_style,
                        provider=active_provider,
                        progress_cb=update_progress,
                    )
            except Exception as gen_err:
                err_text = str(gen_err).lower()
                if (
                    active_provider == "google"
                    and st.session_state.api_key
                    and st.session_state.get("allow_openai_fallback", False)
                    and not st.session_state.backend_api_url
                ):
                    update_progress("⚠ Gemini failed. Retrying with OpenAI...")
                    from openai import OpenAI
                    fallback_client = OpenAI(api_key=st.session_state.api_key)
                    result = generate_review(
                        client=fallback_client,
                        topic=st.session_state.topic,
                        articles=st.session_state.articles,
                        citation_style=st.session_state.citation_style,
                        provider="openai",
                        progress_cb=update_progress,
                    )
                elif active_provider == "openai" and st.session_state.gemini_api_key and (
                    "invalid_api_key" in err_text
                    or "401" in err_text
                    or "authentication" in err_text
                    or "insufficient_quota" in err_text
                    or "429" in err_text
                    or "exceeded your current quota" in err_text
                ) and not st.session_state.backend_api_url:
                    update_progress("⚠ OpenAI unavailable/quota reached. Retrying with Gemini...")
                    fallback_client = st.session_state.gemini_api_key
                    result = generate_review(
                        client=fallback_client,
                        topic=st.session_state.topic,
                        articles=st.session_state.articles,
                        citation_style=st.session_state.citation_style,
                        provider="google",
                        progress_cb=update_progress,
                    )
                else:
                    raise gen_err
            result["topic"]          = st.session_state.topic
            result["citation_style"] = st.session_state.citation_style

            # Log to DB
            review_id = db.log_review(
                session_id    = st.session_state.session_id,
                topic         = st.session_state.topic,
                article_count = len(st.session_state.articles),
                citation_style= st.session_state.citation_style,
                word_count    = result["word_count"],
            )
            result["review_id"] = review_id
            st.session_state.review_id = review_id

            # ≡ƒÆ╕ MONETIZATION: Increment credits
            if st.session_state.auth_username:
                db.increment_user_credits(st.session_state.auth_username)
                status = db.get_user_status(st.session_state.auth_username)
                st.session_state.user_credits = status["credits_used"]

            # Save to session result and history
            st.session_state.result = result
            history_entry = {
                "topic":          st.session_state.topic,
                "citation_style": st.session_state.citation_style,
                "word_count":     result["word_count"],
                **result,
            }
            st.session_state.history = ([history_entry] + st.session_state.history)[:3]

            status.update(
                label=f"✅ Literature review ready! ({result['word_count']:,} words)",
                state="complete"
            )

        except Exception as e:
            err_msg = str(e)
            st.session_state.error = err_msg
            status.update(label="❌ Generation failed", state="error")
            st.error(f"**Generation error:** {err_msg[:300]}")
            if "rate_limit" in err_msg.lower():
                st.info("≡ƒÆí You've hit OpenAI's rate limit. Wait 30 seconds and try again.")
            elif "api_key" in err_msg.lower() or "authentication" in err_msg.lower():
                st.info("≡ƒÆí Check your API key in the sidebar — it may be invalid or expired.")
    avatar_loader.empty()


# ══════════════════════════════════════════════════════════════════
#  OUTPUT — REVIEW DISPLAY & DOWNLOADS
# ══════════════════════════════════════════════════════════════════
def render_output(result: dict):
    st.markdown("---")

    # ── Header badges ──────────────────────────────────────────────
    arts_count = len(result.get("articles_meta", []))
    wc = result.get("word_count", 0)
    st.markdown(f"""
    <div class="review-header-bar animate-up">
      <span class="pill pill-teal">✅ Review Ready</span>
      <span class="pill pill-indigo">📖 {result['citation_style']}</span>
      <span class="pill pill-indigo">≡ƒôä {arts_count} article(s)</span>
      <span class="pill pill-indigo">✍️ {wc:,} words</span>
      <span class="pill pill-amber">⏱ ~{max(1, wc//200)} min read</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Source attribution ─────────────────────────────────────────
    with st.expander("≡ƒöù Source Attribution — which articles contributed to each claim"):
        st.markdown('<div class="attr-panel">', unsafe_allow_html=True)
        attribution = result.get("attribution", [])
        if attribution:
            for art in attribution:
                st.markdown(f"""
                <div class="attr-item">
                  <span class="attr-badge">{art['intext_key']}</span>
                  <span><strong>{art['title']}</strong>
                  ({', '.join(art['authors'][:1])} {art['year']}) —
                  cited approximately {art['count']} time(s)</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("Attribution data not available.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ── The review itself ──────────────────────────────────────────
    review_text = result.get("review_text", "")
    refs_text   = result.get("references_text", "")

    def _clean_generated_text(text: str) -> str:
        """Remove accidental HTML/code wrappers from model output."""
        if not text:
            return ""
        cleaned = text.replace("```html", "```").replace("```markdown", "```")
        cleaned = cleaned.replace("```", "")
        # Strip common HTML tags that sometimes leak from model output
        cleaned = re.sub(r"</?(div|span|p|h1|h2|h3|h4|h5|h6|br|hr)[^>]*>", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"<[^>]+>", "", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
        return cleaned

    review_text = _clean_generated_text(review_text)
    refs_text = _clean_generated_text(refs_text)

    # Render as readable HTML in a styled container
    def md_to_html(text: str) -> str:
        """Convert basic markdown headings to HTML for the review display."""
        lines = text.split("\n")
        html_parts = []
        for line in lines:
            line = line.strip()
            if not line:
                html_parts.append("<br/>")
            elif line.startswith("## "):
                html_parts.append(f"<h2 style='color:#1A2A40;font-family:Arial,sans-serif;"
                                   f"font-size:1.1rem;margin:20px 0 8px;'>{line[3:]}</h2>")
            elif line.startswith("# "):
                html_parts.append(f"<h1 style='color:#0A1628;font-family:Arial,sans-serif;"
                                   f"font-size:1.3rem;margin:24px 0 10px;'>{line[2:]}</h1>")
            else:
                html_parts.append(f"<p>{line}</p>")
        return "\n".join(html_parts)

    refs_html = ""
    for ref in refs_text.split("\n\n"):
        ref = ref.strip()
        if ref:
            refs_html += f"<p>{ref}</p>"

    full_html = f"""
    <div class="result-container animate-up">
      <div style="text-align:center; margin-bottom:48px;">
        <div style="font-size:0.7rem; font-weight:800; color:var(--indigo); letter-spacing:0.2em; margin-bottom:8px;">GENERATED SYNTHESIS</div>
        <h1 style="border:none; margin:0; padding:0; font-size:2.4rem;">Literature Review</h1>
        <div style="width:60px; height:3px; background:var(--indigo); margin:24px auto;"></div>
        <p style="font-family:'DM Sans', sans-serif; font-size:0.9rem; color:#64748B; font-style:normal;">
          Topic: <span style="color:#0F172A; font-weight:600;">{result['topic']}</span> &nbsp;┬╖&nbsp;
          Style: <span style="color:#0F172A; font-weight:600;">{result['citation_style']}</span>
        </p>
      </div>
      
      <div class="academic-body">
        {md_to_html(review_text)}
      </div>

      <div style="margin-top:64px; padding-top:32px; border-top:1px solid #E2E8F0;">
        <h2 style="font-size:1.6rem; margin-bottom:24px; border:none; padding:0;">References</h2>
        <div style="font-family:'DM Sans', sans-serif; font-size:1rem; line-height:1.6; color:#475569;">
          {refs_html}
        </div>
      </div>
    </div>
    """
    components.html(f"""
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
    :root{{--indigo:#4361EE}}
    body{{margin:0;padding:0;background:transparent;font-family:'DM Sans',sans-serif}}
    .result-container{{background:#fff;border-radius:16px;padding:48px;box-shadow:0 4px 24px rgba(0,0,0,0.08);max-width:100%;}}
    .academic-body p{{color:#334155;font-size:1rem;line-height:1.8;margin-bottom:1rem}}
    .academic-body h1,.academic-body h2{{color:#0F172A;margin:1.5rem 0 0.75rem}}
    </style>
    {full_html}
    """, height=max(800, len(review_text) // 3), scrolling=True)

    # ── Download bar ───────────────────────────────────────────────
    st.markdown('<div class="download-bar animate-up">', unsafe_allow_html=True)
    st.markdown('<div class="download-bar-title">📥 Download Your Review</div>',
                unsafe_allow_html=True)

    slug  = slugify(result["topic"])
    style_slug = result["citation_style"].replace(" ", "").replace("th","").replace("st","")
    ts    = now_str()

    dl_col1, dl_col2, dl_col3, dl_col4 = st.columns(4)

    # PDF download
    with dl_col1:
        with st.spinner("Building PDF..."):
            try:
                pdf_bytes = generate_pdf(
                    review_text, refs_text,
                    result["topic"], result["citation_style"]
                )
                if st.download_button(
                    "≡ƒôä Download PDF",
                    data=pdf_bytes,
                    file_name=f"literature_review_{slug}_{style_slug}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                ):
                    if result.get("review_id"):
                        db.log_download(result["review_id"], "PDF")
            except Exception as e:
                st.error(f"PDF error: {e}")

    # DOCX download
    with dl_col2:
        with st.spinner("Building DOCX..."):
            try:
                docx_bytes = generate_docx(
                    review_text, refs_text,
                    result["topic"], result["citation_style"]
                )
                if st.download_button(
                    "📥 Download DOCX",
                    data=docx_bytes,
                    file_name=f"literature_review_{slug}_{style_slug}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                ):
                    if result.get("review_id"):
                        db.log_download(result["review_id"], "DOCX")
            except Exception as e:
                st.error(f"DOCX error: {e}")

    # References only
    with dl_col3:
        refs_only_bytes = refs_text.encode("utf-8")
        if st.download_button(
            "📖 References Only",
            data=refs_only_bytes,
            file_name=f"references_{slug}_{style_slug}.txt",
            mime="text/plain",
            use_container_width=True,
        ):
            if result.get("review_id"):
                db.log_download(result["review_id"], "References")

    # Plain text copy
    with dl_col4:
        full_text = (f"LITERATURE REVIEW\n"
                     f"Topic: {result['topic']}\n"
                     f"Citation Style: {result['citation_style']}\n"
                     f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                     f"{review_text}\n\n"
                     f"REFERENCES\n{refs_text}")
        if st.download_button(
            "≡ƒôï Copy as Text",
            data=full_text.encode("utf-8"),
            file_name=f"literature_review_{slug}_{style_slug}.txt",
            mime="text/plain",
            use_container_width=True,
        ):
            if result.get("review_id"):
                db.log_download(result["review_id"], "TXT")

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Academic disclaimer ────────────────────────────────────────
    st.markdown("""
    <div style="background:rgba(244,162,97,0.08);border:1px solid rgba(244,162,97,0.25);
                border-radius:8px;padding:12px 16px;margin-top:12px;
                font-size:0.78rem;color:#F4A261;">
      ⚠️ <strong>Academic Integrity Reminder:</strong>
      ScholarAI generates an AI-assisted first draft. You are responsible for reviewing all content,
      verifying citations against source articles, and ensuring compliance with your institution's
      academic integrity policy before submission.
    </div>
    """, unsafe_allow_html=True)


if st.session_state.result:
    render_output(st.session_state.result)

# ── Footer ─────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<div style="text-align:center;font-size:0.75rem;color:#6B7A99;padding:8px 0;">'
    'ScholarAI v1.0 ┬╖ Powered by OpenAI GPT-4o ┬╖ '
    '<a href="/Admin_Dashboard" style="color:#4361EE;">Admin Dashboard</a>'
    '</div>',
    unsafe_allow_html=True
)
