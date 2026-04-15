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

load_dotenv()

# ── Page config (must be first Streamlit call) ─────────────────────
st.set_page_config(
    page_title="ScholarAI — Literature Review Generator",
    page_icon="🎓",
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
import database as db
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
        if st.button("🚀 Buy Weekly", key="buy_w", use_container_width=True):
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
        if st.button("👑 Buy Yearly", key="buy_y", use_container_width=True):
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
    css_path = Path("assets/style.css")
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
            import threading
            threading.Thread(target=mailer.send_password_reset, args=(_em, _rc), daemon=True).start()
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
# Handle ?go=app BEFORE rendering home — skips the heavy home render entirely
if st.query_params.get("go") == "app":
    st.query_params.clear()
    st.session_state.show_home = False

if st.session_state.get("show_home", True) and not st.session_state.user_authenticated:
    render_home()
    st.stop()


# ── Password Reset Card ────────────────────────────────────────────────────
def _build_reset_card(step, email, remaining, err):
    mm = str(remaining // 60).zfill(2)
    ss = str(remaining % 60).zfill(2)
    def sc(st_): return "active" if step == st_ else ("done" if (st_ == "otp" and step in ("password","success")) or (st_ == "password" and step == "success") else "idle")
    def si(st_): return '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>' if (st_ == "otp" and step in ("password","success")) or (st_ == "password" and step == "success") or (st_ == "success" and step == "success") else {"otp":"1","password":"2","success":"3"}[st_]
    c1 = "done" if step in ("password","success") else ""
    c2 = "done" if step == "success" else ""
    ov, pv, sv = ("flex" if step=="otp" else "none"), ("flex" if step=="password" else "none"), ("flex" if step=="success" else "none")
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{--p:#4361EE;--p2:#7209B7;--s:#10B981;--bg:#020617;--card:rgba(13,20,40,.95);--tx:#F8FAFC;--mu:#94A3B8;--br:rgba(255,255,255,.1);--glow:rgba(67,97,238,.4)}}
html,body{{font-family:'Plus Jakarta Sans',sans-serif;background:transparent;height:100%;margin:0;padding:0;overflow:hidden}}
.fullscreen{{width:100%;min-height:100vh;background:var(--bg);display:flex;align-items:center;justify-content:center;padding:20px 0}}
body::before{{content:'';position:fixed;inset:0;background:radial-gradient(ellipse at 20% 60%,rgba(67,97,238,.13),transparent 55%),radial-gradient(ellipse at 80% 20%,rgba(114,9,183,.1),transparent 50%);pointer-events:none;z-index:9998}}
.card{{background:var(--card);backdrop-filter:blur(28px);border:1px solid var(--br);border-radius:28px;padding:40px 36px;width:460px;max-width:calc(100vw - 24px);box-shadow:0 32px 64px rgba(0,0,0,.55);position:relative;overflow:hidden;animation:up .4s cubic-bezier(.16,1,.3,1) both}}
.card::before{{content:'';position:absolute;top:0;left:12%;right:12%;height:1px;background:linear-gradient(90deg,transparent,rgba(99,120,255,.55),transparent)}}
@keyframes up{{from{{opacity:0;transform:translateY(20px) scale(.97)}}to{{opacity:1;transform:none}}}}
.stepper{{display:flex;align-items:center;justify-content:center;margin-bottom:32px}}
.si{{display:flex;flex-direction:column;align-items:center;gap:5px}}
.sc{{width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:.75rem;font-weight:800;transition:.3s}}
.sc.active{{background:linear-gradient(135deg,var(--p),var(--p2));color:#fff;box-shadow:0 0 16px var(--glow)}}
.sc.done{{background:var(--s);color:#fff;box-shadow:0 0 12px rgba(16,185,129,.4)}}
.sc.idle{{background:rgba(255,255,255,.06);color:var(--mu);border:1px solid var(--br)}}
.sl{{font-size:.62rem;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:var(--mu)}}
.sl.active{{color:#818cf8}}.sl.done{{color:var(--s)}}
.conn{{width:44px;height:2px;background:var(--br);margin:0 4px;margin-bottom:20px;transition:.3s}}
.conn.done{{background:var(--s)}}
.logo{{width:48px;height:48px;border-radius:13px;background:linear-gradient(135deg,var(--p),var(--p2));display:flex;align-items:center;justify-content:center;margin:0 auto 18px;box-shadow:0 0 22px var(--glow)}}
h1{{font-size:1.55rem;font-weight:800;color:var(--tx);margin-bottom:5px;letter-spacing:-.02em;text-align:center}}
.sub{{color:var(--mu);font-size:.88rem;margin-bottom:24px;line-height:1.55;text-align:center}}
.view{{display:flex;flex-direction:column;animation:fi .3s ease both}}
@keyframes fi{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:none}}}}
.otp-row{{display:flex;gap:9px;justify-content:center;margin-bottom:6px}}
.ob{{width:50px;height:60px;border-radius:13px;border:2px solid var(--br);background:rgba(255,255,255,.04);color:#818cf8;font-weight:800;font-size:1.35rem;text-align:center;outline:none;transition:.2s;caret-color:var(--p);font-family:inherit}}
.ob:focus{{border-color:var(--p);background:rgba(67,97,238,.1);box-shadow:0 0 0 3px rgba(67,97,238,.2),0 0 14px rgba(67,97,238,.25)}}
.ob.filled{{border-color:rgba(129,140,248,.45);background:rgba(67,97,238,.07)}}
.rrow{{font-size:.83rem;color:var(--mu);margin-bottom:20px;text-align:center;min-height:20px}}
.rbtn{{color:var(--p);font-weight:700;cursor:pointer;background:none;border:none;font-family:inherit;font-size:inherit;padding:0;display:none}}
.field{{text-align:left;margin-bottom:16px}}
.field label{{display:block;font-size:.8rem;font-weight:700;color:var(--mu);margin-bottom:6px}}
.fw{{position:relative}}
.field input{{width:100%;padding:12px 42px 12px 13px;border-radius:11px;border:1.5px solid var(--br);background:rgba(255,255,255,.04);color:var(--tx);font-size:.93rem;font-family:inherit;outline:none;transition:.2s}}
.field input:focus{{border-color:var(--p);background:rgba(67,97,238,.07);box-shadow:0 0 0 3px rgba(67,97,238,.14)}}
.field input::placeholder{{color:rgba(148,163,184,.45)}}
.eye{{position:absolute;right:12px;top:50%;transform:translateY(-50%);cursor:pointer;color:var(--mu);background:none;border:none;font-size:.95rem;padding:0;transition:.2s}}
.eye:hover{{color:var(--tx)}}
.sbar{{height:3px;border-radius:2px;margin-top:5px;transition:all .3s;background:var(--br);width:0}}
.sbar.w{{background:#ef4444;width:25%}}.sbar.f{{background:#f59e0b;width:55%}}.sbar.g{{background:#3b82f6;width:80%}}.sbar.s{{background:var(--s);width:100%}}
.shint{{font-size:.7rem;color:var(--mu);margin-top:3px;min-height:14px}}
.err{{background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.25);color:#fca5a5;padding:9px 13px;border-radius:9px;font-size:.82rem;margin-bottom:14px;animation:shake .35s ease;display:none;text-align:left}}
@keyframes shake{{0%,100%{{transform:translateX(0)}}25%{{transform:translateX(-4px)}}75%{{transform:translateX(4px)}}}}
.btn{{width:100%;padding:14px;border-radius:13px;border:none;cursor:pointer;background:linear-gradient(135deg,var(--p),var(--p2));color:#fff;font-weight:800;font-size:.97rem;font-family:inherit;box-shadow:0 6px 18px rgba(67,97,238,.35);transition:.25s;position:relative;overflow:hidden}}
.btn::before{{content:'';position:absolute;top:0;left:-100%;width:100%;height:100%;background:linear-gradient(90deg,transparent,rgba(255,255,255,.14),transparent);transition:.5s}}
.btn:hover{{transform:translateY(-2px);box-shadow:0 10px 26px rgba(67,97,238,.45)}}.btn:hover::before{{left:100%}}
.btn:active{{transform:translateY(0)}}.btn:disabled{{opacity:.4;cursor:not-allowed;transform:none;box-shadow:none}}
.back{{display:block;text-align:center;margin-top:15px;color:var(--mu);font-size:.82rem;font-weight:600;cursor:pointer;background:none;border:none;font-family:inherit;width:100%;transition:.2s}}
.back:hover{{color:var(--tx)}}
.cring{{width:76px;height:76px;border-radius:50%;background:rgba(16,185,129,.12);border:2px solid rgba(16,185,129,.4);display:flex;align-items:center;justify-content:center;margin:0 auto 20px;animation:pop .5s cubic-bezier(.16,1,.3,1) both}}
@keyframes pop{{from{{transform:scale(0);opacity:0}}to{{transform:scale(1);opacity:1}}}}
.stitle{{font-size:1.45rem;font-weight:800;color:var(--tx);margin-bottom:7px;text-align:center}}
.ssub{{color:var(--mu);font-size:.88rem;margin-bottom:28px;line-height:1.6;text-align:center}}
.btns{{width:100%;padding:14px;border-radius:13px;border:none;cursor:pointer;background:linear-gradient(135deg,var(--s),#059669);color:#fff;font-weight:800;font-size:.97rem;font-family:inherit;box-shadow:0 6px 18px rgba(16,185,129,.3);transition:.25s}}
.btns:hover{{transform:translateY(-2px);box-shadow:0 10px 26px rgba(16,185,129,.4)}}
</style></head><body>
<div class="fullscreen">
<div class="card">
  <div class="stepper">
    <div class="si"><div class="sc {sc('otp')}">{si('otp')}</div><div class="sl {sc('otp')}">Verify</div></div>
    <div class="conn {c1}"></div>
    <div class="si"><div class="sc {sc('password')}">{si('password')}</div><div class="sl {sc('password')}">Update</div></div>
    <div class="conn {c2}"></div>
    <div class="si"><div class="sc {sc('success')}">{si('success')}</div><div class="sl {sc('success')}">Done</div></div>
  </div>
  <div class="logo"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg></div>

  <div class="view" style="display:{ov}">
    <h1>Verify Code</h1>
    <p class="sub">Enter the 6-digit code sent to<br><strong style="color:#818cf8">{email}</strong></p>
    <div class="otp-row">
      <input class="ob" type="text" maxlength="1" inputmode="numeric">
      <input class="ob" type="text" maxlength="1" inputmode="numeric">
      <input class="ob" type="text" maxlength="1" inputmode="numeric">
      <input class="ob" type="text" maxlength="1" inputmode="numeric">
      <input class="ob" type="text" maxlength="1" inputmode="numeric">
      <input class="ob" type="text" maxlength="1" inputmode="numeric">
    </div>
    <div class="rrow" id="rrow">Resend in <span id="tmr">{mm}:{ss}</span><button class="rbtn" id="rbtn">Resend Code</button></div>
    <div class="err" id="oerr">{err}</div>
    <button class="btn" id="vbtn" disabled>Verify Code</button>
    <button class="back" id="bkotp">← Back to Login</button>
  </div>

  <div class="view" style="display:{pv}">
    <h1>New Password</h1>
    <p class="sub">Choose a strong password for your account</p>
    <div class="err" id="perr">{err}</div>
    <div class="field"><label>New Password</label><div class="fw"><input type="password" id="np" placeholder="Min. 8 characters"><button class="eye" id="e1" type="button">&#128065;</button></div><div class="sbar" id="sbar"></div><div class="shint" id="shint"></div></div>
    <div class="field"><label>Confirm Password</label><div class="fw"><input type="password" id="cp" placeholder="Repeat your password"><button class="eye" id="e2" type="button">&#128065;</button></div></div>
    <button class="btn" id="ubtn">Update Password</button>
    <button class="back" id="bkpass">← Back</button>
  </div>

  <div class="view" style="display:{sv}">
    <div class="cring"><svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg></div>
    <div class="stitle">Password Updated!</div>
    <p class="ssub">Your password has been changed successfully.<br>Sign in with your new password.</p>
    <button class="btns" id="sibtn">Go to Sign In</button>
  </div>
</div>
<script>
(function(){{
  function bridge(action,fields){{
    var p=window.parent.document,ins=p.querySelectorAll('input'),btns=p.querySelectorAll('button');
    var km={{otp:'PR_OTP',np:'PR_NP',cp:'PR_CP'}};
    if(fields) Object.keys(fields).forEach(function(k){{
      for(var i=0;i<ins.length;i++){{
        var w=ins[i].closest('[data-testid="stTextInput"]');
        if(!w) continue;
        var l=w.querySelector('label');
        if(l&&l.textContent.includes(km[k])){{ins[i].value=fields[k];ins[i].dispatchEvent(new Event('input',{{bubbles:true}}));break;}}
      }}
    }});
    var lm={{verify:'PR_VERIFY',update:'PR_UPDATE',resend:'PR_RESEND',login:'PR_LOGIN'}};
    setTimeout(function(){{
      var label = lm[action];
      for(var b=0;b<btns.length;b++){{
        var p=btns[b].querySelector('p');
        var txt=p?p.textContent.trim():btns[b].innerText.trim();
        if(txt===label){{btns[b].click();break;}}
      }}
    }},160);
  }}
  var boxes=document.querySelectorAll('.ob');
  var vbtn=document.getElementById('vbtn');
  var rbtn=document.getElementById('rbtn');
  var rrow=document.getElementById('rrow');
  var oerr=document.getElementById('oerr');
  var bkotp=document.getElementById('bkotp');
  if(oerr&&oerr.textContent.trim())oerr.style.display='block';
  if(boxes.length){{
    boxes[0].focus();
    boxes.forEach(function(b,i){{
      b.oninput=function(){{
        b.value=b.value.replace(/[^0-9]/g,'');
        b.classList.toggle('filled',!!b.value);
        if(b.value&&i<5)boxes[i+1].focus();
        var full=Array.from(boxes).every(function(x){{return x.value;}});
        vbtn.disabled=!full;
        if(full){{vbtn.disabled=true;vbtn.textContent='Verifying\u2026';bridge('verify',{{otp:Array.from(boxes).map(function(x){{return x.value;}}).join('')}});}}
      }};
      b.onkeydown=function(e){{
        if(e.key==='Backspace'&&!b.value&&i>0)boxes[i-1].focus();
        if(e.key==='ArrowLeft'&&i>0)boxes[i-1].focus();
        if(e.key==='ArrowRight'&&i<5)boxes[i+1].focus();
      }};
      b.onpaste=function(e){{
        e.preventDefault();
        var t=(e.clipboardData||window.clipboardData).getData('text').replace(/[^0-9]/g,'').slice(0,6);
        t.split('').forEach(function(ch,j){{if(boxes[j]){{boxes[j].value=ch;boxes[j].classList.add('filled');}}}});
        if(t.length===6){{boxes[5].focus();vbtn.disabled=false;}}
      }};
    }});
    var rem={remaining};
    var tmr=document.getElementById('tmr');
    function tick(){{
      if(rem<=0){{if(rrow){{rrow.innerHTML='';rrow.appendChild(rbtn);rbtn.style.display='inline';}}return;}}
      if(tmr)tmr.textContent=String(Math.floor(rem/60)).padStart(2,'0')+':'+String(rem%60).padStart(2,'0');
      rem--;setTimeout(tick,1000);
    }}
    tick();
    if(rbtn)rbtn.onclick=function(){{bridge('resend');}};
    if(bkotp)bkotp.onclick=function(){{bridge('login');}};
  }}
  var np=document.getElementById('np'),cp=document.getElementById('cp');
  var ubtn=document.getElementById('ubtn'),perr=document.getElementById('perr');
  var sbar=document.getElementById('sbar'),shint=document.getElementById('shint');
  var bkpass=document.getElementById('bkpass');
  if(perr&&perr.textContent.trim())perr.style.display='block';
  if(np)np.focus();
  function strength(p){{var s=0;if(p.length>=8)s++;if(p.length>=12)s++;if(/[A-Z]/.test(p))s++;if(/[a-z]/.test(p))s++;if(/[0-9]/.test(p))s++;if(/[^A-Za-z0-9]/.test(p))s++;return s;}}
  if(np)np.oninput=function(){{var s=strength(np.value);var c=s<=1?'w':s<=3?'f':s<=4?'g':'s';var t=s<=1?'Weak':s<=3?'Fair':s<=4?'Good':'Strong';if(sbar)sbar.className='sbar '+c;if(shint)shint.textContent=np.value?t:'';}}
  var e1=document.getElementById('e1'),e2=document.getElementById('e2');
  if(e1)e1.onclick=function(){{np.type=np.type==='password'?'text':'password';e1.innerHTML=np.type==='password'?'&#128065;':'&#128584;';}};
  if(e2)e2.onclick=function(){{cp.type=cp.type==='password'?'text':'password';e2.innerHTML=cp.type==='password'?'&#128065;':'&#128584;';}};
  if(ubtn)ubtn.onclick=function(){{
    if(np.value.length<8){{perr.style.display='block';perr.textContent='\u26a0 Password must be at least 8 characters.';return;}}
    if(np.value!==cp.value){{perr.style.display='block';perr.textContent='\u26a0 Passwords do not match.';return;}}
    perr.style.display='none';ubtn.disabled=true;ubtn.textContent='Updating\u2026';
    bridge('update',{{np:np.value,cp:cp.value}});
  }};
  if(bkpass)bkpass.onclick=function(){{bridge('login');}};
  var sibtn=document.getElementById('sibtn');
  if(sibtn)sibtn.onclick=function(){{bridge('login');}};
}})();
</script></div></body></html>"""

# ══════════════════════════════════════════════════════════════════
#  USER AUTHENTICATION GATE
# ══════════════════════════════════════════════════════════════════
if not st.session_state.user_authenticated:

    # ── Query param bridges ────────────────────────────────────────
    if st.query_params.get("auth_back") == "1":
        st.query_params.clear()
        st.session_state.show_home = True
        st.rerun()

    st.markdown("""<style>
    .stApp{background:#020617!important}
    [data-testid="stSidebar"],[data-testid="stHeader"],[data-testid="stToolbar"],
    .stMainHeader,footer,#MainMenu,[data-testid="stDecoration"]{display:none!important}
    .main .block-container{padding-top:0.5rem!important}
    /* Hide bridge text inputs instantly */
    [data-testid="stTextInput"]:has(input[aria-label="OTP_BRIDGE"]),
    [data-testid="stTextInput"]:has(input[aria-label="SU_USERNAME"]),
    [data-testid="stTextInput"]:has(input[aria-label="SU_EMAIL"]),
    [data-testid="stTextInput"]:has(input[aria-label="SU_PASSWORD"]),
    [data-testid="stTextInput"]:has(input[aria-label="OTP_VALUE_BRIDGE"]),
    [data-testid="stTextInput"]:has(input[aria-label="PR_OTP"]),
    [data-testid="stTextInput"]:has(input[aria-label="PR_NP"]),
    [data-testid="stTextInput"]:has(input[aria-label="PR_CP"]),
    [data-testid="stTextInput"]:has(input[aria-label="PR_EMAIL"]) {
        position:fixed!important;left:-9999px!important;top:-9999px!important;
        width:1px!important;height:1px!important;overflow:hidden!important;opacity:0!important;
    }
    </style>""", unsafe_allow_html=True)
    col_c = st.columns([1, 2, 1])[1]
    with col_c:
        # ── Global bridge-element hider (runs on every auth mode) ─
        # Hides ALL Streamlit text inputs & buttons in the auth column
        # so only the components.html custom UI is visible.
        components.html("""
<script>
(function hideBridge(){
  var BRIDGE_INPUTS = ['SU_USERNAME','SU_EMAIL','SU_PASSWORD',
                       'OTP_VALUE_BRIDGE','PR_OTP','PR_NP','PR_CP','PR_EMAIL',
                       'OTP_BRIDGE'];
  var BRIDGE_BTNS   = ['SU_SUBMIT','SU_LOGIN',
                       'PR_SEND','PR_VERIFY','PR_UPDATE','PR_RESEND','PR_LOGIN',
                       'DO_VERIFY','DO_BACK','DO_RESEND'];
  var hide = 'position:fixed!important;left:-9999px!important;top:-9999px!important;width:1px!important;height:1px!important;overflow:hidden!important;opacity:0!important;margin:0!important;padding:0!important;pointer-events:none!important';
  function run(){
    var p = window.parent.document;
    var done = true;
    p.querySelectorAll('[data-testid="stTextInput"]').forEach(function(w){
      var lbl = w.querySelector('label');
      var txt = lbl ? lbl.textContent.trim() : '';
      if(BRIDGE_INPUTS.indexOf(txt) !== -1){ w.style.cssText = hide; }
    });
    p.querySelectorAll('[data-testid="stButton"]').forEach(function(w){
      var btn = w.querySelector('button p');
      var txt = btn ? btn.textContent.trim() : '';
      if(BRIDGE_BTNS.indexOf(txt) !== -1){ w.style.cssText = hide; }
    });
    // Keep running to catch any re-renders
    setTimeout(run, 100);
  }
  run();
})();
</script>
""", height=0)
        # ── Auth top-bar: back arrow + theme toggle ────────────────
        st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Inter:wght@400;500;600;700&display=swap');
        .auth-topbar{
          position:fixed;top:0;left:0;right:0;z-index:9999;
          display:flex;align-items:center;justify-content:space-between;
          padding:12px 28px;
          background:rgba(11,15,25,0.82);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);
          border-bottom:1px solid rgba(255,255,255,0.07);
          font-family:'Inter',sans-serif;
        }
        .auth-topbar-logo{display:flex;align-items:center;gap:9px;text-decoration:none!important}
        .auth-topbar-icon{
          width:32px;height:32px;border-radius:8px;
          background:linear-gradient(135deg,#4361EE,#7209B7);
          display:flex;align-items:center;justify-content:center;
          box-shadow:0 0 16px rgba(67,97,238,0.45);flex-shrink:0;
        }
        .auth-topbar-name{font-family:'Syne',sans-serif;font-size:1rem;font-weight:800;color:#F1F5F9}
        .auth-topbar-right{display:flex;align-items:center;gap:8px}
        .auth-back-btn{
          display:inline-flex;align-items:center;gap:6px;
          padding:7px 14px;border-radius:8px;
          border:1px solid rgba(255,255,255,0.1);
          background:rgba(255,255,255,0.05);
          color:#94A3B8;font-size:0.82rem;font-weight:600;
          text-decoration:none!important;cursor:pointer;transition:.2s;
        }
        .auth-back-btn:hover{color:#F1F5F9;background:rgba(255,255,255,0.09);border-color:rgba(255,255,255,0.2)}
        .auth-theme-btn{
          width:36px;height:36px;border-radius:8px;
          border:1px solid rgba(255,255,255,0.1);
          background:rgba(255,255,255,0.05);
          display:flex;align-items:center;justify-content:center;
          cursor:pointer;transition:.2s;flex-shrink:0;
        }
        .auth-theme-btn:hover{background:rgba(255,255,255,0.1);border-color:rgba(255,255,255,0.22)}
        /* light mode */
        body.sai-light .stApp{background:#F0F4FF!important}
        body.sai-light .auth-topbar{background:rgba(240,244,255,0.9);border-bottom-color:rgba(0,0,0,0.08)}
        body.sai-light .auth-topbar-name{color:#0F172A}
        body.sai-light .auth-back-btn{color:#475569;border-color:rgba(0,0,0,0.1);background:rgba(0,0,0,0.04)}
        body.sai-light .auth-back-btn:hover{color:#0F172A;background:rgba(0,0,0,0.07)}
        body.sai-light .auth-theme-btn{border-color:rgba(0,0,0,0.1);background:rgba(0,0,0,0.04)}
        body.sai-light .admin-login-card{background:rgba(255,255,255,0.8)!important;border-color:rgba(0,0,0,0.08)!important}
        body.sai-light .auth-form-title{color:#0F172A!important}
        body.sai-light .auth-form-subtitle{color:#64748B!important}
        body.sai-light div[data-testid="stTextInput"] input,
        body.sai-light div[data-testid="stTextArea"] textarea{
          background:#fff!important;border-color:#CBD5E1!important;color:#0F172A!important;
        }
        body.sai-light label{color:#374151!important}
        body.sai-light div.stButton>button{
          background:rgba(0,0,0,0.05)!important;border-color:rgba(0,0,0,0.1)!important;color:#374151!important;
        }
        body.sai-light div.stButton>button[kind="primary"]{
          background:linear-gradient(135deg,#4361EE,#7209B7)!important;color:#fff!important;
        }
        </style>

        <div class="auth-topbar" id="auth-topbar">
          <a class="auth-topbar-logo" href="?auth_back=1">
            <div class="auth-topbar-icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3.33 1.67 8.67 1.67 12 0v-5"/></svg>
            </div>
            <span class="auth-topbar-name">ScholarAI</span>
          </a>
          <div class="auth-topbar-right">
            <a class="auth-back-btn" href="?auth_back=1">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
              Back to Home
            </a>
            <div class="auth-theme-btn" id="sai-theme-btn" title="Toggle light / dark">
              <svg id="sai-moon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
              <svg id="sai-sun"  width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:none"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Theme toggle JS — must use components.html so script actually runs
        components.html("""
<script>
(function(){
  var body  = window.parent.document.body;
  var moon  = window.parent.document.getElementById('sai-moon');
  var sun   = window.parent.document.getElementById('sai-sun');
  var btn   = window.parent.document.getElementById('sai-theme-btn');
  var light = localStorage.getItem('sai_theme') === 'light';

  function apply(l){
    if(l){ body.classList.add('sai-light'); if(moon)moon.style.display='none'; if(sun)sun.style.display='block'; }
    else  { body.classList.remove('sai-light'); if(moon)moon.style.display='block'; if(sun)sun.style.display='none'; }
  }
  apply(light);

  function ready(){
    var b = window.parent.document.getElementById('sai-theme-btn');
    if(!b){ setTimeout(ready, 150); return; }
    b.addEventListener('click', function(){
      light = !light;
      localStorage.setItem('sai_theme', light ? 'light' : 'dark');
      apply(light);
    });
  }
  ready();
})();
</script>
""", height=0)

        # Branding
        # Only show branding card for login mode — other modes have full-screen UIs
        if st.session_state.auth_mode == "login":
            st.markdown("""
            <style>
            .auth-brand-wrap{text-align:center;margin-bottom:28px;margin-top:20px}
            .auth-brand-icon{
              width:48px;height:48px;border-radius:12px;
              background:linear-gradient(135deg,#4361EE,#7209B7);
              display:flex;align-items:center;justify-content:center;
              margin:0 auto 14px;
              box-shadow:0 0 24px rgba(67,97,238,0.4);
            }
            </style>
            <div class="admin-login-card animate-up">
              <div class="auth-brand-wrap">
                <div class="auth-brand-icon">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3.33 1.67 8.67 1.67 12 0v-5"/></svg>
                </div>
                <div class="auth-form-title">ScholarAI</div>
                <div class="auth-form-subtitle">AI-Powered Literature Reviews</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Signup — pure native Streamlit ────────────────────────
        if st.session_state.auth_mode == "signup":
            st.markdown("""<style>
            [data-testid="stSidebar"],[data-testid="stHeader"],[data-testid="stToolbar"],
            .stMainHeader,footer,#MainMenu,[data-testid="stDecoration"]{display:none!important}
            .stApp{background:#0B0F19!important}
            .main .block-container{
                padding:2rem 1rem!important;
                max-width:460px!important;
                margin:0 auto!important;
            }
            div[data-testid="stTextInput"] input{
                background:rgba(255,255,255,.05)!important;
                border:1.5px solid rgba(255,255,255,.1)!important;
                border-radius:10px!important;color:#F8FAFC!important;
                font-size:.93rem!important;
            }
            div[data-testid="stTextInput"] input:focus{
                border-color:#4361EE!important;
                box-shadow:0 0 0 3px rgba(67,97,238,.15)!important;
            }
            div[data-testid="stTextInput"] label{color:#94A3B8!important;font-size:.8rem!important;font-weight:600!important}
            div.stButton>button[kind="primary"]{
                background:linear-gradient(135deg,#4361EE,#7209B7)!important;
                border:none!important;border-radius:11px!important;
                font-weight:800!important;font-size:.95rem!important;
                box-shadow:0 6px 18px rgba(67,97,238,.35)!important;
            }
            div.stButton>button{
                background:transparent!important;
                border:1px solid rgba(255,255,255,.1)!important;
                color:#94A3B8!important;border-radius:11px!important;
            }
            p,label,.stMarkdown{color:#F8FAFC!important}
            h1,h2,h3{color:#F8FAFC!important}
            </style>""", unsafe_allow_html=True)

            # Header
            st.markdown("""
            <div style='text-align:center;margin-bottom:1.5rem;margin-top:1rem'>
              <div style='width:48px;height:48px;border-radius:13px;background:linear-gradient(135deg,#4361EE,#7209B7);
                          display:flex;align-items:center;justify-content:center;margin:0 auto 12px;
                          box-shadow:0 0 22px rgba(67,97,238,.5)'>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.2"
                     stroke-linecap="round" stroke-linejoin="round">
                  <path d="M22 10v6M2 10l10-5 10 5-10 5z"/>
                  <path d="M6 12v5c3.33 1.67 8.67 1.67 12 0v-5"/>
                </svg>
              </div>
              <h2 style='color:#F8FAFC;font-size:1.5rem;font-weight:800;margin-bottom:4px'>Create your Account</h2>
              <p style='color:#64748B;font-size:.87rem'>Start generating literature reviews for free.</p>
            </div>
            """, unsafe_allow_html=True)

            _su_err = st.session_state.get("su_error", "")
            if _su_err:
                st.error(_su_err)
                st.session_state.su_error = ""

            col1, col2 = st.columns(2)
            with col1:
                su_username = st.text_input("Username", placeholder="e.g. albert_e", key="su_username_n")
            with col2:
                su_display  = st.text_input("Display Name (optional)", placeholder="Albert Einstein", key="su_display_n")

            su_email = st.text_input("Email Address", placeholder="xyz@university.edu", key="su_email_n")
            su_pass  = st.text_input("Password", type="password",
                                     placeholder="Choose a secure password (6-50 chars)", key="su_pass_n")

            if st.button("Get Started →", key="su_submit_n", use_container_width=True, type="primary"):
                if not su_username.strip() or not su_email.strip() or not su_pass:
                    st.session_state.su_error = "Please fill in all required fields."
                elif len(su_pass) < 6:
                    st.session_state.su_error = "Password must be at least 6 characters."
                else:
                    v_code = mailer.generate_6_digit_code()
                    success, msg = db.create_user(su_username.strip(), su_email.strip(), su_pass, v_code)
                    if success:
                        # Send verification code email
                        with st.spinner("Sending verification code..."):
                            mailer.send_verification_code(su_email.strip(), v_code)
                        st.session_state.auth_username = su_username.strip()
                        st.session_state.auth_email    = su_email.strip()
                        st.session_state.auth_mode     = "verify"
                        st.session_state.last_code_sent_at = time.time()
                        st.rerun()
                    else:
                        st.session_state.su_error = msg
                st.rerun()

            st.markdown("<div style='text-align:center;margin:12px 0;color:#475569;font-size:.72rem'>OR</div>",
                        unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                if st.button("← Back to Home", key="su_home_n", use_container_width=True):
                    st.session_state.show_home = True
                    st.rerun()
            with c2:
                if st.button("Sign In", key="su_login_n", use_container_width=True):
                    st.session_state.auth_mode = "login"
                    st.rerun()

            st.markdown("<p style='text-align:center;font-size:.7rem;color:#334155;margin-top:10px'>"
                        "By signing up you agree to our Terms of Use and Privacy Policy.</p>",
                        unsafe_allow_html=True)


        # ── Verification — pure native Streamlit ──────────────────
        elif st.session_state.auth_mode == "verify":
            st.markdown("""<style>
            [data-testid="stSidebar"],[data-testid="stHeader"],[data-testid="stToolbar"],
            .stMainHeader,footer,#MainMenu,[data-testid="stDecoration"]{display:none!important}
            .stApp{background:#020617!important}
            .main .block-container{padding:2rem 1rem!important;max-width:460px!important;margin:0 auto!important}
            div[data-testid="stTextInput"] input{
                background:rgba(255,255,255,.05)!important;border:1.5px solid rgba(255,255,255,.1)!important;
                border-radius:10px!important;color:#F8FAFC!important;font-size:1.1rem!important;
                letter-spacing:.2em!important;text-align:center!important;
            }
            div[data-testid="stTextInput"] input:focus{border-color:#4361EE!important;box-shadow:0 0 0 3px rgba(67,97,238,.15)!important;}
            div[data-testid="stTextInput"] label{color:#94A3B8!important;font-size:.8rem!important;font-weight:600!important}
            div.stButton>button[kind="primary"]{background:linear-gradient(135deg,#4361EE,#7209B7)!important;border:none!important;border-radius:11px!important;font-weight:800!important;}
            div.stButton>button{background:transparent!important;border:1px solid rgba(255,255,255,.1)!important;color:#94A3B8!important;border-radius:11px!important;}
            p,label,.stMarkdown{color:#F8FAFC!important}
            </style>""", unsafe_allow_html=True)

            _em = st.session_state.get("auth_email", "")
            try:
                _at = _em.index("@")
                _masked = _em[:2] + "*" * (_at - 2) + _em[_at:]
            except Exception:
                _masked = _em

            COOLDOWN = 120
            _last = st.session_state.get("last_code_sent_at", 0)
            _rem  = max(0, int(COOLDOWN - (time.time() - _last))) if _last else 0

            st.markdown(f"""
            <div style='text-align:center;margin-bottom:1.5rem;margin-top:1rem'>
              <div style='font-size:2.5rem;margin-bottom:.5rem'>📧</div>
              <h3 style='color:#F8FAFC;margin-bottom:.3rem'>Verify Your Email</h3>
              <p style='color:#94A3B8;font-size:.88rem'>Enter the 6-digit code sent to
                <strong style='color:#818cf8'>{_masked}</strong></p>
            </div>""", unsafe_allow_html=True)

            _v_err = st.session_state.get("v_error", "")
            if _v_err:
                st.error(_v_err)
                st.session_state.v_error = ""

            v_code_in = st.text_input("6-Digit Code", placeholder="e.g. 123456",
                                      max_chars=6, key="v_code_direct")

            if st.button("Verify Account →", key="v_verify_n", use_container_width=True, type="primary"):
                user = db.get_user_by_email(_em)
                if user and user.get("verification_code") == v_code_in.strip():
                    db.update_user_verification(st.session_state.auth_username, True)
                    st.session_state.auth_mode = "login"
                    st.session_state.v_error = ""
                    st.rerun()
                else:
                    st.session_state.v_error = "Invalid code. Please check your email and try again."
                    st.rerun()

            if _rem > 0:
                st.caption(f"⏱ Resend available in {_rem // 60:02d}:{_rem % 60:02d}")
            else:
                if st.button("📧 Resend Code", key="v_resend_n", use_container_width=True):
                    v_code = mailer.generate_6_digit_code()
                    db.update_verification_code(_em, v_code)
                    import threading
                    threading.Thread(target=mailer.send_verification_code,
                                     args=(_em, v_code), daemon=True).start()
                    st.session_state.last_code_sent_at = time.time()
                    st.toast("✅ Verification code resent!")
                    st.rerun()

            if st.button("← Back to Signup", key="v_back_n", use_container_width=True):
                st.session_state.auth_mode = "signup"
                st.rerun()

        # ── Forgot Password — pure native Streamlit, no bridges ──
        elif st.session_state.auth_mode == "forgot_pass":
            if "reset_step" not in st.session_state or st.session_state.reset_step not in ("otp", "password", "success"):
                st.session_state.reset_step = "email"

            # Dark theme styling
            st.markdown("""<style>
            [data-testid="stSidebar"],[data-testid="stHeader"],[data-testid="stToolbar"],
            .stMainHeader,footer,#MainMenu{display:none!important}
            .stApp{background:#020617!important}
            .main .block-container{padding:2rem 1rem!important;max-width:480px!important;margin:0 auto!important}
            div[data-testid="stTextInput"] input{
              background:rgba(255,255,255,.05)!important;border:1.5px solid rgba(255,255,255,.1)!important;
              border-radius:10px!important;color:#F8FAFC!important;font-size:.95rem!important;
            }
            div[data-testid="stTextInput"] input:focus{border-color:#4361EE!important;box-shadow:0 0 0 3px rgba(67,97,238,.15)!important;}
            div[data-testid="stTextInput"] label{color:#94A3B8!important;font-size:.8rem!important;font-weight:600!important}
            div.stButton>button[kind="primary"]{background:linear-gradient(135deg,#4361EE,#7209B7)!important;border:none!important;border-radius:11px!important;font-weight:800!important;}
            div.stButton>button{background:transparent!important;border:1px solid rgba(255,255,255,.1)!important;color:#94A3B8!important;border-radius:11px!important;}
            p,label,.stMarkdown{color:#F8FAFC!important}
            </style>""", unsafe_allow_html=True)

            _step = st.session_state.get("reset_step", "email")
            _err  = st.session_state.get("pr_error", "")

            # ── Step indicator ─────────────────────────────────────
            s1_cls = "color:#818cf8;font-weight:800" if _step == "otp"      else ("color:#10B981" if _step in ("password","success") else "color:#475569")
            s2_cls = "color:#818cf8;font-weight:800" if _step == "password"  else ("color:#10B981" if _step == "success"              else "color:#475569")
            s3_cls = "color:#818cf8;font-weight:800" if _step == "success"   else "color:#475569"
            s1 = f"<span style='{s1_cls}'>① Verify</span>"
            s2 = f"<span style='{s2_cls}'>② Update</span>"
            s3 = f"<span style='{s3_cls}'>③ Done</span>"
            st.markdown(f"<div style='text-align:center;font-size:.85rem;margin-bottom:1rem'>{s1} &nbsp;→&nbsp; {s2} &nbsp;→&nbsp; {s3}</div>", unsafe_allow_html=True)

            if _err:
                st.error(_err)
                st.session_state.pr_error = ""

            # ── EMAIL STEP ─────────────────────────────────────────
            if _step == "email":
                st.markdown("<h3 style='color:#F8FAFC;text-align:center'>Reset Password</h3>", unsafe_allow_html=True)
                fe = st.text_input("Email Address", placeholder="e.g. user@university.edu", key="pr_email_direct")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("← Back", key="pr_back_e", use_container_width=True):
                        st.session_state.auth_mode = "login"
                        st.rerun()
                with c2:
                    if st.button("Send Code →", key="pr_send_e", use_container_width=True, type="primary"):
                        fe = fe.strip()
                        if not fe or "@" not in fe:
                            st.session_state.pr_error = "Enter a valid email address."
                        else:
                            user = db.get_user_by_email(fe)
                            if user:
                                r_code = mailer.generate_6_digit_code()
                                db.update_reset_token(fe, r_code)
                                import threading
                                threading.Thread(target=mailer.send_password_reset, args=(fe, r_code), daemon=True).start()
                                st.session_state.auth_email = fe
                                st.session_state.reset_step = "otp"
                                st.session_state.last_code_sent_at = time.time()
                            else:
                                st.session_state.pr_error = "No account found with that email."
                        st.rerun()

            # ── OTP STEP — Native Streamlit (fast & reliable) ─────
            elif _step == "otp":
                COOLDOWN = 120
                _last = st.session_state.get("last_code_sent_at", 0)
                _rem  = max(0, int(COOLDOWN - (time.time() - _last))) if _last else 0
                em = st.session_state.get("auth_email", "")
                _otp_err = st.session_state.get("pr_error", "")

                # Mask email for display
                try:
                    _at = em.index("@")
                    _masked = em[:2] + "*" * (_at - 2) + em[_at:]
                except Exception:
                    _masked = em

                st.markdown(f"""
                <div style='text-align:center;margin-bottom:1rem'>
                  <div style='font-size:2.5rem;margin-bottom:.5rem'>🔐</div>
                  <h3 style='color:#F8FAFC;margin-bottom:.3rem'>Verify Code</h3>
                  <p style='color:#94A3B8;font-size:.88rem'>Code sent to <strong style='color:#818cf8'>{_masked}</strong></p>
                </div>""", unsafe_allow_html=True)

                if _otp_err:
                    st.error(f"⚠ {_otp_err}")
                    st.session_state.pr_error = ""

                otp_in = st.text_input("Enter 6-digit code", placeholder="e.g. 123456",
                                       max_chars=6, key="pr_otp_direct",
                                       label_visibility="visible")

                c1, c2 = st.columns(2)
                with c1:
                    if st.button("← Back", key="pr_back_otp", use_container_width=True):
                        st.session_state.reset_step = "email"
                        st.rerun()
                with c2:
                    if st.button("Verify Code →", key="pr_verify_otp",
                                 use_container_width=True, type="primary"):
                        code = otp_in.strip()
                        user = db.get_user_by_email(em)
                        stored = user.get("reset_token", "") if user else ""
                        if user and stored and code == stored:
                            st.session_state.reset_step = "password"
                            st.session_state.pr_error = ""
                        else:
                            st.session_state.pr_error = "Invalid code. Please try again."
                        st.rerun()

                if _rem > 0:
                    st.caption(f"⏱ Resend available in {_rem // 60:02d}:{_rem % 60:02d}")
                else:
                    if st.button("📧 Resend Code", key="pr_resend_otp", use_container_width=True):
                        r_code = mailer.generate_6_digit_code()
                        db.update_reset_token(em, r_code)
                        import threading
                        threading.Thread(target=mailer.send_password_reset,
                                         args=(em, r_code), daemon=True).start()
                        st.session_state.last_code_sent_at = time.time()
                        st.toast("✅ New code sent!")
                        st.rerun()


            elif _step == "password":
                st.markdown("<h3 style='color:#F8FAFC;text-align:center'>New Password</h3>", unsafe_allow_html=True)
                np_val = st.text_input("New Password", type="password", placeholder="Min. 8 characters", key="pr_np_direct")
                cp_val = st.text_input("Confirm Password", type="password", placeholder="Repeat your password", key="pr_cp_direct")
                if st.button("Update Password →", key="pr_update_p", use_container_width=True, type="primary"):
                    if len(np_val) < 8:
                        st.session_state.pr_error = "Password must be at least 8 characters."
                    elif np_val != cp_val:
                        st.session_state.pr_error = "Passwords do not match."
                    else:
                        db.update_password(st.session_state.auth_email, np_val)
                        st.session_state.reset_step = "success"
                    st.rerun()

            # ── SUCCESS STEP ───────────────────────────────────────
            elif _step == "success":
                st.markdown("""
                <div style='text-align:center;padding:2rem 0'>
                  <div style='font-size:3rem;margin-bottom:1rem'>✅</div>
                  <h3 style='color:#10B981'>Password Updated!</h3>
                  <p style='color:#94A3B8'>Your password has been changed successfully.</p>
                </div>""", unsafe_allow_html=True)
                if st.button("Go to Sign In →", key="pr_signin_s", use_container_width=True, type="primary"):
                    st.session_state.auth_mode = "login"
                    st.session_state.reset_step = "email"
                    st.rerun()

        # ── Login (Default) ────────────────────────────────────────
        else:
            st.markdown('<div class="auth-form-title" style="font-size:1.3rem;">Welcome Back</div>', unsafe_allow_html=True)
            l_user = st.text_input("Username or Email", placeholder="e.g. scholar_user")
            l_pass = st.text_input("Password", type="password", placeholder="••••••••")
            remember_me = st.checkbox("Remember Me", value=True)

            # Auto-login once both fields are filled (no Enter key needed).
            creds_ready = bool(l_user.strip()) and bool(l_pass)
            creds_signature = f"{l_user.strip()}::{l_pass}"
            auto_attempt = False
            if creds_ready:
                last_sig = st.session_state.get("last_login_attempt_sig")
                if last_sig != creds_signature:
                    auto_attempt = True
                    st.session_state.last_login_attempt_sig = creds_signature

            manual_click = st.button("🚀 Sign In", type="primary", use_container_width=True)

            if manual_click or auto_attempt:
                user = db.verify_user(l_user, l_pass)
                if user:
                    if user["is_verified"]:
                        st.session_state.user_authenticated = True
                        st.session_state.username = user["username"]
                        st.session_state.auth_username = user["username"]
                        st.session_state.auth_email = user["email"]
                        st.session_state.user_tier = user.get("tier", "free")
                        
                        if remember_me:
                            # Generate a unique token
                            token = secrets.token_hex(32)
                            db.update_remember_token(user["username"], token)
                            render_remember_me_js("save", token)
                            # Reliable persistence path: keep token in URL params.
                            st.query_params["remember_token"] = token
                        else:
                            db.update_remember_token(user["username"], None)
                            st.query_params.clear()
                            
                        st.rerun()
                    else:
                        st.session_state.auth_email = user["email"]
                        st.session_state.auth_username = user["username"]
                        st.session_state.auth_mode = "verify"
                        # Auto-resend verification code so user gets it immediately
                        v_code = mailer.generate_6_digit_code()
                        db.update_verification_code(user["email"], v_code)
                        import threading
                        threading.Thread(target=mailer.send_verification_code,
                                         args=(user["email"], v_code), daemon=True).start()
                        st.session_state.last_code_sent_at = time.time()
                        st.rerun()
                else:
                    st.error("❌ Invalid login credentials.")

            col_l, col_r = st.columns(2)
            with col_l:
                if st.button("Create Account", use_container_width=True, key="go_signup"):
                    st.session_state.auth_mode = "signup"
                    st.rerun()
            with col_r:
                if st.button("Forgot Password?", use_container_width=True, key="go_forgot"):
                    st.session_state.auth_mode = "forgot_pass"
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
            st.markdown('<div class="sidebar-section-title">📜 Session History</div>',
                        unsafe_allow_html=True)
            for i, h in enumerate(reversed(st.session_state.history)):
                with st.expander(f"Review {len(st.session_state.history)-i}: {h['topic'][:30]}..."):
                    st.caption(f"Style: {h['citation_style']} · {h['word_count']} words")
                    if st.button("↩ Reload", key=f"reload_{i}"):
                        st.session_state.result = h
                        st.rerun()
            st.markdown("---")

        # ── Reset ─────────────────────────────────────────────────
        if st.button("Generate Literature Review", type="primary", use_container_width=True):
            # 💸 MONETIZATION CHECK
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
        st.caption("ScholarAI v1.0 · Powered by GPT-4o")
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
        st.caption(f"💡 {char_count}/300 chars — more detail = better review (aim for 30+ chars)")
    elif char_count < 100:
        st.caption(f"✓ {char_count}/300 chars — good topic length")
    else:
        st.caption(f"✓ {char_count}/300 chars — detailed topic")


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
    st.info(f"✓ Maximum {MAX_ARTICLES} articles uploaded. Remove one to add another.")

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
                  {info["pages"]} page(s) · {info["word_count"]:,} words ·
                  {format_bytes(art["size"])} · {estimate_read_time(info["word_count"])}
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            if st.button("✕", key=f"remove_{i}", help="Remove this article"):
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
                # Initialize direct provider client (legacy local mode)
                if active_provider == "google":
                    import google.generativeai as genai
                    genai.configure(api_key=st.session_state.gemini_api_key)
                    client = genai.GenerativeModel("gemini-1.5-flash")
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
                        import google.generativeai as genai
                        genai.configure(api_key=st.session_state.gemini_api_key)
                        fallback_client = genai.GenerativeModel("gemini-1.5-flash")
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
    f'<div class="style-confirm">📚 Citation style: <strong>{st.session_state.citation_style}</strong>'
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
    
    # 📚 MONETIZATION: Intercept free user first generation
    if generate_clicked and st.session_state.user_tier == "free" and st.session_state.user_credits >= 1:
        st.session_state.show_paywall = True
        st.rerun()
with col_regen:
    if st.session_state.result:
        regen_clicked = st.button("↺ Regenerate", use_container_width=True,
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
            import google.generativeai as genai
            genai.configure(api_key=st.session_state.gemini_api_key)
            client = genai.GenerativeModel("gemini-1.5-flash")
        else:
            from openai import OpenAI
            client = OpenAI(api_key=st.session_state.api_key)

    progress_msgs = []

    with st.status("🔬 Generating your literature review...", expanded=True) as status:
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
                    update_progress("🔐 Generated via private backend API.")
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
                    import google.generativeai as genai
                    genai.configure(api_key=st.session_state.gemini_api_key)
                    fallback_client = genai.GenerativeModel("gemini-1.5-flash")
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

            # 💸 MONETIZATION: Increment credits
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
                st.info("💡 You've hit OpenAI's rate limit. Wait 30 seconds and try again.")
            elif "api_key" in err_msg.lower() or "authentication" in err_msg.lower():
                st.info("💡 Check your API key in the sidebar — it may be invalid or expired.")
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
      <span class="pill pill-indigo">📚 {result['citation_style']}</span>
      <span class="pill pill-indigo">📄 {arts_count} article(s)</span>
      <span class="pill pill-indigo">✍️ {wc:,} words</span>
      <span class="pill pill-amber">⏱ ~{max(1, wc//200)} min read</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Source attribution ─────────────────────────────────────────
    with st.expander("🔗 Source Attribution — which articles contributed to each claim"):
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
          Topic: <span style="color:#0F172A; font-weight:600;">{result['topic']}</span> &nbsp;·&nbsp;
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
    st.markdown('<div class="download-bar-title">⬇ Download Your Review</div>',
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
                    "📄 Download PDF",
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
                    "📝 Download DOCX",
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
            "📚 References Only",
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
            "📋 Copy as Text",
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
    'ScholarAI v1.0 · Powered by OpenAI GPT-4o · '
    '<a href="/Admin_Dashboard" style="color:#4361EE;">Admin Dashboard</a>'
    '</div>',
    unsafe_allow_html=True
)
