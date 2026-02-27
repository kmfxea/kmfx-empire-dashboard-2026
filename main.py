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
# FULL CSS STYLING – Dark theme + Black text ONLY on EN/TL toggle
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
    a {{
        color: #00ffaa !important;
    }}
    a:hover {{
        color: #00ffcc !important;
    }}
    /* Glass cards – optimized for dark bg */
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
        color: {text_primary} !important;
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
    /* Primary buttons – green bg + black text */
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
    /* Header & Sidebar – dark & blurred */
    header[data-testid="stHeader"] {{
        background-color: {bg_color} !important;
        backdrop-filter: blur(20px);
    }}
    section[data-testid="stSidebar"] {{
        background: {sidebar_bg} !important;
        backdrop-filter: blur(20px);
        border-right: 1px solid {border_color};
        color: {text_primary} !important;
    }}
    /* Force BLACK text ONLY on the EN/TL toggle button */
    button[key="lang_toggle_public"] {{
        color: #000000 !important;
    }}
    button[key="lang_toggle_public"] span {{
        color: #000000 !important;
    }}
    button[key="lang_toggle_public"]:hover {{
        color: #000000 !important;
    }}
    /* Ensure other buttons/text don't inherit black */
    button:not([key="lang_toggle_public"]) {{
        color: inherit !important;
    }}
    /* Mobile adjustments */
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

    # ── Waitlist Form (FINAL FIXED – client-side Edge Function invoke) ──
st.markdown("<div class='glass-card' style='padding: 2.5rem; border-radius: 24px;'>", unsafe_allow_html=True)

st.markdown(f"""
    <h2 style='text-align:center; margin-bottom:1.5rem;'>{txt('join_waitlist')}</h2>
    <p style='text-align:center; color:{text_muted}; font-size:1.1rem; margin-bottom:2rem; line-height:1.6;'>
        Sumali sa waitlist para maunang makakuha ng access kapag live na ang KMFX EA.<br>
        Limited spots para sa mga pioneer — be part of the journey!
    </p>
""", unsafe_allow_html=True)

