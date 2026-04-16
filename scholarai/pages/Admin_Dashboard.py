"""
pages/Admin_Dashboard.py — ScholarAI Admin Dashboard
Password-protected analytics panel for site administrators.
"""

import os
from pathlib import Path
from datetime import datetime, timedelta

import streamlit as st
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="ScholarAI — Admin Dashboard",
    page_icon="🛡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load CSS
css_path = Path(__file__).parent.parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
import database as db

db.init_db()

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "scholarai_admin_2026")

# ══════════════════════════════════════════════════════════════════
#  LOGIN GATE
# ══════════════════════════════════════════════════════════════════
if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

if not st.session_state.admin_authenticated:
    st.markdown("<br><br>", unsafe_allow_html=True)

    col_c = st.columns([1,2,1])[1]
    with col_c:
        st.markdown("""
<div class="admin-login-card platinum-card animate-up">
<div style="text-align:center;margin-bottom:28px;">
<div style="font-size:2.5rem;margin-bottom:8px;">🛡️</div>
<div class="step-heading" style="font-size:1.8rem;">Admin Portal</div>
<div class="step-description">
ScholarAI Infrastructure Analytics
</div>
</div>
</div>
""", unsafe_allow_html=True)

        password_input = st.text_input(
            "Admin Password", type="password",
            placeholder="Enter admin password...",
        )
        if st.button("Sign In", type="primary", use_container_width=True):
            if password_input == ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("❌ Incorrect password.")

        st.caption("← [Back to ScholarAI](/) ")

    st.stop()

# ══════════════════════════════════════════════════════════════════
#  DASHBOARD — AUTHENTICATED
# ══════════════════════════════════════════════════════════════════

# ── Top bar ───────────────────────────────────────────────────────
col_title, col_logout = st.columns([5, 1])
with col_title:
    st.markdown("""
<div style="display:flex;align-items:center;gap:18px;padding:24px 0 32px;">
<div class="platinum-logo" style="width:48px; height:48px; font-size:1.5rem;">🛡️</div>
<div>
<h1 style="border:none; margin:0; padding:0; font-size:2rem;">Infrastructure Dashboard</h1>
<div style="font-size:0.85rem; color:var(--muted); margin-top:4px;">
Operational Status: <span style="color:var(--teal); font-weight:600;">ACTIVE</span> &nbsp;·&nbsp;
Last Sync: """ + datetime.now().strftime("%H:%M:%S") + """
</div>
</div>
</div>
""", unsafe_allow_html=True)
with col_logout:
    if st.button("Sign Out", use_container_width=True):
        st.session_state.admin_authenticated = False
        st.rerun()

st.markdown("---")

# ── Fetch data ────────────────────────────────────────────────────
stats        = db.get_stats()
daily_data   = db.get_reviews_per_day(days=14)
style_dist   = db.get_citation_style_dist()
format_dist  = db.get_download_format_dist()
recent       = db.get_recent_reviews(limit=20)
active_today = db.get_active_sessions_today()

# ══════════════════════════════════════════════════════════════════
#  KPI CARDS
# ══════════════════════════════════════════════════════════════════
st.markdown("### 📊 Key Performance Indicators")

k1, k2, k3 = st.columns(3)
with k1:
    st.metric("Total User Sessions", f"{stats['total_sessions']:,}",
              delta=f"{active_today} active today")
with k2:
    st.metric("Total Reviews Generated", f"{stats['total_reviews']:,}",
              delta=f"+{stats['today_reviews']} today")
with k3:
    st.metric("Reviews This Week", f"{stats['week_reviews']:,}",
              delta="Active focus")

k4, k5, k6, k7 = st.columns(4)
with k4:
    st.metric("Total Downloads", f"{stats['total_downloads']:,}")
with k5:
    st.metric("Premium Users", f"{stats['total_premium']:,}", delta="PRO Conversions")
with k6:
    st.metric("Avg Articles/Review", str(stats['avg_articles']))
with k7:
    st.metric("Avg Review Length", f"{stats['avg_words']:,} words")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════
