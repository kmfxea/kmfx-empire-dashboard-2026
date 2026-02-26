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
# FULL CSS STYLING
# ────────────────────────────────────────────────
st.markdown(f"""
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">
<style>
    html, body, [class*="css-"] {{
        font-family: 'Poppins', sans-serif !important;
        font-size: 15px !important;
    }}
    .stApp {{
        background: {bg_color};
        color: {text_primary};
    }}
    h1, h2, h3, h4, h5, h6, p, div, span, label, .stMarkdown {{
        color: {text_primary} !important;
    }}
    small, caption, .caption {{
        color: {text_muted} !important;
    }}
    .glass-card {{
        background: {card_bg};
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 20px;
        border: 1px solid {border_color};
        padding: 2.2rem !important;
        box-shadow: {card_shadow};
        transition: all 0.3s ease;
        margin: 2rem auto;
        max-width: 1100px;
    }}
    .glass-card:hover {{
        box-shadow: 0 15px 40px {accent_glow if theme=='dark' else 'rgba(0,0,0,0.2)'};
        transform: translateY(-6px);
        border-color: {accent_primary};
    }}
    .gold-text {{
        color: {accent_gold} !important;
        font-weight: 600;
        letter-spacing: 0.5px;
    }}
    /* ... rest of your CSS remains the same ... */
    button[kind="primary"] {{
        background: {accent_primary} !important;
        color: #000000 !important;
        border-radius: 16px !important;
        box-shadow: 0 6px 20px {accent_glow} !important;
        padding: 1rem 2rem !important;
        font-size: 1.2rem !important;
    }}
    button[kind="primary"]:hover {{
        background: {accent_hover} !important;
        box-shadow: 0 12px 35px {accent_glow} !important;
        transform: translateY(-3px);
    }}
    header[data-testid="stHeader"] {{
        background-color: {bg_color} !important;
        backdrop-filter: blur(20px);
    }}
    section[data-testid="stSidebar"] {{
        background: {sidebar_bg} !important;
        backdrop-filter: blur(20px);
        border-right: 1px solid {border_color};
    }}
    @media (max-width: 768px) {{
        .public-hero {{ padding: 4rem 1rem 3rem; min-height: 70vh; }}
        .glass-card {{ padding: 1.5rem !important; max-width: 95% !important; }}
    }}
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

    # Hero
    hero_container = st.container()
    with hero_container:
        st.markdown(f"<h1 class='gold-text' style='text-align: center;'>KMFX EA</h1>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='text-align: center; color:{text_primary};'>Automated Gold Trading for Financial Freedom</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; font-size:1.4rem; color:{text_muted};'>Passed FTMO Phase 1 • +3,071% 5-Year Backtest • Building Legacies of Generosity</p>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size:1.2rem;'>Mark Jeff Blando – Founder & Developer • 2026</p>", unsafe_allow_html=True)

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

    # ── Waitlist Form (FIX V2: remove special chars, debug, bilingual) ──
st.markdown("<div class='glass-card' style='padding: 2.5rem; border-radius: 24px;'>", unsafe_allow_html=True)

st.markdown(f"""
    <h2 style='text-align:center; margin-bottom:1.5rem;'>{txt('join_waitlist')}</h2>
    <p style='text-align:center; color:{text_muted}; font-size:1.1rem; margin-bottom:2rem; line-height:1.6;'>
        Sumali sa waitlist para maunang makakuha ng access kapag live na ang KMFX EA.  
        Limited spots para sa mga pioneer — be part of the journey!
    </p>
""", unsafe_allow_html=True)

with st.form("waitlist_form", clear_on_submit=True):
    col1, col2 = st.columns([1, 1.4])
    
    with col1:
        full_name = st.text_input(
            txt("name"),
            placeholder="Juan Dela Cruz" if st.session_state.language == "en" else "Juan Dela Cruz",
            key="waitlist_fullname",
            help="Pwede ring nickname o full name mo lang"
        )
    
    with col2:
        email_input = st.text_input(
            txt("email"),
            placeholder="your@email.com",
            key="waitlist_email",
            help="Ito ang email na gagamitin namin para sa updates at invitation"
        )
    
    message = st.text_area(
        txt("why_join"),
        height=140,
        placeholder=(
            "Halimbawa: Gusto ko sumali dahil pagod na ako sa manual trading at hanap ko na yung stable na system..."
            if st.session_state.language == "tl"
            else "Example: I'm tired of manual trading and want a stable automated system..."
        ),
        key="waitlist_message"
    )
    
    submitted = st.form_submit_button(
        txt("submit"),
        type="primary",
        use_container_width=True,
        help="We respect your privacy — email mo lang ang iingatan namin."
    )

if submitted:
    email = email_input.strip().lower()
    
    if not email:
        st.error("Email is required" if st.session_state.language == "en" else "Kailangan ang Email")
    elif "@" not in email or "." not in email.split("@")[-1]:
        st.error("Please enter a valid email address" if st.session_state.language == "en" else "Pakilagyan ng valid na email address")
    else:
        try:
            # Remove problematic chars completely (safest fix for now)
            import re
            safe_full_name = re.sub(r"['\"\\]", "", (full_name or "").strip()) if full_name else None
            safe_message   = re.sub(r"['\"\\]", "", (message or "").strip()) if message else None
            safe_email     = email

            # Debug info (temporary – pwede mong tanggalin later)
            st.caption(f"Debug: Sending name='{safe_full_name}', message='{safe_message[:50]}...'")

            # Insert
            supabase.table("waitlist").insert({
                "full_name": safe_full_name,
                "email": safe_email,
                "message": safe_message,
                "language": st.session_state.language,
            }).execute()

            st.success(
                "Salamat! Nasa waitlist ka na. Makakatanggap ka ng welcome email shortly 👑" 
                if st.session_state.language == "tl"
                else "Thank you! You're on the waitlist. Welcome email coming soon 👑"
            )
            st.balloons()

            st.caption(
                "Check inbox/spam for welcome email."
                if st.session_state.language == "en"
                else "Check inbox/spam para sa welcome email."
            )

        except Exception as e:
            error_text = str(e).lower()
            if "duplicate" in error_text or "unique" in error_text:
                st.info(
                    "Nasa waitlist na pala ang email mo — salamat! Keep following lang."
                    if st.session_state.language == "tl"
                    else "Already on waitlist — thank you! Stay tuned."
                )
            else:
                st.error(f"Error: {str(e)}")
                st.code(str(e), language="text")  # shows full details

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
# FULL TRADING JOURNEY EXPANDER (YOUR ORIGINAL LONG STORY – FULLY RESTORED)
# ────────────────────────────────────────────────
if "show_full_journey" not in st.session_state:
    st.session_state.show_full_journey = False

st.markdown(
    "<div class='glass-card' style='text-align:center; margin:5rem auto; padding:3rem; max-width:1100px;'>",
    unsafe_allow_html=True,
)
st.markdown(f"<h2 class='gold-text'>Want the Full Story Behind KMFX EA?</h2>", unsafe_allow_html=True)
st.markdown(
    "<p style='font-size:1.4rem; opacity:0.9;'>From OFW in Saudi to building an automated empire — built by faith, lessons, and persistence.</p>",
    unsafe_allow_html=True,
)
if st.button("👑 Read My Full Trading Journey (2014–2026)", type="primary", use_container_width=True):
    st.session_state.show_full_journey = True
    st.rerun()

if st.session_state.get("show_full_journey", False):
    st.markdown(
        "<div class='glass-card' style='padding:3rem; margin:3rem auto; max-width:1100px; border-left:6px solid {accent_gold};'>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<h2 class='gold-text' style='text-align:center;'>My Trading Journey: From 2014 to KMFX EA 2026</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center; font-style:italic; font-size:1.3rem; opacity:0.9;'>"
        "Ako si <strong>Mark Jeff Blando</strong> (Codename: <em>Kingminted</em>) — "
        "simula 2014 hanggang ngayon 2026, pinagdaanan ko ang lahat: losses, wins, scams, pandemic gains, "
        "at sa wakas, pagbuo ng sariling automated system.<br><br>"
        "Ito ang kwento ko — <strong>built by faith, shared for generations</strong>.</p>",
        unsafe_allow_html=True,
    )

    # 2014: The Beginning in Saudi Arabia
    st.markdown(
        f"<h3 style='color:{accent_gold}; text-align:center; font-size:1.8rem; margin:2rem 0;'>"
        "🌍 2014: The Beginning in Saudi Arabia</h3>",
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        resized1 = make_same_size("assets/saudi1.jpg", target_width=800, target_height=700)
        if resized1:
            st.image(resized1, use_column_width=True, caption="Team Saudi Boys 🇸🇦")
    with col2:
        resized2 = make_same_size("assets/saudi2.jpg", target_width=800, target_height=700)
        if resized2:
            st.image(resized2, use_column_width=True, caption="Selfie with STC Cap")
    st.write("""
Noong 2014, nandoon ako sa Saudi Arabia bilang Telecom Technician sa STC.
Everyday routine: work sa site, init ng desert... pero tuwing **Friday — off day ko** — may oras akong mag-explore online.
Nag-start ako mag-search ng ways para magdagdag ng income. Alam mo naman OFW life: padala sa pamilya, savings, pero gusto ko rin ng something para sa future.
Dun ko natuklasan ang **Philippine stock market**. Nagbukas ako ng account sa First Metro Sec, nag-download ng app, nagbasa ng news, PSE index... at sinubukan lahat ng basic — buy low sell high, tips sa forums, trial-and-error.
**Emotions? Grabe.** Sobrang saya kapag green — parang nanalo sa lotto! Pero kapag red? Lungkot talaga, "sayang 'yung overtime ko."
Paulit-ulit 'yun — wins, losses, lessons. Hindi pa seryoso noon, more like hobby lang habang nasa abroad... pero dun talaga nagsimula ang passion ko sa trading.
Around 2016, naging close friends ko sina Ramil, Mheg, at Christy. Nagsha-share kami ng ideas sa chat, stock picks, charts kahit liblib na oras.
Yun 'yung simula ng **"team" feeling** — hindi pa pro, pero may spark na.
*Little did I know, 'yung mga simpleng usapan na 'yun ang magiging foundation ng KMFX EA years later.*
    """)

    # 2017: Umuwi sa Pinas at Crypto Era
    st.markdown(
        f"<h3 style='color:{accent_gold}; text-align:center; font-size:1.8rem; margin:2rem 0;'>"
        "🏠 2017: Umuwi sa Pinas at Crypto Era</h3>",
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        resized1 = make_same_size("assets/family1.jpg", target_width=800, target_height=700)
        if resized1:
            st.image(resized1, use_column_width=True, caption="Date with her ❤️")
    with col2:
        resized2 = make_same_size("assets/family2.jpg", target_width=800, target_height=700)
        if resized2:
            st.image(resized2, use_column_width=True, caption="Selfie My Family 👨‍👩‍👧")
    st.write("""
Noong 2017, desisyon ko na — umuwi na ako sa Pilipinas para mag-start ng family life.
Matagal na rin akong OFW, at 30+ na si misis 😊. Gusto ko nang makasama sila araw-araw, hindi na video call lang tuwing weekend.
Yung feeling ng pagbalik? Airport pickup, yakap ng pamilya, settle sa Quezon City. **Parang fresh start** — walang desert heat, puro quality time na.
Pero dun din sumabog ang **crypto wave**! Bitcoin skyrocket hanggang ₱1M+ — grabe 'yung hype!
From stock learnings ko sa PSE, na-curious ako agad. 24/7 market kasi — mas madali mag-trade kahit busy sa bahay.
Ginamit ko 'yung basics: charts, news, patterns. Pero newbie pa rin talaga ako sa crypto.
Na-scam ako sa Auroramining (fake cloud mining). Sinubukan futures — leverage, high risk, manalo bigla tapos natatalo rin agad.
Walang solid strategy pa, walang discipline. Emosyon ang nagdedesisyon: FOMO kapag pump, panic kapag dump.
Paulit-ulit na cycle ng highs at lows... pero dun talaga natuto ako ng malalim na lessons sa volatility at risk.
Yung panahon na 'yun: mix ng saya sa family life at excitement (at sakit) sa crypto world.
Hindi pa stable, pero 'yung fire sa trading? **Lalong lumakas.**
*Little did I know, 'yung mga losses at scams na 'yun ang magiging stepping stones para sa KMFX EA — natuto akong tanggalin emotions at mag-build ng system.*
    """)

    # 2019–2021: Pandemic Days & Biggest Lesson
    st.markdown(
        f"<h3 style='color:{accent_gold}; text-align:center; font-size:1.8rem; margin:2rem 0;'>"
        "🦠 2019–2021: Pandemic Days & Biggest Lesson</h3>",
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        resized1 = make_same_size("assets/klever1.jpg", target_width=800, target_height=700)
        if resized1:
            st.image(resized1, use_column_width=True, caption="Part of Gain almost 20k$+ Max gain 🔥")
    with col2:
        resized2 = make_same_size("assets/klever2.jpg", target_width=800, target_height=700)
        if resized2:
            st.image(resized2, use_column_width=True, caption="Klever Exchange Set Buy Sell Instant")
    st.write("""
Noong 2019 hanggang 2021, dumating ang pandemic — isa sa pinakamahaba sa mundo.
Lahat kami nasa bahay, walang labas, puro quarantine.
Pero sa gitna ng gulo, natagpuan ko 'yung **Klever token (KLV)**. May feature na "Ninja Move" — set buy order tapos instant sell sa target. Parang automated quick flips.
Ginawa ko 'yun religiously — sobrang laki ng gains! Kasama ko si Michael, nag-team up kami, nag-celebrate sa chat kapag green. Feeling jackpot!
Yung bull run noon, parang lahat may pera. Sobrang saya — "finally, may solid way na 'to."
Pero bigla, glitch sa platform — half lang ng profits 'yung nabalik. Sakit sa puso 'yun.
Pero dun dumating ang **pinakamalaking realization**: May pera talaga sa market kung may right strategy + discipline + emotion control. Hindi sa luck o hype.
**90% ng traders natatalo** hindi dahil sa strategy — kundi sa emotions: greed, fear, FOMO, revenge trading.
Ako mismo, nahuhulog pa rin noon sa ganun.
After 2021 crash (BTC 60k → 20k) — market bloodbath. Dun ako nag-decide: lumayo muna, mag-reflect, mag-heal, mag-build ng matibay na foundation.
Yung pandemic days: family time sa bahay, pero dinagdagan ng market lessons na magiging key sa KMFX EA later.
*From home setups, laptop sa kama, hanggang sa pag-unawa na automation + no-emotion ang susi.*
    """)

    # 2024–2025: The Professional Shift
    st.markdown(
        f"<h3 style='color:{accent_gold}; text-align:center; font-size:1.8rem; margin:2rem 0;'>"
        "🤖 2024–2025: The Professional Shift</h3>",
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        resized1 = make_same_size("assets/ai1.jpg", target_width=800, target_height=700)
        if resized1:
            st.image(resized1, use_column_width=True, caption="New Tech Found")
    with col2:
        resized2 = make_same_size("assets/ai2.jpg", target_width=800, target_height=700)
        if resized2:
            st.image(resized2, use_column_width=True, caption="Using Old Laptop to Build")
    st.write("""
Noong 2024-2025, biglang nauso ang AI sa lahat — news, work, trading.
Nakita ko 'yung potential: bakit hindi gamitin 'yung tech para tanggalin 'yung human weaknesses? Emotions, late decisions, overtrading — lahat nawawala sa automation.
Dun ko naisip: oras na gumawa ng sariling **Expert Advisor (EA)**.
Buong halos isang taon akong nag-self-study ng **MQL5 programming**. Gabi-gabi, after work at family time — nakaupo sa laptop, nagbabasa, nanonood tutorials, nagko-code, nagde-debug.
Pinagsama ko lahat ng natutunan mula 2014: stock basics, crypto volatility, pandemic lessons, Klever moves, at lahat ng sakit sa manual trading.
Narealize ko 'yung **formula ng professional trader**:
- Solid strategy (entries, exits, indicators)
- Iron-clad risk management (1% risk per trade, no martingale)
- Psychology — discipline, patience, trust the system
Goal ko: maging ganun — hindi na trial-and-error trader, kundi consistent, emotion-free pro.
**January 2025: Breakthrough!** Fully working na 'yung KMFX EA — focused sa Gold (XAUUSD).
Agad testing kasama sina Weber (super active), Jai, Sheldon, Ramil. Real-time results, adjustments.
End of 2025: Pioneer community formed — mga believers na sumali at naging part ng journey.
*Parang rebirth. Mula sa losses dati, hanggang sa tool na makakatulong sa marami. Built by faith, fueled by persistence.*
    """)

    # 2025–2026: FTMO Challenges & Comeback
    st.markdown(
        f"<h3 style='color:{accent_gold}; text-align:center; font-size:1.8rem; margin:2rem 0;'>"
        "🏆 2025–2026: FTMO Challenges & Comeback</h3>",
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        resized1 = make_same_size("assets/ftmo.jpeg", target_width=800, target_height=700)
        if resized1:
            st.image(resized1, use_column_width=True, caption="Passed Phase 1 in 13 days! 🎉")
    with col2:
        resized2 = make_same_size("assets/ongoing.jpg", target_width=800, target_height=700)
        if resized2:
            st.image(resized2, use_column_width=True, caption="Current challenge - full trust mode 🚀")
    st.write("""
First Taste of Pro Validation – Then the Hard Reset
End of 2025 hanggang 2026: pinaka-exciting at challenging phase.
After 1 year ng building at testing, ready na subukan sa **FTMO** — goal: funded account, live market proof.
December 13, 2025: Start ng first 10K Challenge.
December 26, 2025: **PASSED Phase 1 in 13 days!** +10.41% gain, 2.98% max DD.
Stats:
- $10,000 → $11,040.58
- 118 trades (longs only)
- 52% win rate, +12,810 pips
- Profit factor 1.52
- Avg duration ~43 minutes
"Yes, it works!" moment — share agad sa group, salamat sa testers.
Pero Phase 2: Failed — emotional intervention. Nag-adjust manually out of fear.
Key insight: Untouched sim run = +$2,000 more — madali sanang na-pass.
**Big lesson**: Emotions ang tunay na kalaban. Full trust lang — run and forget mode. Surrender sa process, tulad ng surrender sa God's plan.
January 2026: New challenge — 100% hands-off, pure automated.
Confidence high. Comeback stronger — para sa legacy, community, financial freedom.
*Built by faith, tested by fire.*
    """)

    # Realization & Future Vision – FULL SIZE, NO CROP
    st.markdown(
        f"<h3 style='color:{accent_gold}; text-align:center; font-size:1.8rem; margin:2rem 0;'>"
        "✨ Realization & Future Vision</h3>",
        unsafe_allow_html=True,
    )
    try:
        vision_image = Image.open("assets/journey_vision.jpg")
        st.image(
            vision_image,
            use_column_width=True,
            caption="Built by Faith, Shared for Generations 👑"
        )
    except Exception as e:
        st.warning(f"Vision image not found or failed to load: {str(e)}")
        st.info("Image: assets/journey_vision.jpg")

    st.write("""
Mula noong 2014, ramdam na ramdam ko na may malaking plano si Lord para sa akin.
Hindi aksidente 'yung involvement ko sa market — stocks, crypto, gold, highs at lows.
Lahat ng losses, scams, emotional rollercoasters, pandemic gains, FTMO failures... part ng preparation.
Purpose ko na 'to — hindi lang para sa sarili ko, kundi para makatulong sa marami na nahihirapan pero may pangarap na financially free.
Kaya binuo ko ang **KMFX EA** — tool na tanggalin ang human error, bigyan ng consistency, at patunayan na kaya maging pro trader kahit nagsimula sa zero.
*Built by faith, tested by fire, ready na ibahagi.*
**Dream ko ngayon**:
- KMFX EA Foundations — full guide mula basics hanggang pro level
- Para maiwasan ng baguhan ang sakit ng ulo na pinagdaanan ko
- Passive income para sa lahat na sumali at naniwala
- Financial freedom — mas maraming oras sa Panginoon, pamilya, peaceful life
Hindi 'to tungkol sa pera lang. Tungkol sa **legacy** — makapag-iwan ng something na makakatulong sa susunod na henerasyon.
Na patunayan na kapag may faith, discipline, at tamang system — kaya baguhin ang buhay.
**KMFX EA: Built by Faith, Shared for Generations**
— Mark Jeff Blando | Founder & Developer | 2014 hanggang ngayon 👑
    """)

    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("Close Journey", use_container_width=True):
        st.session_state.show_full_journey = False
        st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# WHY CHOOSE KMFX EA? (FULL GRID – RESTORED)
# ────────────────────────────────────────────────
st.markdown(
    "<div class='glass-card' style='margin:4rem auto; padding:3rem; max-width:1100px;'>",
    unsafe_allow_html=True,
)
st.markdown(
    "<h2 class='gold-text' style='text-align:center;'>Why Choose KMFX EA?</h2>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align:center; opacity:0.9; font-size:1.3rem; margin-bottom:3rem;'>"
    "Hindi lang isa pang EA — ito ang automated system na galing sa totoong 12+ years journey, "
    "pinatunayan sa FTMO, at ginawa with discipline, persistence, at faith.</p>",
    unsafe_allow_html=True,
)

cols = st.columns(3)
benefits = [
    {"emoji": "👑", "title": "100% Hands-Off Automation", "points": [
        "Run and forget — walang kailangang galawin pag naka-set na",
        "Removes emotions completely (yung pinakamalaking killer sa trading)",
        "Pure MQL5 logic + strict risk rules = consistent execution"
    ]},
    {"emoji": "📈", "title": "Gold (XAUUSD) Focused Edge", "points": [
        "Optimized for Gold volatility — best market para sa scalping & swing",
        "+3,071% 5-Year Backtest • +187% 2025 • Low DD <3%",
        "Proven sa real FTMO challenge (Phase 1 passed in 13 days!)"
    ]},
    {"emoji": "🔒", "title": "Prop Firm Ready & Safe", "points": [
        "FTMO-compatible — strict no-martingale, no-grid, 1% risk per trade",
        "Locked version para sa challenges • Flexible personal version",
        "Full transparency: journey, stats, at community pioneer sharing"
    ]},
    {"emoji": "🙏", "title": "Built by Faith & Real Experience", "points": [
        "Galing sa 12 taon na totoong trading journey (2014 hanggang 2026)",
        "Hindi basta code — may purpose: tulungan ang marami sa financial freedom",
        "Discipline + surrender to God's plan = sustainable success"
    ]},
    {"emoji": "🤝", "title": "Pioneer Community & Sharing", "points": [
        "Early believers get proportional profit share (30% pool)",
        "Real accountability group — testers, pioneers, at future foundation",
        "Hindi solo — sama-sama tayo sa pag-scale ng empire"
    ]},
    {"emoji": "💰", "title": "Passive Income + Legacy Vision", "points": [
        "Goal: true passive income para mas maraming time sa pamilya at Lord",
        "Dream: KMFX EA Foundations — turuan ang aspiring traders maging pro",
        "Built by faith, shared for generations — legacy na hindi matitigil"
    ]}
]

for i, benefit in enumerate(benefits):
    with cols[i % 3]:
        st.markdown(
            f"""
            <div style='text-align:center; padding:1.5rem;'>
                <div style='font-size:3.5rem; margin-bottom:1rem;'>{benefit['emoji']}</div>
                <h4 style='color:{accent_gold}; margin:0.8rem 0; font-size:1.3rem;'>{benefit['title']}</h4>
                <ul style='text-align:left; padding-left:1.5rem; margin:0; opacity:0.9;'>
                    {''.join(f'<li style="margin:0.5rem 0; line-height:1.5;">{p}</li>' for p in benefit['points'])}
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("</div>", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# IN-DEPTH FAQs – RESTORED
# ────────────────────────────────────────────────
st.markdown(
    "<div class='glass-card' style='margin:4rem auto; padding:3rem; max-width:1100px;'>",
    unsafe_allow_html=True,
)
st.markdown(
    "<h2 class='gold-text' style='text-align:center;'>In-Depth Questions About KMFX EA</h2>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align:center; opacity:0.9; font-size:1.2rem; margin-bottom:2.5rem;'>"
    "Diretsong sagot sa mga tanong na tinatanong ng mga seryosong traders — walang paligoy-ligoy, puro facts at transparency.</p>",
    unsafe_allow_html=True,
)

faqs = [
    ("1. Ano ang edge ng KMFX EA kumpara sa ibang Gold EAs sa market?", """
- Tunay na focused sa XAUUSD volatility patterns na pinag-aralan mula 2021–2025 backtests
- Walang over-optimization — daan-daang forward tests + real FTMO challenge proof
- 1% strict risk + dynamic filters para sa news spikes (hindi basta indicator-based)
- Galing sa 12 taon na personal trading journey, hindi copy-paste o generic code
    """),
    ("2. Paano n'yo napatunayan na hindi overfitted yung strategy?", """
- 5-Year Backtest (2021–2025): +3,071% na may realistic slippage & spread
- Out-of-sample forward testing 2025: consistent gains sa live-like conditions
- Real FTMO Phase 1 pass (13 days, +10.41%, 2.98% DD) — hindi lang curve-fitted
- Strict walk-forward validation, walang look-ahead bias o magic parameters
    """),
    ("3. Ano ang worst-case drawdown scenario base sa history?", """
- Max historical DD sa backtest: ~12–15% sa malalakas na Gold crashes (2022 bear market)
- Real FTMO run: 2.98% max DD lang (conservative live settings)
- Built-in recovery filters: kung tumaas ang DD, nagti-tighten ang entries
- Designed para tumagal — hindi blow-up kahit sa prolonged sideways o volatility spikes
    """),
    ("4. Paano kung magbago ang market behavior ng Gold?", """
- May adaptive filters (news volatility, session checks, momentum rules)
- Regular forward testing at community feedback para ma-spot agad ang weaknesses
- Hindi static — pinagsama price action + risk management na flexible sa conditions
- Long-term: future updates may mas advanced adaptation (pero priority muna stability)
    """),
    ("5. Paano sumali o makakuha ng access sa KMFX EA?", """
- Available sa community members at trusted users na sumali sa vision
- May profit-sharing model base sa contribution at participation
- Para sa interesadong sumali: message sa group o admin para sa details at verification
- Goal: i-scale responsibly para mapanatili ang performance at transparency
    """),
    ("6. May plan ba kayo magdagdag ng ibang pairs (EURUSD, indices, crypto)?", """
- Sa ngayon: Gold lang muna para focused at optimized (pinakamagandang results)
- Future versions: possible multi-pair pag na-master na ang Gold edge
- Priority: stability at low drawdown kaysa magmadali sa maraming instruments
    """),
    ("7. Paano kung gusto kong i-backtest o i-verify mismo yung performance?", """
- Pwede — may documented stats, sample reports, at live metrics sa dashboard
- FTMO Phase 1 certificate + backtest summary visible sa community
- Hindi full code release (security), pero transparent sa key performance data
- Sumali sa community para makita real-time results sa actual accounts
    """),
    ("8. Ano ang exit strategy kung biglang magbago ang market o mag-fail?", """
- Auto DD limits + manual override option (pero recommended wag gamitin sa live)
- Growth Fund buffer para sa reinvestment sa new challenges kung kailangan
- Community feedback loop — kung consistent na underperform, titigil o i-a-adjust
- Long-term mindset: sustainable passive income, hindi get-rich-quick
    """),
    ("9. Paano nyo pinoprotektahan ang system laban sa copy-paste o piracy?", """
- Encrypted license key (XOR + unique per user/account)
- MT5 login binding option para ma-lock sa specific accounts
- Revoke capability kung may violation o unauthorized use
- Community-first approach: trusted users muna para mapanatili ang integrity
    """),
    ("10. Ano ang ultimate vision mo para sa KMFX EA sa susunod na 5–10 taon?", """
- Build KMFX EA Foundations: education at tools para sa aspiring Pinoy traders
- Scale sa multiple funded accounts + real personal at community portfolios
- Create legacy: passive income para sa marami, mas maraming oras sa pamilya at pananampalataya
- Patunayan na possible ang consistent trading gamit discipline, automation, at God's plan
    """)
]

for q, a in faqs:
    with st.expander(q):
        st.write(a)

st.markdown("</div>", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# SECURE MEMBER LOGIN – ROLE-AWARE + FIXED REDIRECTS
# ────────────────────────────────────────────────
st.markdown("<div class='glass-card' style='text-align:center; margin:5rem auto; padding:4rem; max-width:800px;'>", unsafe_allow_html=True)
st.markdown("<h2 class='gold-text'>Already a Pioneer or Member?</h2>", unsafe_allow_html=True)
st.markdown("<p style='font-size:1.4rem; opacity:0.9;'>Access your elite dashboard, realtime balance, profit shares, EA versions, and empire tools</p>", unsafe_allow_html=True)

tab_owner, tab_admin, tab_client = st.tabs(["👑 Owner Login", "🛠️ Admin Login", "👥 Client Login"])

# ── OWNER ────────────────────────────────────────
with tab_owner:
    with st.form(key="owner_login_form", clear_on_submit=True):
        st.markdown("<p style='text-align:center; opacity:0.8;'>Owner-only access</p>", unsafe_allow_html=True)
        owner_username = st.text_input("Username", placeholder="e.g. kingminted", key="owner_username")
        owner_password = st.text_input("Password", type="password", key="owner_password")
        submit_owner = st.form_submit_button("Login as Owner →", type="primary", use_container_width=True)

    if submit_owner:
        success = login_user(owner_username.strip().lower(), owner_password, expected_role="owner")
        if success:
            st.success("Owner login successful! Redirecting...")
            st.session_state.role = "owner"
            # time.sleep(0.8)  # uncomment if you want a small delay to see message
            st.switch_page("pages/👤_Admin_Management.py")  # Owner starts here
        else:
            st.error("Login failed – check credentials or role")

# ── ADMIN ────────────────────────────────────────
with tab_admin:
    with st.form(key="admin_login_form", clear_on_submit=True):
        st.markdown("<p style='text-align:center; opacity:0.8;'>Admin access</p>", unsafe_allow_html=True)
        admin_username = st.text_input("Username", placeholder="Your admin username", key="admin_username")
        admin_password = st.text_input("Password", type="password", key="admin_password")
        submit_admin = st.form_submit_button("Login as Admin →", type="primary", use_container_width=True)

    if submit_admin:
        success = login_user(admin_username.strip().lower(), admin_password, expected_role="admin")
        if success:
            st.success("Admin login successful! Redirecting...")
            st.session_state.role = "admin"
            # time.sleep(0.8)
            st.switch_page("pages/👤_Admin_Management.py")  # Admin starts here
        else:
            st.error("Login failed – check credentials or role")

# ── CLIENT / PIONEER ─────────────────────────────
with tab_client:
    with st.form(key="client_login_form", clear_on_submit=True):
        st.markdown("<p style='text-align:center; opacity:0.8;'>Client / Pioneer access</p>", unsafe_allow_html=True)
        client_username = st.text_input("Username", placeholder="Your username", key="client_username")
        client_password = st.text_input("Password", type="password", key="client_password")
        submit_client = st.form_submit_button("Login as Client →", type="primary", use_container_width=True)

    if submit_client:
        success = login_user(client_username.strip().lower(), client_password, expected_role="client")
        if success:
            st.success("Welcome back! Redirecting to your dashboard...")
            st.session_state.role = "client"
            # time.sleep(0.8)
            st.switch_page("pages/🏠_Dashboard.py")  # ← FIXED HERE (correct path)
        else:
            st.error("Login failed – check credentials or role")

st.markdown("</div>", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# STOP IF NOT AUTHENTICATED
# ────────────────────────────────────────────────
if not is_authenticated():
    st.stop()