with st.form("waitlist_form", clear_on_submit=True):
    col1, col2 = st.columns([1, 1.4])
    
    with col1:
        full_name = st.text_input(
            txt("name"),
            placeholder="Juan Dela Cruz",
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
    full_name_clean = full_name.strip() if full_name else None
    message_clean = message.strip() if message else None

    # Basic validation
    if not email:
        st.error(
            "Email is required" if st.session_state.language == "en"
            else "Kailangan ang Email"
        )
    elif "@" not in email or "." not in email.split("@")[-1] or len(email) < 5:
        st.error(
            "Please enter a valid email address" if st.session_state.language == "en"
            else "Pakilagyan ng valid na email address"
        )
    else:
        with st.spinner("Processing your request..."):
            try:
                data = {
                    "full_name": full_name_clean,
                    "email": email,
                    "message": message_clean,
                    "language": st.session_state.language,
                    "status": "Pending",
                    "subscribed": True
                }

                # DEBUG: Show data (optional – remove later if you want clean UI)
                # st.info("DEBUG: Data being sent")
                # st.json(data)

                response = supabase.table("waitlist").insert(data).execute()

                if response.data:
                    st.success(
                        "Salamat! Nasa waitlist ka na. Makakatanggap ka ng welcome email shortly 👑"
                        if st.session_state.language == "tl"
                        else "Thank you! You're on the waitlist. Welcome email coming soon 👑"
                    )
                    st.balloons()
                    st.caption(
                        "Check your inbox (and spam folder) for the confirmation email."
                        if st.session_state.language == "en"
                        else "Check mo ang inbox mo (at spam folder) para sa welcome email."
                    )

                    # ── DIRECTLY INVOKE EDGE FUNCTION FROM STREAMLIT ──
                    try:
                        invoke_resp = supabase.functions.invoke(
                            "send-waitlist-confirmation",  # ← exact name of your Edge Function
                            {
                                "body": {
                                    "name": full_name_clean or "Anonymous",
                                    "email": email,
                                    "message": message_clean or "",
                                    "language": st.session_state.language
                                }
                            }
                        )

                        # Optional: Show more info if you want (remove for production)
                        # st.caption(f"Email request sent (status: {invoke_resp.status_code})")

                        st.caption("Welcome email request sent successfully! Check spam if not arrived in 1–2 minutes.")
                    
                    except Exception as invoke_err:
                        st.caption(
                            f"Welcome email send had a small issue ({str(invoke_err)}), "
                            "but you're already on the waitlist! We'll fix it soon."
                        )
                        # Optional: log to your logs table
                        # supabase.table("logs").insert({
                        #     "action": "waitlist_email_invoke_failed",
                        #     "details": str(invoke_err),
                        #     "email": email
                        # }).execute()

                else:
                    st.warning("Submission processed but no confirmation received — check dashboard.")

            except Exception as e:
                err_str = str(e).lower()
                if any(x in err_str for x in ["duplicate", "unique", "23505"]):
                    st.info(
                        "Nasa waitlist na pala ang email mo — salamat! Keep following lang."
                        if st.session_state.language == "tl"
                        else "Looks like you're already on the waitlist — thank you! Stay tuned."
                    )
                else:
                    st.error(f"Error joining waitlist: {str(e)}")
                    if "dev" in os.getenv("ENV", "").lower():
                        st.code(str(e))

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
# 1. THE FULL JOURNEY SECTION (RESTORED TO ORIGINAL LENGTH)
# ────────────────────────────────────────────────
if "show_full_journey" not in st.session_state:
    st.session_state.show_full_journey = False

st.markdown("<div class='glass-card' style='text-align:center; margin:5rem auto; padding:3rem;'>", unsafe_allow_html=True)
st.markdown("<h2 class='gold-text'>Want the Full Story Behind KMFX EA?</h2>", unsafe_allow_html=True)
st.markdown("<p style='font-size:1.4rem; opacity:0.9;'>From OFW in Saudi to building an automated empire — built by faith, lessons, and persistence.</p>", unsafe_allow_html=True)

if st.button("👑 Read My Full Trading Journey (2014–2026)", type="primary", use_container_width=True):
    st.session_state.show_full_journey = True
    st.rerun()

if st.session_state.show_full_journey:
    st.markdown(f"<div class='glass-card' style='padding:3rem; margin-top:2rem; border-left:6px solid var(--gold);'>", unsafe_allow_html=True)
    st.markdown("<h2 class='gold-text' style='text-align:center;'>My Trading Journey: From 2014 to KMFX EA 2026</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; font-style:italic; font-size:1.2rem;'>'Built by faith, shared for generations.'</p>", unsafe_allow_html=True)

    # 2014 Section
    st.markdown("### 🌍 2014: The Beginning in Saudi Arabia")
    c1, c2 = st.columns(2)
    with c1: st.image("assets/saudi1.jpg", caption="Team Saudi Boys 🇸🇦", use_column_width=True)
    with c2: st.image("assets/saudi2.jpg", caption="Selfie with STC Cap", use_column_width=True)
    st.write("""
    Noong 2014, nandoon ako sa Saudi Arabia bilang Telecom Technician sa STC. Everyday routine: work sa site, init ng desert... pero tuwing Friday off day ko, dun ko natuklasan ang Philippine stock market.
    Nag-bukas ako ng account sa First Metro Sec. Emotions? Grabe. Sobrang saya kapag green, pero kapag red, lungkot talaga dahil sayang ang overtime. 
    Around 2016, naging close friends ko sina Ramil, Mheg, at Christy. Sila ang naging foundation ng 'team' feeling bago pa naging pro ang lahat.
    """)

    # 2017 Section
    st.markdown("### 🏠 2017: Umuwi sa Pinas at Crypto Era")
    c3, c4 = st.columns(2)
    with c3: st.image("assets/family1.jpg", caption="Date with her ❤️", use_column_width=True)
    with c4: st.image("assets/family2.jpg", caption="Selfie My Family 👨‍👩‍👧", use_column_width=True)
    st.write("""
    Umuwi ako sa Pinas para mag-start ng family life. Dun din sumabog ang crypto wave! Na-scam ako sa Auroramining at natalo sa futures dahil sa FOMO at panic. 
    Walang solid strategy pa noon, emosyon ang nagdedesisyon. Pero yung fire sa trading? Lalong lumakas. Ang mga losses na yan ang naging stepping stones para matuto akong tanggalin ang emosyon sa system.
    """)

    # 2019-2021 Section
    st.markdown("### 🦠 2019–2021: Pandemic Days & Biggest Lesson")
    c5, c6 = st.columns(2)
    with c5: st.image("assets/klever1.jpg", caption="Max gain almost $20k+ 🔥", use_column_width=True)
    with c6: st.image("assets/klever2.jpg", caption="Klever Exchange Setup", use_column_width=True)
    st.write("""
    Sa gitna ng quarantine, natagpuan ko ang Klever token (KLV). Ginamit ko ang 'Ninja Move' feature para sa automated quick flips. 
    Sobrang laki ng gains! Pero nung nag-crash ang BTC (60k to 20k), dun ko naintindihan na 90% ng traders natatalo dahil sa emosyon. 
    Kailangan ng automation para tanggalin ang greed at fear.
    """)

    # 2024-2025 Section
    st.markdown("### 🤖 2024–2025: The Professional Shift")
    c7, c8 = st.columns(2)
    with c7: st.image("assets/ai1.jpg", caption="New Tech Found", use_column_width=True)
    with c8: st.image("assets/ai2.jpg", caption="Using Old Laptop to Build", use_column_width=True)
    st.write("""
    Halos isang taon akong nag-self study ng MQL5 programming. Gabi-gabi, after work, nakaupo sa laptop para i-code ang strategy ko sa Gold (XAUUSD). 
    Pinagsama ko lahat ng lessons mula 2014. No Martingale, No Grid, Strict 1% Risk. 
    January 2025: Breakthrough! Fully working na ang KMFX EA.
    """)

    # 2026 Section
    st.markdown("### 🏆 2025–2026: FTMO Challenges & Comeback")
    c9, c10 = st.columns(2)
    with c9: st.image("assets/ftmo.jpeg", caption="Passed Phase 1 in 13 Days! 🎉", use_column_width=True)
    with c10: st.image("assets/ongoing.jpg", caption="100% Trust Mode 🚀", use_column_width=True)
    st.write("""
    December 2025: PASSED Phase 1 in 13 days! +10.41% gain, 2.98% max DD. 
    Pero nung Phase 2, nag-fail ako dahil nag-intervene ako manually out of fear. 
    Lesson learned: Full trust lang sa system. Ngayong 2026, ang focus ko ay 100% hands-off para sa legacy at community.
    """)

    st.markdown("### ✨ Realization & Future Vision")
    st.image("assets/journey_vision.jpg", use_column_width=True, caption="Built by Faith, Shared for Generations 👑")
    st.write("""
    Ang KMFX EA ay hindi lang tungkol sa pera; ito ay tungkol sa legacy. 
    Ang dream ko ay makapag-iwan ng system na makakatulong sa susunod na henerasyon ng Pinoy traders para maiwasan nila ang sakit na pinagdaanan ko.
    """)

    if st.button("Close Journey", use_container_width=True):
        st.session_state.show_full_journey = False
        st.rerun()
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
# 3. IN-DEPTH FAQs (10 QUESTIONS)
# ────────────────────────────────────────────────
st.markdown("<h2 class='gold-text' style='text-align:center; margin-top:4rem;'>In-Depth Questions</h2>", unsafe_allow_html=True)
faqs = [
    ("1. Ano ang edge ng KMFX EA?", "Focused sa Gold volatility patterns 2021-2025. 1% strict risk + dynamic filters para sa news spikes."),
    ("2. Paano n'yo napatunayan na hindi ito overfitted?", "5-Year Backtest with realistic slippage + real FTMO Phase 1 pass proof."),
    ("3. Ano ang worst-case drawdown?", "Max historical DD is ~12-15% sa backtest, but only 2.98% sa conservative live FTMO run."),
    ("4. Paano kung magbago ang market behavior?", "May adaptive filters para sa news, sessions, at momentum. Regular updates para sa community."),
    ("5. Paano sumali o makakuha ng access?", "Exclusive muna sa pioneers. Message admin for verification at profit-sharing details."),
    ("6. May plan ba sa ibang pairs?", "Gold muna para sa maximum optimization. Stability is priority over quantity."),
    ("7. Paano ko maveverify ang performance?", "May documented stats, FTMO certificates, at live metrics sa pioneer dashboard."),
    ("8. Ano ang exit strategy pag nag-fail?", "Auto DD limits + Growth Fund buffer para sa reinvestment sa challenges."),
    ("9. Paano protektado ang system sa piracy?", "Encrypted license XOR keys + MT5 login binding. Remote revoke capability included."),
    ("10. Ano ang ultimate vision?", "Build KMFX EA Foundations: education and true financial freedom for the next generation.")
]

for q, a in faqs:
    with st.expander(q):
        st.write(a)

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