#  AI SYNTHESIS ENGINE CONFIGURATION
# ══════════════════════════════════════════════════════════════════
st.markdown("### ⚙️ AI Synthesis Engine Configuration")

# Initialize session state variables if they don't exist
if "backend_api_url" not in st.session_state:
    st.session_state.backend_api_url = ""
if "backend_api_token" not in st.session_state:
    st.session_state.backend_api_token = ""
if "ai_provider" not in st.session_state:
    st.session_state.ai_provider = "google"
if "allow_openai_fallback" not in st.session_state:
    st.session_state.allow_openai_fallback = False

engine_col1, engine_col2 = st.columns([1, 1])

with engine_col1:
    st.markdown("#### 🔧 Backend Configuration")
    
    backend_url_input = st.text_input(
        "Private API URL (optional)",
        value=st.session_state.backend_api_url,
        placeholder="http://127.0.0.1:8000",
        help="If set, generation is routed to your own backend API.",
    )
    st.session_state.backend_api_url = backend_url_input.strip()
    
    backend_token_input = st.text_input(
        "Private API Token (optional)",
        value=st.session_state.backend_api_token,
        type="password",
        placeholder="secret-token",
    )
    st.session_state.backend_api_token = backend_token_input.strip()
    
    using_private_api = bool(st.session_state.backend_api_url)
    if using_private_api:
        st.success("🔐 Private backend enabled: provider keys are used server-side.")
    else:
        st.info("🌐 Using environment variables for API keys.")

with engine_col2:
    st.markdown("#### 🤖 Provider Settings")
    
    provider = st.radio(
        "Select AI Provider",
        ["Google Gemini (Free)", "OpenAI (Premium)"],
        index=0 if st.session_state.ai_provider == "google" else 1,
        label_visibility="collapsed"
    )
    st.session_state.ai_provider = "google" if "Gemini" in provider else "openai"
    
    # Provider-specific settings
    if using_private_api:
        st.caption("🔐 Provider keys are loaded on backend server.")
    else:
        if st.session_state.ai_provider == "google":
            st.caption("✨ Using Gemini key from environment (.env).")
            st.session_state.allow_openai_fallback = st.checkbox(
                "Fallback to OpenAI if Gemini fails",
                value=st.session_state.get("allow_openai_fallback", False),
                help="Uses OpenAI key from .env if enabled.",
            )
        else:
            st.caption("⚡ Using OpenAI key from environment (.env).")

# Status summary
st.markdown("---")
status_col1, status_col2, status_col3 = st.columns(3)

with status_col1:
    status_color = "🟢" if st.session_state.backend_api_url else "🟡"
    st.metric("Backend Status", f"{status_color} {'Private' if st.session_state.backend_api_url else 'Environment'}")

with status_col2:
    provider_icon = "🔮" if st.session_state.ai_provider == "google" else "🚀"
    st.metric("Active Provider", f"{provider_icon} {st.session_state.ai_provider.title()}")

with status_col3:
    fallback_status = "✅ Enabled" if st.session_state.get("allow_openai_fallback", False) else "❌ Disabled"
    st.metric("OpenAI Fallback", fallback_status)

# Email Testing Section
st.markdown("---")
st.markdown("### 📧 Email Configuration Test")

email_test_col1, email_test_col2 = st.columns([2, 1])

with email_test_col1:
    test_email = st.text_input(
        "Test Email Address",
        placeholder="Enter email to test configuration",
        help="Send a test email to verify SMTP settings"
    )

