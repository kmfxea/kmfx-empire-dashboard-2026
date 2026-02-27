# main.py
# =====================================================================
# KMFX EA - PUBLIC LANDING + LOGIN PAGE
# Multi-page entry point: redirects to dashboard if logged-in
# =====================================================================

import streamlit as st
import datetime
import bcrypt
import threading
import time
import requests
import qrcode
from io import BytesIO
from supabase import create_client, Client
from dotenv import load_dotenv
import uuid
from PIL import Image
import os

from utils.supabase_client import supabase
from utils.auth import login_user, is_authenticated
from utils.helpers import (
    upload_to_supabase,
    make_same_size,
    log_action,
    start_keep_alive_if_needed
)

# Optional keep-alive
start_keep_alive_if_needed()

# ────────────────────────────────────────────────
# Determine authentication state FIRST
# ────────────────────────────────────────────────
authenticated = is_authenticated()

# ────────────────────────────────────────────────
# PAGE CONFIG - MUST be the first Streamlit command
# ────────────────────────────────────────────────
if authenticated:
    st.set_page_config(
        page_title="KMFX Empire Dashboard",
        page_icon="👑",
        layout="wide",
        initial_sidebar_state="expanded"
    )
else:
    st.set_page_config(
        page_title="KMFX EA - Elite Empire",
        page_icon="👑",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    # Modern sidebar hiding for public page
    st.markdown("""
    <style>
        [data-testid="collapsedControl"] { display: none !important; }
        section[data-testid="stSidebar"] {
            visibility: hidden !important;
            width: 0 !important;
            min-width: 0 !important;
            overflow: hidden !important;
        }
        .main .block-container {
            max-width: 1100px !important;
            margin: 0 auto !important;
            padding: 2rem 1.5rem !important;
        }
    </style>
    """, unsafe_allow_html=True)

# main.py (important snippet - add / replace in the early section)

if authenticated:
    st.switch_page("pages/🏠_Dashboard.py")
else:
    if st.session_state.pop("logging_out", False):
        msg = st.session_state.pop("logout_message", None)
        if msg:
            st.success(msg)
        # Also make sure sidebar flag is gone
        st.session_state.pop("_sidebar_rendered", None)

    # Optional: hide sidebar completely on public page
    st.markdown("""
    <style>
        section[data-testid="stSidebar"] {
            visibility: hidden !important;
            width: 0 !important;
            min-width: 0 !important;
        }
    </style>
    """, unsafe_allow_html=True)
# ────────────────────────────────────────────────
# THEME & COLORS (simplified - no forced switch)
# ────────────────────────────────────────────────
if "theme" not in st.session_state:
    st.session_state.theme = "dark" if not authenticated else "light"

theme = st.session_state.theme

accent_primary = "#00ffaa"
accent_gold   = "#ffd700"
accent_glow   = "#00ffaa40"
accent_hover  = "#00ffcc"

bg_color     = "#f8fbff" if theme == "light" else "#0a0d14"
card_bg      = "rgba(255,255,255,0.75)" if theme == "light" else "rgba(15,20,30,0.70)"
border_color = "rgba(0,0,0,0.08)"  if theme == "light" else "rgba(100,100,100,0.15)"
text_primary = "#0f172a"           if theme == "light" else "#ffffff"
text_muted   = "#64748b"           if theme == "light" else "#aaaaaa"
card_shadow  = "0 8px 25px rgba(0,0,0,0.12)" if theme == "light" else "0 10px 30px rgba(0,0,0,0.5)"
sidebar_bg   = "rgba(248,251,255,0.95)" if theme == "light" else "rgba(10,13,20,0.95)"

# ────────────────────────────────────────────────
# ELITE FULL CODE - FULLY OPTIMIZED CSS (UI/UX PRO)
# ────────────────────────────────────────────────
st.markdown(f"""
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">
<style>
    :root {{
        --accent-glow: {accent_glow if theme=='dark' else 'rgba(0,0,0,0.1)'};
        --gold-gradient: linear-gradient(135deg, #FFD700 0%, #B8860B 100%);
        --metric-white: #FFFFFF;
        /* Define maximum width for content */
        --max-app-width: 1300px; 
    }}

    /* Global Reset & Fluid Typography */
    html, body, [class*="css-"] {{
        font-family: 'Poppins', sans-serif !important;
        font-size: 16px;
        scroll-behavior: smooth;
    }}

    .stApp {{
        background: {bg_color};
        color: {text_primary};
    }}

    /* --- CENTERED LAYOUT STRATEGY (LAPTOP) --- */
    .main .block-container {{
        max-width: var(--max-app-width) !important;
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        margin: 0 auto !important; /* Forces centering */
    }}

    /* --- 3D SEPARATOR (ENGRAVED STYLE) --- */
    hr {{
        border: 0;
        height: 1px;
        background: rgba(255, 255, 255, 0.05); /* Light top edge */
        border-bottom: 1px solid rgba(0, 0, 0, 0.5); /* Dark bottom shadow */
        margin: 2.5rem 0 !important;
        box-shadow: 0px 1px 2px rgba(255, 215, 0, 0.05); /* Very subtle gold glow */
    }}

    /* --- METRIC CARDS (WHITE TEXT ENHANCEMENT) --- */
    [data-testid="stMetricLabel"] {{
        color: var(--metric-white) !important;
        font-size: clamp(0.9rem, 2vw, 1.1rem) !important;
        font-weight: 500 !important;
        letter-spacing: 1px !important;
        opacity: 0.8;
    }}

    [data-testid="stMetricValue"] {{
        color: var(--metric-white) !important;
        font-size: clamp(1.8rem, 4vw, 2.5rem) !important;
        font-weight: 700 !important;
        text-shadow: 0 0 15px rgba(255, 255, 255, 0.2);
    }}

    [data-testid="stMetric"] {{
        background: rgba(255, 255, 255, 0.04);
        padding: 1.5rem !important;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
    }}
    
    [data-testid="stMetric"]:hover {{
        transform: translateY(-5px);
        border-color: {accent_gold};
        background: rgba(255, 255, 255, 0.07);
    }}

    /* Responsiveness for Headings */
    h1 {{ font-size: clamp(2rem, 5vw, 3.5rem) !important; font-weight: 700 !important; }}
    h2 {{ font-size: clamp(1.5rem, 4vw, 2.5rem) !important; font-weight: 600 !important; }}

    /* Elite Glassmorphism Card */
    .glass-card {{
        background: {card_bg};
        backdrop-filter: blur(25px);
        -webkit-backdrop-filter: blur(25px);
        border-radius: 24px;
        border: 1px solid {border_color};
        padding: clamp(1.5rem, 5vw, 2.5rem) !important;
        box-shadow: {card_shadow};
        transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
        margin: 1.5rem auto;
        max-width: 100%; /* Will stay within the main container */
        width: 100%;
    }}

    .glass-card:hover {{
        box-shadow: 0 20px 50px var(--accent-glow);
        transform: translateY(-8px);
        border-color: {accent_primary}88;
    }}

    /* Luxury Gold Text Effect */
    .gold-text {{
        background: var(--gold-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        letter-spacing: 0.8px;
        filter: drop-shadow(0px 2px 4px rgba(0,0,0,0.3));
    }}

    /* Luxury Primary Button */
    button[kind="primary"] {{
        background: {accent_primary} !important;
        color: #000000 !important;
        border-radius: 14px !important;
        border: none !important;
        padding: 0.8rem 2.2rem !important;
        font-weight: 700 !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 15px {accent_glow} !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}

    /* Toggle & Form Button Specificity */
    button[key="lang_toggle_public"], 
    div[data-testid="stFormSubmitButton"] button {{
        background: #00ffa2 !important;
        color: #000000 !important;
    }}
    
    button[key="lang_toggle_public"] p {{
        color: #000000 !important;
    }}

    /* Sidebar & Header */
    header[data-testid="stHeader"] {{
        background-color: transparent !important;
        backdrop-filter: blur(15px);
    }}

    section[data-testid="stSidebar"] {{
        background: {sidebar_bg} !important;
        border-right: 1px solid {border_color};
    }}

    /* Mobile & Tablet Optimization Grid */
    @media (max-width: 768px) {{
        html, body {{ font-size: 14px; }}
        .glass-card {{ 
            padding: 1.2rem !important; 
            border-radius: 18px;
        }}
        [data-testid="stMetricValue"] {{ font-size: 1.8rem !important; }}
        button[kind="primary"] {{
            width: 100% !important;
            padding: 1rem !important;
        }}
        /* Remove max-width on mobile to use full screen */
        .main .block-container {{
            max-width: 100% !important;
            padding: 1rem !important;
        }}
    }}

    /* Custom Scrollbar */
    ::-webkit-scrollbar {{ width: 8px; }}
    ::-webkit-scrollbar-track {{ background: {bg_color}; }}
    ::-webkit-scrollbar-thumb {{ 
        background: {border_color}; 
        border-radius: 10px; 
    }}
    ::-webkit-scrollbar-thumb:hover {{ background: {accent_gold}; }}
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# QR AUTO-LOGIN
# ────────────────────────────────────────────────
params = st.query_params
qr_token = params.get("qr", [None])[0]

if qr_token and not authenticated:
    try:
        resp = supabase.table("users").select("*").eq("qr_token", qr_token).execute()
        if resp.data:
            user = resp.data[0]
            st.session_state.authenticated = True
            st.session_state.username      = user["username"].lower()
            st.session_state.full_name     = user["full_name"] or user["username"]
            st.session_state.role          = user["role"]
            st.session_state.theme         = "light"
            st.session_state.just_logged_in = True
            log_action("QR Login Success", f"User: {user['full_name']} | Role: {user['role']}")
            st.query_params.clear()
            st.switch_page("pages/🏠_Dashboard.py")
        else:
            st.error("Invalid or revoked QR code")
            st.query_params.clear()
    except Exception as e:
        st.error(f"QR login failed: {str(e)}")
        st.query_params.clear()

# ────────────────────────────────────────────────
# PUBLIC LANDING CONTENT (only shown if NOT authenticated)
# ────────────────────────────────────────────────
if not authenticated:
    # ── Language support (for bilingual waitlist form) ──
    if "language" not in st.session_state:
        st.session_state.language = "en"

    texts = {
        "en": {
            "join_waitlist": "Join Waitlist – Early Access",
            "name": "Full Name",
            "email": "Email",
            "why_join": "Why do you want to join KMFX? (optional)",
            "submit": "Join Waitlist 👑",
            "success": "Success! You're on the list. Check your email soon 🚀",
            # Add more keys later if you want to translate hero / other texts
        },
        "tl": {
            "join_waitlist": "Sumali sa Waitlist – Maagang Access",
            "name": "Buong Pangalan",
            "email": "Email",
            "why_join": "Bakit gusto mong sumali sa KMFX? (opsyonal)",
            "submit": "Sumali sa Waitlist 👑",
            "success": "Tagumpay! Nasa listahan ka na. Check mo ang email mo soon 🚀",
        }
    }

    def txt(key):
        # Safe fallback to English if language or key missing
        lang_dict = texts.get(st.session_state.language, texts["en"])
        return lang_dict.get(key, key)

    # Language toggle (top-right-ish)
    st.markdown('<div style="text-align: right; margin: 1rem 0;">', unsafe_allow_html=True)
    if st.button("EN / TL", key="lang_toggle_public"):
        st.session_state.language = "tl" if st.session_state.language == "en" else "en"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Logo
    logo_col = st.columns([1, 4, 1])[1]
    with logo_col:
        st.image("assets/logo.png", use_column_width=True)

    # Hero - MODIFIED
    hero_container = st.container()
    with hero_container:
        # Pinalitan natin ang class mula 'gold-text' papuntang 'brand-title'
        st.markdown(f"<h1 class='brand-title' style='text-align: center;'>KMFX EA</h1>", unsafe_allow_html=True)                
        
        st.markdown(f"<h2 style='text-align: center; color:{text_primary};'>Automated Gold Trading for Financial Freedom</h2>", unsafe_allow_html=True)                
        st.markdown(f"<p style='text-align: center; font-size:1.4rem; color:{text_muted};'>Passed FTMO Phase 1 • +3,071% 5-Year Backtest • Building Legacies of Generosity</p>", unsafe_allow_html=True)                
        st.markdown("<p style='text-align: center; font-size:1.2rem;'>Mark Jeff Blando – Founder & Developer • since 2014</p>", unsafe_allow_html=True)

    # Realtime Stats
    try:
        accounts_count = supabase.table("ftmo_accounts").select("id", count="exact").execute().count or 0
        equity_data = supabase.table("ftmo_accounts").select("current_equity").execute().data or []
        total_equity = sum(acc.get("current_equity", 0) for acc in equity_data)
        gf_data = supabase.table("growth_fund_transactions").select("type", "amount").execute().data or []
        gf_balance = sum(t["amount"] if t["type"] == "In" else -t["amount"] for t in gf_data)
        members_count = supabase.table("users").select("id", count="exact").eq("role", "client").execute().count or 0
    except Exception:
        accounts_count = total_equity = gf_balance = members_count = 0

    stat_cols = st.columns(4)
    with stat_cols[0]: st.metric("Active Accounts", accounts_count)
    with stat_cols[1]: st.metric("Total Equity", f"${total_equity:,.0f}")
    with stat_cols[2]: st.metric("Growth Fund", f"${gf_balance:,.0f}")
    with stat_cols[3]: st.metric("Members", members_count)

    # ── Live Gold Price (with better error handling) ──
    @st.cache_data(ttl=300)
    def get_gold_price():
        try:
            import yfinance as yf
            t = yf.Ticker("GC=F")
            info = t.info
            price = (
                info.get('regularMarketPrice') or
                info.get('regularMarketPreviousClose') or
                info.get('previousClose') or
                info.get('currentPrice')
            )
            ch = info.get('regularMarketChangePercent') or 0.0
            if price is None:
                hist = t.history(period="2d")
                if not hist.empty:
                    price = hist['Close'][-1]
                    prev = hist['Close'][-2] if len(hist) > 1 else price
                    ch = ((price - prev) / prev * 100) if prev else 0.0
            return round(price, 1) if price else None, round(ch, 2)
        except Exception as e:
            # Silent fallback in production
            return None, 0.0

    price, change = get_gold_price()
    if price:
        st.markdown(f"""
        <div style="text-align:center; font-size: clamp(3rem,9vw,4.5rem); font-weight:800; color:{accent_gold}; text-shadow:0 0 24px {accent_glow}; margin:2.2rem 0 0.8rem;">
            ${price:,.1f}
        </div>
        <p style="text-align:center; font-size:1.55rem; opacity:0.95;">
            <span style="color:{'#00ffaa' if change >=0 else '#ff5555'}; font-weight:700; font-size:1.65rem;">{change:+.2f}%</span>
             • Live Gold (XAU/USD) • GC=F Futures
        </p>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"<p style='text-align:center; color:{text_muted}; font-size:1.8rem;'>Gold Price (Loading or Market Closed...)</p>", unsafe_allow_html=True)

    # ── TradingView Mini Chart (fixed indentation) ──
    st.components.v1.html("""
    <div class="tradingview-widget-container" style="width:100%; height:340px; min-height:220px; max-height:380px; margin:1.8rem auto 3rem; border-radius:14px; overflow:hidden; box-shadow:0 8px 28px rgba(0,0,0,0.5); background:rgba(13,17,23,0.6);">
      <div class="tradingview-widget-container__widget"></div>
      <script type="module" src="https://widgets.tradingview-widget.com/w/en/tv-mini-chart.js" async></script>
      <tv-mini-chart symbol="OANDA:XAUUSD" color-theme="dark" locale="en" height="100%" width="100%"></tv-mini-chart>
    </div>
    """, height=420)

    # ────────────────────────────────────────────────
# WAITLIST FORM – ELITE UI/UX PORTAL
# ────────────────────────────────────────────────

# 1. Custom CSS for Form Elements (Add this to your CSS block)
st.markdown("""
<style>
    /* 1. White Background for Text Inputs (Name & Email) */
    .stTextInput input {
        background: rgba(255, 255, 255, 0.15) !important; /* White transparent */
        color: white !important;
        border: 1px solid rgba(255, 215, 0, 0.2) !important;
        border-radius: 12px !important;
        padding: 12px 15px !important;
    }

    /* 2. White Background for Text Area (Message) */
    .stTextArea textarea {
        background: rgba(255, 255, 255, 0.15) !important; /* White transparent */
        color: white !important;
        border: 1px solid rgba(255, 215, 0, 0.2) !important;
        border-radius: 12px !important;
        padding: 12px 15px !important;
    }

    /* 3. Focus State Styling */
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #FFD700 !important;
        background: rgba(255, 255, 255, 0.2) !important; /* Lighter white on focus */
        box-shadow: 0 0 10px rgba(255, 215, 0, 0.2) !important;
    }

    /* Placeholder text color */
    .stTextInput input::placeholder, .stTextArea textarea::placeholder {
        color: rgba(255, 255, 255, 0.5) !important;
    }

    /* Success Box Styling */
    .success-box {
        background: linear-gradient(135deg, rgba(0, 255, 162, 0.15) 0%, rgba(0, 255, 162, 0.08) 100%);
        border: 1px solid #00ffa2;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# 2. The Glass Card Container
st.markdown("<div class='glass-card' style='padding: clamp(1.5rem, 5vw, 3rem); border: 1px solid rgba(255,215,0,0.3); position: relative; overflow: hidden;'>", unsafe_allow_html=True)

# Subtle Background Glow for the Form
st.markdown("""
    <div style='position:absolute; top:-50px; right:-50px; width:150px; height:150px; background:rgba(255,215,0,0.1); filter:blur(50px); border-radius:50%; z-index:0;'></div>
""", unsafe_allow_html=True)

# Header Section
st.markdown(f"""
    <div style='text-align:center; position:relative; z-index:1;'>
        <h2 class='gold-text' style='margin-bottom:0.5rem;'>👑 {txt('join_waitlist')}</h2>
        <p style='color:rgba(255,255,255,0.7); font-size:1.1rem; margin-bottom:2rem; line-height:1.6; max-width:600px; margin-left:auto; margin-right:auto;'>
            Sumali sa waitlist para maunang makakuha ng access. 
            <span style='color:#FFD700; font-weight:600;'>Limited slots</span> para sa mga pioneer — be part of the empire!
        </p>
    </div>
""", unsafe_allow_html=True)

# Main Form Logic
with st.form("waitlist_form", clear_on_submit=True):
    col1, col2 = st.columns([1, 1]) # 50/50 split for balanced look
    
    with col1:
        full_name = st.text_input(
            f"👤 {txt('name')}",
            placeholder="Juan Dela Cruz",
            key="waitlist_fullname",
            help="Pwede ring nickname o full name mo lang"
        )
    
    with col2:
        email_input = st.text_input(
            f"📧 {txt('email')}",
            placeholder="your@email.com",
            key="waitlist_email",
            help="Dito namin ipapadala ang iyong private invitation."
        )
    
    message = st.text_area(
        f"🎯 {txt('why_join')}",
        height=120,
        placeholder=(
            "Halimbawa: Gusto ko sumali dahil pagod na ako sa manual trading at hanap ko na yung stable na system..."
            if st.session_state.language == "tl"
            else "Example: I'm tired of manual trading and want a stable automated system..."
        ),
        key="waitlist_message"
    )
    
    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    
    submitted = st.form_submit_button(
        f"🚀 {txt('submit').upper()}",
        type="primary",
        use_container_width=True
    )

# 3. Processing Logic (Remains similar but with UX Polish)
if submitted:
    email = email_input.strip().lower()
    full_name_clean = full_name.strip() if full_name else None
    message_clean = message.strip() if message else None

    if not email or "@" not in email:
        st.error("❌ " + ("Please enter a valid email address" if st.session_state.language == "en" else "Pakilagyan ng valid na email address"))
    else:
        with st.spinner("Authenticating your spot in the empire..."):
            try:
                data = {
                    "full_name": full_name_clean,
                    "email": email,
                    "message": message_clean,
                    "language": st.session_state.language,
                    "status": "Pending",
                    "subscribed": True
                }

                response = supabase.table("waitlist").insert(data).execute()

                if response.data:
                    # UX SUCCESS BLOCK
                    st.markdown(f"""
                        <div class='success-box'>
                            <h3 style='color:#00ffa2; margin-bottom:10px;'>MISSION SUCCESS! 👑</h3>
                            <p style='margin:0;'>Welcome to the pioneer circle, <b>{full_name_clean or 'Trader'}</b>.</p>
                            <p style='font-size:0.8rem; opacity:0.7;'>Check your inbox (and spam) for your confirmation.</p>
                        </div>
                    """, unsafe_allow_html=True)
                    st.balloons()

                    # EDGE FUNCTION INVOKE (Silent in background for cleaner UX)
                    try:
                        supabase.functions.invoke(
                            "send-waitlist-confirmation",
                            {"body": {"name": full_name_clean or "Anonymous", "email": email, "message": message_clean or "", "language": st.session_state.language}}
                        )
                    except:
                        pass # Fail silently as they are already in the DB

            except Exception as e:
                err_str = str(e).lower()
                if any(x in err_str for x in ["duplicate", "unique", "23505"]):
                    st.info("💡 " + ("You're already on the list! We'll reach out soon." if st.session_state.language == "en" else "Nasa waitlist ka na pala — salamat! Keep following lang."))
                else:
                    st.error(f"Error joining waitlist: {str(e)}")

st.markdown("</div>", unsafe_allow_html=True)


# Portfolio Story (centered)
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.markdown("<h2 class='gold-text'>Origin & Motivation (2024)</h2>", unsafe_allow_html=True)
st.write("""
Noong 2024, frustrated ako sa manual trading — paulit-ulit na losses dahil sa emotions, lack of discipline, at timing issues. Realization: "Kung hindi professional, maloloss ka lang sa market."
Decided to build my own Expert Advisor (EA) to remove human error, achieve consistency, and become a professional trader through automation.
Early inspiration from ~2016 trading days, sharing ideas with friend Ramil.
""")

st.markdown("<h2 class='gold-text'>Development Phase (2024)</h2>", unsafe_allow_html=True)
st.write("""
- Full year of self-study in MQL5 programming
- Trial-and-error: Combined multiple indicators, price action rules, risk management filters
- Hundreds of backtests, forward tests, debugging — almost 1 year of experiment before stability
""")

st.markdown("<h2 class='gold-text'>Official Launch & Early Testing (2025)</h2>", unsafe_allow_html=True)
st.write("""
- January 2025: Breakthrough — EA fully functional and running smoothly. Officially named KMFX EA
- Focused exclusively on XAUUSD (GOLD) for its volatility and opportunities
- September 2025: Formed KMFX EA TESTER group (initial: Weber — most active, Ramil, Sheldon, Jai). ~2 months forward testing with multiple trials and real-time feedback
- Late 2025 (Oct-Dec): Mastered backtesting — ran historical data from 2021–2025. Game-changer: Quickly spotted weaknesses, polished entries/exits, filters for gold spikes/news volatility
""")

st.markdown("<h2 class='gold-text'>Major Milestones & Tools (2025)</h2>", unsafe_allow_html=True)
st.write("""
- October 15, 2025: Launched sleek KMFX EA MT5 Client Tracker dashboard at kmfxea.streamlit.app — premium portal for performance tracking (owner, admin, client logins)
- December 2025: Pioneer community formed — 14 believers contributed ₱17,000 PHP (₱1,000 per unit) to fund the real challenge phase
  - Profit sharing: 30% of profits proportional to units
  - Thank you to: Mark, Jai, Doc, Weber (2 units), Don, Mark Fernandez (3 units), Ramil, Cristy, Meg, Roland, Mila, Malruz, Julius, Joshua
""")

st.markdown("<h2 class='gold-text'>FTMO Prop Firm Journey – First Attempt (Dec 2025 - Jan 2026)</h2>", unsafe_allow_html=True)
st.write("""
- December 13, 2025: Started FTMO 10K Challenge (Plan A, real evaluation)
- December 26, 2025: PASSED Phase 1 (Challenge) in just ~13 days!
  - Certificate issued: Proven profit target achieved + quality risk management
  - Stats snapshot: $10,000 → $11,040.58 (+10.41% gain), 2.98% max drawdown, 118 trades (longs only, 52% win rate), +12,810.8 pips, profit factor 1.52
  - Avg trade: 43 minutes (scalping-style on gold volatility)
""")

st.markdown("<h2 class='gold-text'>Phase 2 (Verification) Attempt</h2>", unsafe_allow_html=True)
st.write("""
- Goal: 5% profit target, same strict risk limits (5% daily / 10% overall loss)
- Outcome: Failed due to emotional intervention — shaken by market noise, manually adjusted parameters and added trades
- Key Insight: Untouched sim run (Jan 1–16, 2026) showed ~$2,000 additional gain — would have passed easily
- Big Lesson: Trust the System No Matter What. Emotions are the real enemy; the EA is solid when left alone
- Turned failure into life rebuild: Discipline, patience, surrender to God's plan — applied to trading AND personal life
""")

st.markdown("<h2 class='gold-text'>Current Attempt (Jan 2026)</h2>", unsafe_allow_html=True)
st.write("""
- New FTMO 10K Challenge (Phase 1) ongoing
- Full trust mode: 100% hands-off — no tweaks, no manual trades, pure automated execution
- Confidence: Previous pass + untouched sims prove the edge. Goal: Pass with consistency, low DD, then Verification → funded account
""")

st.markdown("<h2 class='gold-text'>Dual Product Evolution (2026)</h2>", unsafe_allow_html=True)
st.write("""
- Prop Firm Version (KMFX EA – Locked): For FTMO/challenges only — personal use, strict no-intervention during evaluations
- Personal/Client Version (in progress): Same core strategy, but client-friendly
  - Solid backtest results on historical GOLD data (consistent gains, controlled risk)
  - Future: Deployable on personal accounts, potential for clients/pioneers (with sharing or access via dashboard)
  - Advantage: Separate from prop rules — flexible for real-money growth
""")

st.markdown("<h2 class='gold-text'>Performance Proof</h2>", unsafe_allow_html=True)
st.write("""
- FTMO Phase 1 Passed: +10.41%, 2.98% max DD
- 2025 Backtest: +187.97%
- 5-Year Backtest (2021-2025): +3,071%
- Safety First: 1% risk per trade, no martingale/grid, controlled drawdown
""")

st.markdown("</div>", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# 1. THE FULL JOURNEY SECTION – COMPLETE & HEARTFELT VERSION
# ────────────────────────────────────────────────
if "show_full_journey" not in st.session_state:
    st.session_state.show_full_journey = False

st.markdown(
    "<div class='glass-card' style='text-align:center; margin:5rem auto; padding:3rem; max-width:1100px; border-radius:24px;'>",
    unsafe_allow_html=True,
)

st.markdown(
    "<h2 class='gold-text'>Want the Full Story Behind KMFX EA?</h2>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='font-size:1.4rem; opacity:0.9; line-height:1.6;'>"
    "From OFW days in Saudi Arabia to building an automated trading empire — "
    "through losses, scams, breakthroughs, faith, and unbreakable persistence.</p>",
    unsafe_allow_html=True,
)

if st.button("👑 Read My Full Trading Journey (2014–2026)", type="primary", use_container_width=True):
    st.session_state.show_full_journey = True
    st.rerun()

if st.session_state.show_full_journey:
    st.markdown(
        f"<div class='glass-card' style='padding:3rem; margin-top:2rem; border-left:6px solid {accent_gold}; border-radius:16px;'>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "<h2 class='gold-text' style='text-align:center;'>My Trading Journey: From 2014 to KMFX EA 2026</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center; font-style:italic; font-size:1.3rem; opacity:0.9;'>"
        "'Built by faith, shared for generations.'</p>",
        unsafe_allow_html=True,
    )

    # 2014: The Beginning in Saudi Arabia
    st.markdown("### 🌍 2014: The Beginning in Saudi Arabia")
    c1, c2 = st.columns(2)
    with c1: st.image("assets/saudi1.jpg", caption="Team Saudi Boys 🇸🇦", use_column_width=True)
    with c2: st.image("assets/saudi2.jpg", caption="Selfie with STC Cap", use_column_width=True)
    st.markdown("""
Noong 2014, nandoon ako sa Saudi Arabia bilang Telecom Technician sa STC. Araw-araw: trabaho sa site, init ng desert, pero tuwing Friday — off day ko — dun ko natuklasan ang Philippine stock market.

Nagbukas ako ng account sa First Metro Sec. Sobrang basic pa: buy low sell high, tips sa forums. Pero grabe ang emotions — saya kapag green, parang nanalo sa lotto! Kapag red naman, lungkot talaga, sayang ang overtime.

Around 2016, naging close friends ko sina Ramil, Mheg, at Christy. Nagsha-share kami ng stock picks at charts kahit liblib na oras. Dun nagsimula ang **team feeling** — hindi pa pro, pero may spark na na magiging pundasyon ng KMFX EA years later.
    """)

    # 2017: Umuwi sa Pinas at Crypto Era
    st.markdown("### 🏠 2017: Umuwi sa Pinas at Crypto Era")
    c3, c4 = st.columns(2)
    with c3: st.image("assets/family1.jpg", caption="Date with her ❤️", use_column_width=True)
    with c4: st.image("assets/family2.jpg", caption="Selfie My Family 👨‍👩‍👧", use_column_width=True)
    st.markdown("""
Umuwi ako sa Pinas para mag-start ng family life. Airport pickup, yakap ng pamilya — fresh start talaga.

Pero sumabay ang crypto wave! Bitcoin skyrocket, FOMO everywhere. Na-scam ako sa Auroramining, natalo sa futures dahil sa leverage at emotions. Walang solid strategy pa noon — puro gut feel.

Pero dun natuto ako ng malalim: **90% ng traders natatalo dahil sa emotions, hindi sa market.** Greed, fear, revenge trading — lahat 'yan natuto kong iwasan. Yung losses na 'yun ang naging stepping stones para matuto akong tanggalin ang emosyon sa system.
    """)

    # 2019–2021: Pandemic Days & Biggest Lesson
    st.markdown("### 🦠 2019–2021: Pandemic Days & Biggest Lesson")
    c5, c6 = st.columns(2)
    with c5: st.image("assets/klever1.jpg", caption="Max gain almost $20k+ 🔥", use_column_width=True)
    with c6: st.image("assets/klever2.jpg", caption="Klever Exchange Setup", use_column_width=True)
    st.markdown("""
Sa gitna ng quarantine, natagpuan ko ang Klever token (KLV) at 'Ninja Move' feature — automated quick flips. Sobrang laki ng gains! Feeling jackpot talaga.

Pero nung nag-crash ang BTC (60k to 20k), dun talaga bumagsak lahat. Realization: **automation + emotion control ang susi.** Hindi na pwede manual decisions kung gusto mong manalo long-term.

Kailangan ng system na tanggalin ang greed at fear. Dun nagsimula ang idea na gumawa ng sariling EA.
    """)

    # 2024–2025: The Professional Shift
    st.markdown("### 🤖 2024–2025: The Professional Shift")
    c7, c8 = st.columns(2)
    with c7: st.image("assets/ai1.jpg", caption="New Tech Found", use_column_width=True)
    with c8: st.image("assets/ai2.jpg", caption="Using Old Laptop to Build", use_column_width=True)
    st.markdown("""
Halos isang taon akong nag-self-study ng MQL5 programming. Gabi-gabi, after work at family time, nakaupo sa laptop — code, backtest, debug, ulit-ulit.

Pinagsama ko lahat ng lessons mula 2014: stock basics, crypto volatility, pandemic insights, at lahat ng sakit sa manual trading.

No Martingale, No Grid, Strict 1% Risk per trade.

**January 2025: Breakthrough!** Fully working na ang KMFX EA — focused sa Gold (XAUUSD). Agad testing kasama sina Weber, Jai, Sheldon, Ramil. Real-time results, adjustments.

End of 2025: Pioneer community formed — 14 believers, ₱17,000 initial fund. Salamat sa inyo lahat — Mark, Jai, Doc, Weber (2 units), Don, Mark Fernandez (3 units), Ramil, Cristy, Meg, Roland, Mila, Malruz, Julius, Joshua.

From hobby → passion → system → community. **Built by faith, fueled by persistence.**
    """)

    # 2025–2026: FTMO Challenges & Comeback
    st.markdown("### 🏆 2025–2026: FTMO Challenges & Comeback")
    c9, c10 = st.columns(2)
    with c9: st.image("assets/ftmo.jpeg", caption="Passed Phase 1 in 13 Days! 🎉", use_column_width=True)
    with c10: st.image("assets/ongoing.jpg", caption="100% Trust Mode 🚀", use_column_width=True)
    st.markdown("""
December 2025: Started FTMO 10K Challenge. December 26: **PASSED Phase 1 in just 13 days!**  
+10.41% gain, 2.98% max DD, 118 trades, profit factor 1.52.

Pero Phase 2: Failed dahil nag-intervene ako manually out of fear. Emotional sabotage.

Big lesson: **Trust the system 100%.** Untouched sim run would’ve passed easily.

January 2026: New challenge — **full trust mode**. No tweaks, no manual trades. Pure automation.

Ngayong 2026, focus ko: consistency, discipline, surrender. Para sa legacy at sa lahat na sumali.
    """)

    # Realization & Future Vision
    st.markdown("### ✨ Realization & Future Vision")
    st.image("assets/journey_vision.jpg", use_column_width=True, caption="Built by Faith, Shared for Generations 👑")

    st.markdown("""
Mula 2014 hanggang ngayon — lahat ng sakit, tagumpay, at aral... **hindi aksidente**.

May plano si Lord. Ang KMFX EA ay hindi lang para sa akin — para sa mga susunod na henerasyon ng Pinoy traders na ayaw na maulit ang hirap na pinagdaanan ko.

**Dream ko**:
- KMFX EA Foundations: education mula basics hanggang algo-trading
- Passive income para sa pioneers at believers
- Financial freedom — mas maraming oras sa pamilya, pananampalataya, at kapayapaan

Hindi 'to tungkol sa pera lang. Tungkol sa **legacy** — makapag-iwan ng sistema na makakatulong sa libu-libong pamilya.

**KMFX EA: Built by Faith, Tested by Fire, Shared for Generations**

— Mark Jeff Blando  
Founder & Developer | 2014–2026 👑
    """)

    if st.button("Close Journey", use_container_width=True):
        st.session_state.show_full_journey = False
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# 2. WHY CHOOSE KMFX EA? (FULL GRID)
# ────────────────────────────────────────────────
st.markdown("<h2 class='gold-text' style='text-align:center; margin-top:4rem;'>Why Choose KMFX EA?</h2>", unsafe_allow_html=True)
cols = st.columns(3)
benefits = [
    {"emoji": "👑", "title": "100% Hands-Off Automation", "desc": "Run and forget. Removes emotions completely (the #1 killer in trading)."},
    {"emoji": "📈", "title": "Gold (XAUUSD) Focused Edge", "desc": "Optimized for Gold. +3,071% 5-Year Backtest. Proven sa real FTMO challenge."},
    {"emoji": "🔒", "title": "Prop Firm Ready & Safe", "desc": "Strict no-martingale, no-grid, 1% risk per trade. FTMO-compatible logic."},
    {"emoji": "🙏", "title": "Built by Faith", "desc": "Result of 12 years of experience. Designed to help the community achieve financial freedom."},
    {"emoji": "🤝", "title": "Pioneer Community", "desc": "Early believers get proportional profit share (30% pool). Accountability group included."},
    {"emoji": "💰", "title": "Passive Income + Legacy", "desc": "Sustainable wealth for generations. More time for family, faith, and peaceful life."}
]

for i, b in enumerate(benefits):
    with cols[i % 3]:
        st.markdown(f"""
        <div class='glass-card' style='text-align:center; padding:1.5rem; margin-bottom:1rem; min-height:250px;'>
            <div style='font-size:3rem;'>{b['emoji']}</div>
            <h4 style='color:var(--gold);'>{b['title']}</h4>
            <p style='font-size:0.9rem; opacity:0.8;'>{b['desc']}</p>
        </div>
        """, unsafe_allow_html=True)

# ────────────────────────────────────────────────
# IN-DEPTH FAQs – EXECUTIVE LUXURY VERSION
# ────────────────────────────────────────────────
st.markdown(
    "<div class='glass-card' style='margin:4rem auto; padding:clamp(1.5rem, 5vw, 3.5rem); max-width:1150px;'>",
    unsafe_allow_html=True,
)

st.markdown(
    "<h2 class='gold-text' style='text-align:center; margin-bottom:1rem;'>Intelligence & Transparency: KMFX EA Deep Dive</h2>",
    unsafe_allow_html=True,
)

st.markdown(
    "<p style='text-align:center; opacity:0.8; font-size:1.1rem; max-width:800px; margin:0 auto 3rem;'>"
    "Hindi kami nagtatago sa likod ng marketing hypes. Heto ang mga teknikal na detalye at estratehiya na bumubuo sa KMFX EA system "
    "para sa mga traders na ang hanap ay long-term stability at hindi panandaliang swerte.</p>",
    unsafe_allow_html=True,
)

# Custom Styling para sa Expanders (Para sumunod sa Luxury Theme)
st.markdown("""
<style>
    .stExpander {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 215, 0, 0.1) !important;
        border-radius: 15px !important;
        margin-bottom: 1rem !important;
        transition: all 0.3s ease !important;
    }
    .stExpander:hover {
        border-color: rgba(255, 215, 0, 0.4) !important;
        background: rgba(255, 255, 255, 0.05) !important;
    }
    .faq-ans {
        line-height: 1.7;
        font-size: 1rem;
        opacity: 0.9;
        padding: 1rem;
    }
    .faq-highlight {
        color: #FFD700;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

faqs = [
    ("👑 1. Ano ang tunay na 'Edge' ng KMFX EA sa nagkalat na Gold EAs?", """
    <div class='faq-ans'>
    Karamihan ng EAs ay gumagamit ng generic indicators (RSI, EMA) na madaling mabutas sa Gold volatility. Ang edge ng KMFX EA ay ang <b>XAUUSD-Specific Volatility Mapping</b>. 
    <br><br>
    • <b>Built for Chaos:</b> Ang logic ay hango sa 2021-2025 data—panahon ng pandemic recovery, wars, at record-high gold prices.<br>
    • <b>No Blind Trading:</b> Mayroon itong 'Dynamic Filters' na nagbabasa ng momentum. Kung masyadong mabilis ang galaw (News Spike), ang EA ay naghihintay ng stability bago pumasok.<br>
    • <b>Skin in the Game:</b> Ito ay ginawa ng isang trader (Kingminted) para sa sariling fund, hindi lang ibinebenta bilang retail product.
    </div>
    """),

    ("🛡️ 2. Paano napatunayan na hindi ito 'Curve-Fitted' o swerte lang?", """
    <div class='faq-ans'>
    Ang curve-fitting ay ang pag-adjust ng settings para maganda lang tignan sa backtest. Nilabanan namin ito sa pamamagitan ng:
    <br><br>
    • <b>Walk-Forward Analysis:</b> Tinetesting ang system sa data na hindi pa nito 'nakikita' (Out-of-sample data).<br>
    • <b>Real-World Friction:</b> Ang aming 5-year backtest (+3,071%) ay may kasamang <u>realistic slippage at variable spreads</u>. <br>
    • <b>Prop Firm Validation:</b> Ang pagpasa sa <b>FTMO Phase 1 sa loob ng 13 days</b> ay patunay na ang system ay sumusunod sa strict institutional rules.
    </div>
    """),

    ("📉 3. Ano ang pinaka-malalang Drawdown (DD) na pwedeng mangyari?", """
    <div class='faq-ans'>
    Transparency is our policy. Sa pinaka-aggressive na backtest (2022 market crash), ang historical max DD ay umabot ng <span class='faq-highlight'>~12-15%</span>. 
    <br><br>
    • <b>Live Safety:</b> Sa aming conservative setup (Prop Firm settings), ang DD ay nananatiling below <b>3-5%</b>. <br>
    • <b>Recovery Logic:</b> Hindi kami gumagamit ng Martingale (double lot size). Sa halip, ang system ay gumagamit ng 'Ratio Rebalancing' kung saan unti-unting binabawi ang loss gamit ang high-probability setups.
    </div>
    """),

    ("🌪️ 4. Paano hina-handle ng EA ang 'Black Swan' events o biglang pagbabago ng market?", """
    <div class='faq-ans'>
    Ang Gold ay sensitive sa geopolitics. Ang KMFX EA ay may <b>Emergency Session Control</b>. 
    <br><br>
    • <b>Momentum Killswitch:</b> Kapag ang price movement ay lumampas sa normal ATR (Average True Range), automatic na nag-hi-hibernate ang entry logic para maiwasan ang 'catching a falling knife'.<br>
    • <b>Time Filtering:</b> Iniiwasan ang low-liquidity hours kung saan madalas ang 'stop hunt' at manipus na spreads.
    </div>
    """),

    ("🤝 5. Paano ang sistema ng pagsali at 'Profit-Sharing' model?", """
    <div class='faq-ans'>
    Hindi kami 'signal provider' lang. Kami ay isang <b>Pioneer Community</b>. 
    <br><br>
    • <b>Contribution Based:</b> Ang access ay binibigay sa mga seryosong partners na naniniwala sa long-term vision.<br>
    • <b>Shared Success:</b> May nakalaang 30% pool mula sa system profits para sa mga pioneers—ito ay para masiguro na lahat ay kumikita habang lumalaki ang ecosystem. Message admin para sa verification process.
    </div>
    """),

    ("📊 6. Bakit Gold lang? May plano ba para sa EURUSD o Crypto?", """
    <div class='faq-ans'>
    "Jack of all trades, master of none." Pinili namin ang Gold dahil ito ang may pinaka-consistent na liquidity at predictable volatility patterns para sa <b>MQL5 automation</b>. 
    <br><br>
    • <b>Focus over Breadth:</b> Mas gusto naming maging +10% monthly sa Gold nang stable, kaysa mag-trade ng 20 pairs na puro drawdown. Ang future versions ay maaaring mag-expand, pero <u>Stability First</u> lagi ang motto namin.
    </div>
    """),

    ("🔍 7. Pwede ko bang makita ang 'Live Audit' o Myfxbook ng EA?", """
    <div class='faq-ans'>
    Yes. Naniniwala kami sa <span class='faq-highlight'>Proof of Work</span>. 
    <br><br>
    • <b>Dashboard Access:</b> Ang mga members ay may access sa live metrics, FTMO certificates, at detailed trade logs sa loob ng dashboard.<br>
    • <b>Community Verification:</b> Pwede kang magtanong sa mga pioneer testers na nakakita ng performance mula Day 1.
    </div>
    """),

    ("🚪 8. Ano ang 'Exit Plan' kung sakaling mag-fail ang account?", """
    <div class='faq-ans'>
    Sa trading, risk is always present. Ang aming protection layers:
    <br><br>
    • <b>Hard Stop Loss:</b> Bawat trade ay may fixed SL. Walang trade na iniiwan na 'open-ended'.<br>
    • <b>Growth Fund Buffer:</b> Ang aming 'Growth Fund' (nakikita sa dashboard) ay nagsisilbing safety net para sa re-funding at continuous development.
    </div>
    """),

    ("🔐 9. Gaano kaseguro ang system laban sa mga 'Leakers' at Scammers?", """
    <div class='faq-ans'>
    Ang KMFX EA ay protektado ng <b>Military-Grade Encryption</b>:
    <br><br>
    • <b>Account Binding:</b> Ang EA license ay naka-lock sa iyong specific MT5 ID. Hindi ito gagana sa ibang account.<br>
    • <b>Server-Side Validation:</b> Ang system ay nag-che-check sa aming server bawat session. Kung may unauthorized attempt, automatic na mag-te-terminate ang connection.
    </div>
    """),

    ("🚀 10. Ano ang long-term legacy ng KMFX EA sa loob ng 5-10 taon?", """
    <div class='faq-ans'>
    Ang vision ni Mark Jeff Blando ay hindi lang gumawa ng software, kundi bumuo ng <b>Financial Institution</b>. 
    <br><br>
    • <b>KMFX Foundations:</b> Isang educational arm na magtuturo sa mga batang Pinoy ng tamang mindset sa algorithmic trading.<br>
    • <b>Automated Empire:</b> Ang layunin ay magkaroon ng libo-libong pamilya na nabibigyan ng passive income habang sila ay nakatutok sa kanilang pamilya at pananampalataya.
    </div>
    """),
]

for q, a in faqs:
    with st.expander(q):
        st.markdown(a, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# CUSTOM CSS FOR ELITE UI/UX LOGIN
# ────────────────────────────────────────────────
st.markdown("""
<style>
    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(0,0,0,0.2);
        padding: 10px;
        border-radius: 15px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        background-color: transparent;
        border-radius: 10px;
        color: white;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #FFD700 0%, #B8860B 100%) !important;
        color: black !important;
        box-shadow: 0px 4px 15px rgba(255, 215, 0, 0.3);
    }

    /* Login Card Container */
    .login-box {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 40px;
        border-radius: 25px;
        box-shadow: 0 25px 50px rgba(0,0,0,0.5);
        margin-top: 20px;
    }

    /* Input Fields Enhancement */
    .stTextInput input {
        background-color: rgba(0,0,0,0.3) !important;
        color: white !important;
        border: 1px solid rgba(255,215,0,0.2) !important;
        border-radius: 12px !important;
        padding: 12px !important;
        transition: all 0.3s ease;
    }
    .stTextInput input:focus {
        border-color: #FFD700 !important;
        box-shadow: 0 0 10px rgba(255,215,0,0.2) !important;
    }

    /* Luxury Button */
    .stButton button {
        background: linear-gradient(135deg, #FFD700 0%, #B8860B 100%) !important;
        color: black !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        border: none !important;
        border-radius: 12px !important;
        padding: 15px !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(255,215,0,0.4) !important;
    }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# LOGIN SECTION UI
# ────────────────────────────────────────────────
st.markdown("<div style='margin-top: 6rem;'></div>", unsafe_allow_html=True)

# Header with Glow Effect
st.markdown("""
    <div style='text-align:center;'>
        <h1 style='color: #FFD700; text-shadow: 0 0 20px rgba(255,215,0,0.5); margin-bottom:0;'>MEMBER ACCESS</h1>
        <p style='opacity:0.7; letter-spacing: 2px;'>SECURE GATEWAY TO THE EMPIRE</p>
    </div>
""", unsafe_allow_html=True)

# Main Login Container
col_l, col_mid, col_r = st.columns([1, 2, 1])

with col_mid:
    st.markdown("<div class='login-box'>", unsafe_allow_html=True)
    
    # Elegant Tabs for Roles
    tab_owner, tab_admin, tab_client = st.tabs(["👑 OWNER", "🛠️ ADMIN", "👥 CLIENT"])

    def render_elegant_login(role_label, redirect_page):
        st.markdown(f"<p style='text-align:center; font-size:0.9rem; opacity:0.6; margin-bottom:20px;'>Authorized {role_label} Entry Only</p>", unsafe_allow_html=True)
        
        with st.form(key=f"login_{role_label.lower()}"):
            user = st.text_input("Username", key=f"u_{role_label}")
            pwd = st.text_input("Password", type="password", key=f"p_{role_label}")
            
            st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
            
            submit = st.form_submit_button(f"ENTER {role_label} DASHBOARD", use_container_width=True)
            
            if submit:
                if login_user(user.strip().lower(), pwd, expected_role=role_label.lower()):
                    st.session_state.role = role_label.lower()
                    st.toast(f"Access Granted: Welcome {role_label}!", icon="👑")
                    st.switch_page(redirect_page)
                else:
                    st.error("Access Denied: Invalid Credentials")

    with tab_owner:
        render_elegant_login("Owner", "pages/👤_Admin_Management.py")
    
    with tab_admin:
        render_elegant_login("Admin", "pages/👤_Admin_Management.py")
        
    with tab_client:
        render_elegant_login("Client", "pages/🏠_Dashboard.py")

    st.markdown("</div>", unsafe_allow_html=True)

    # Footer link for support
    st.markdown("""
        <p style='text-align:center; margin-top:25px; font-size:0.8rem; opacity:0.5;'>
            Forgot access? Contact the KMFX Support Team.
        </p>
    """, unsafe_allow_html=True)

# ────────────────────────────────────────────────
# FOOTER
# ────────────────────────────────────────────────
st.markdown("---")
st.markdown(f"""
    <div style="text-align:center; padding:2rem; opacity:0.5; font-size:0.8rem; letter-spacing:1px;">
        KMFX EA VERSION 2.1 | © 2026 BUILT BY FAITH, SHARED FOR GENERATIONS
    </div>
""", unsafe_allow_html=True)

# Final Security Stop
if not is_authenticated():
    st.stop()