with email_test_col2:
    st.markdown("<br>", unsafe_allow_html=True)  # Align button with input
    if st.button("📧 Send Test Email", use_container_width=True):
        if test_email:
            import sys
            sys.path.append(str(Path(__file__).parent.parent))
            from mailer import test_email_config, send_email_with_fallback
            
            with st.spinner("Testing email configuration..."):
                # Test configuration
                config_test = test_email_config()
                
                if config_test["success"]:
                    st.success("✅ Email configuration is valid!")
                    
                    # Send test email
                    subject = "ScholarAI Email Test"
                    body = """
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                        <div style="background-color: #4361EE; padding: 20px; text-align: center; border-radius: 8px;">
                            <h1 style="color: white; margin: 0;">🎓 ScholarAI</h1>
                            <p style="color: white; margin: 5px 0 0;">Email Configuration Test</p>
                        </div>
                        <div style="background-color: white; padding: 30px; border-radius: 0 0 8px 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                            <p style="color: #333; font-size: 16px;">Hello,</p>
                            <p style="color: #333; font-size: 16px;">
                                This is a test email from ScholarAI to verify that your email configuration is working correctly.
                            </p>
                            <p style="color: #666; font-size: 14px;">
                                If you received this email, your SMTP settings are properly configured.
                            </p>
                            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                            <p style="color: #666; font-size: 14px;">
                                Best regards,<br>
                                The ScholarAI Team
                            </p>
                        </div>
                    </div>
                    """
                    
                    success, message = send_email_with_fallback(subject, test_email, body)
                    
                    if success:
                        st.success(f"✅ Test email sent successfully! {message}")
                    else:
                        st.error(f"❌ Failed to send test email: {message}")
                else:
                    st.error(f"❌ Email configuration error: {config_test['error']}")
                    st.info(f"📝 Details: {config_test['details']}")
                    if 'help' in config_test:
                        st.warning(f"💡 Help: {config_test['help']}")
        else:
            st.error("Please enter an email address to test")

with email_test_col1:
    # Show current SMTP configuration (without password)
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from mailer import get_smtp_config
    
    config = get_smtp_config()
    
    st.markdown("#### 📋 Current SMTP Configuration")
    config_info = f"""
    - **Server**: {config['server']}
    - **Port**: {config['port']}
    - **Username**: {config['user']}
    - **From Address**: {config['from']}
    - **Password**: {'✅ Configured' if config['password'] else '❌ Not set'}
    """
    
    st.markdown(config_info)
    
    if not config['user'] or not config['password']:
        st.warning("⚠️ SMTP credentials not properly configured. Please check your .env file.")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════
#  CHARTS ROW
# ══════════════════════════════════════════════════════════════════
chart_col1, chart_col2 = st.columns([2, 1])

# ── Daily reviews chart ────────────────────────────────────────────
with chart_col1:
    st.markdown("#### 📈 Reviews Generated — Last 14 Days")
    if daily_data:
        try:
            import plotly.express as px
            df_daily = pd.DataFrame(daily_data)
            df_daily["day"] = pd.to_datetime(df_daily["day"])
            fig = px.bar(
                df_daily, x="day", y="count",
                color_discrete_sequence=["#4361EE"],
                labels={"day": "Date", "count": "Reviews"},
                template="plotly_dark",
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#A8B2C3", family="DM Sans"),
                margin=dict(l=10, r=10, t=10, b=10),
                bargap=0.25,
                xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
            )
            fig.update_traces(marker_line_width=0, marker_color="#4361EE",
                               hoverlabel=dict(bgcolor="#0F2044", font_size=13))
            st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            df_daily = pd.DataFrame(daily_data).set_index("day")
            st.bar_chart(df_daily["count"])
    else:
        st.info("No review data yet — generate some reviews first!")

# ── Citation style distribution ────────────────────────────────────
with chart_col2:
    st.markdown("#### 📚 Citation Styles")
    if style_dist:
        try:
            import plotly.express as px
            df_styles = pd.DataFrame(style_dist)
            fig2 = px.pie(
                df_styles, names="citation_style", values="count",
                color_discrete_sequence=["#4361EE","#06D6A0","#F4A261",
                                          "#E9C46A","#E63946","#7209B7"],
                template="plotly_dark",
                hole=0.45,
            )
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#A8B2C3", family="DM Sans"),
                margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(font=dict(size=11)),
                showlegend=True,
            )
            fig2.update_traces(
                textposition="inside", textinfo="percent",
                hoverlabel=dict(bgcolor="#0F2044", font_size=13)
            )
            st.plotly_chart(fig2, use_container_width=True)
        except ImportError:
            for row in style_dist:
                st.write(f"{row['citation_style']}: {row['count']}")
    else:
        st.info("No style data yet.")

# ── Download formats chart ─────────────────────────────────────────
st.markdown("---")
dl_col1, dl_col2 = st.columns([1, 2])

with dl_col1:
    st.markdown("#### ⬇ Downloads by Format")
    if format_dist:
        try:
            import plotly.express as px
            df_fmt = pd.DataFrame(format_dist)
            fig3 = px.bar(
                df_fmt, x="format", y="count",
                color_discrete_sequence=["#06D6A0"],
                labels={"format": "Format", "count": "Downloads"},
                template="plotly_dark",
            )
            fig3.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#A8B2C3", family="DM Sans"),
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
            )
            st.plotly_chart(fig3, use_container_width=True)
        except ImportError:
            for row in format_dist:
                st.write(f"{row['format']}: {row['count']}")
    else:
        st.info("No downloads yet.")

# ── Summary stats panel ────────────────────────────────────────────
with dl_col2:
    st.markdown("#### 📋 Platform Summary")
    summary_data = {
        "Metric": [
            "Total Unique Sessions",
            "Active Sessions Today",
            "Reviews Generated Today",
            "Reviews This Week",
            "Total Reviews (All Time)",
            "Total Downloads",
            "Avg Articles per Review",
            "Avg Review Word Count",
        ],
        "Value": [
            f"{stats['total_sessions']:,}",
            f"{active_today:,}",
            f"{stats['today_reviews']:,}",
            f"{stats['week_reviews']:,}",
            f"{stats['total_reviews']:,}",
            f"{stats['total_downloads']:,}",
            str(stats['avg_articles']),
            f"{stats['avg_words']:,} words",
        ]
    }
    df_summary = pd.DataFrame(summary_data)
    st.dataframe(
        df_summary, use_container_width=True, hide_index=True,
        column_config={
            "Metric": st.column_config.TextColumn("Metric", width="medium"),
            "Value":  st.column_config.TextColumn("Value",  width="small"),
        }
    )

# ══════════════════════════════════════════════════════════════════
#  RECENT REVIEWS TABLE
# ══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("#### 🕐 Recent Reviews (Last 20)")

if recent:
    df_recent = pd.DataFrame(recent)
    df_recent["created_at"] = pd.to_datetime(df_recent["created_at"]).dt.strftime("%d %b %Y %H:%M")
    df_recent["topic"] = df_recent["topic"].str[:60] + "..."

    st.dataframe(
        df_recent[["id","topic","article_count","citation_style",
                   "word_count","downloads","created_at"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "id":             st.column_config.NumberColumn("ID",         width="small"),
            "topic":          st.column_config.TextColumn("Topic",        width="large"),
            "article_count":  st.column_config.NumberColumn("Articles",   width="small"),
            "citation_style": st.column_config.TextColumn("Style",        width="medium"),
            "word_count":     st.column_config.NumberColumn("Words",       width="small"),
            "downloads":      st.column_config.NumberColumn("Downloads",   width="small"),
            "created_at":     st.column_config.TextColumn("Generated At", width="medium"),
        }
    )
else:
    st.info("No reviews generated yet. Share the app with students to get started!")

# ══════════════════════════════════════════════════════════════════
#  REFRESH + NAVIGATION
# ══════════════════════════════════════════════════════════════════
st.markdown("---")
ref_col, back_col = st.columns([1, 5])
with ref_col:
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()
with back_col:
    st.markdown(
        "← [Back to ScholarAI Main App](/)",
        unsafe_allow_html=False
    )

st.markdown(
    '<div style="text-align:center;font-size:0.72rem;color:#6B7A99;margin-top:20px;">'
    f'ScholarAI Admin · Data stored locally in SQLite · Last refresh: '
    f'{datetime.now().strftime("%H:%M:%S")}</div>',
    unsafe_allow_html=True
)
