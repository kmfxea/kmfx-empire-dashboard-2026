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
# 1. FULL TRADING JOURNEY (TIMELINE STYLE)
# ────────────────────────────────────────────────
if "show_full_journey" not in st.session_state:
    st.session_state.show_full_journey = False

st.markdown("<div class='glass-card' style='text-align:center; margin:3rem auto; padding:2rem;'>", unsafe_allow_html=True)
st.markdown("<h2 class='gold-text'>Want the Full Story Behind KMFX EA?</h2>", unsafe_allow_html=True)
st.markdown("<p style='font-size:1.2rem; opacity:0.9;'>From OFW in Saudi to building an automated empire — built by faith, lessons, and persistence.</p>", unsafe_allow_html=True)

if st.button("👑 Read My Full Trading Journey (2014–2026)", type="primary", use_container_width=True):
    st.session_state.show_full_journey = not st.session_state.show_full_journey
    st.rerun()
st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.show_full_journey:
    st.markdown("<div class='glass-card' style='padding:2rem; margin-bottom:3rem; border-left:5px solid var(--gold);'>", unsafe_allow_html=True)
    
    # --- 2014 ---
    st.markdown("### 🌍 2014: The Beginning in Saudi Arabia")
    col1, col2 = st.columns(2)
    with col1: st.image("assets/saudi1.jpg", caption="Team Saudi Boys 🇸🇦", use_column_width=True)
    with col2: st.image("assets/saudi2.jpg", caption="The Foundation", use_column_width=True)
    st.write("""
    Noong 2014, Telecom Technician ako sa STC Saudi. Tuwing Friday off, nag-aaral ako ng Philippine stock market. 
    Dito ko natutunan ang hirap ng emotions: masaya pag green, "sayang overtime" pag red. 
    Dito rin nabuo ang tropa nina Ramil, Mheg, at Christy—ang early foundation ng team.
    """)

    # --- 2017 ---
    st.markdown("### 🏠 2017: Homecoming & Crypto Era")
    col3, col4 = st.columns(2)
    with col3: st.image("assets/family1.jpg", caption="Family is Why ❤️", use_column_width=True)
    with col4: st.image("assets/family2.jpg", caption="Fresh Start 👨‍👩‍👧", use_column_width=True)
    st.write("""
    Umuwi ako para mag-start ng pamilya. Sumabay ang Crypto wave! Na-scam sa Auroramining, natalo sa futures dahil sa FOMO. 
    High risk, no discipline. Pero dito ko na-realize: Ang market ay hindi para sa emosyonal. 
    Kailangan ng system na hindi napapagod o natatakot.
    """)

    # --- 2019-2021 ---
    st.markdown("### 🦠 2019–2021: Pandemic & Klever Realization")
    col5, col6 = st.columns(2)
    with col5: st.image("assets/klever1.jpg", caption="Max Gain $20k+ 🔥", use_column_width=True)
    with col6: st.image("assets/klever2.jpg", caption="Automated Logic", use_column_width=True)
    st.write("""
    Quarantine days. Sa Klever (KLV), nakita ko ang power ng "Ninja Move" automated flips. 
    Pero noong nag-crash ang BTC (60k to 20k), doon ko naintindihan: **90% ng traders natatalo dahil sa emosyon.** Hindi sapat ang strategy; kailangan ng automation para tanggalin ang greed at fear.
    """)

    # --- 2024-2025 ---
    st.markdown("### 🤖 2024–2025: The Professional Shift (MQL5)")
    col7, col8 = st.columns(2)
    with col7: st.image("assets/ai1.jpg", caption="Tech Foundation", use_column_width=True)
    with col8: st.image("assets/ai2.jpg", caption="Coding Nights", use_column_width=True)
    st.write("""
    Isang taon akong nag-self-study ng **MQL5 programming**. Gabi-gabing puyat para i-code ang strategy ko sa Gold (XAUUSD). 
    Pinagsama ko lahat ng lessons mula 2014. No Martingale, No Grid. Strict 1% Risk. 
    **January 2025:** Breakthrough! Fully working na ang KMFX EA.
    """)

    # --- 2026 ---
    st.markdown("### 🏆 2025–2026: FTMO Victory & Legacy")
    col9, col10 = st.columns(2)
    with col9: st.image("assets/ftmo.jpeg", caption="Phase 1 Passed! 🎉", use_column_width=True)
    with col10: st.image("assets/ongoing.jpg", caption="100% Hands-Off Mode", use_column_width=True)
    st.write("""
    December 2025: Pasado ang FTMO Phase 1 (+10.41% gain, 2.98% max DD). 
    Napatunayan na ang system ay solid. Ngayong 2026, ang focus ay **Legacy**—ang makapag-iwan ng 
    automated system na makakatulong sa susunod na henerasyon ng Pinoy traders.
    """)
    
    st.markdown("</div>", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# 2. WHY CHOOSE KMFX EA? (BENEFITS GRID)
# ────────────────────────────────────────────────
st.markdown("<h2 class='gold-text' style='text-align:center; margin-top:4rem;'>Why Choose KMFX EA?</h2>", unsafe_allow_html=True)
cols = st.columns(3)
benefits = [
    {"emoji": "👑", "title": "100% Hands-Off", "desc": "Run and forget. Removes human emotions—the #1 killer in trading."},
    {"emoji": "📈", "title": "Gold (XAUUSD) Edge", "desc": "Optimized for Gold volatility. +3,071% 5-Year Backtest performance."},
    {"emoji": "🔒", "title": "Prop Firm Ready", "desc": "FTMO-compatible. Strict no-martingale, no-grid, 1% risk per trade."},
    {"emoji": "🙏", "title": "Built by Faith", "desc": "Result of 12 years of experience. A tool with a purpose and a vision."},
    {"emoji": "🤝", "title": "Pioneer Community", "desc": "Early believers get a 30% profit share. Real accountability group."},
    {"emoji": "💰", "title": "Legacy Vision", "desc": "Passive income for your family. Sustainable wealth for generations."}
]

for i, b in enumerate(benefits):
    with cols[i % 3]:
        st.markdown(f"""
        <div class='glass-card' style='text-align:center; padding:1.5rem; height:220px; margin-bottom:1rem;'>
            <div style='font-size:2.5rem;'>{b['emoji']}</div>
            <h4 style='color:var(--gold);'>{b['title']}</h4>
            <p style='font-size:0.9rem; opacity:0.8;'>{b['desc']}</p>
        </div>
        """, unsafe_allow_html=True)

# ────────────────────────────────────────────────
# 3. IN-DEPTH QUESTIONS (THE FULL 10 FAQs)
# ────────────────────────────────────────────────
st.markdown("<h2 class='gold-text' style='text-align:center; margin-top:4rem;'>In-Depth Questions</h2>", unsafe_allow_html=True)
faqs = [
    ("1. Ano ang edge ng KMFX EA sa market?", "Focused sa XAUUSD volatility patterns (2021–2025). No over-optimization, true forward test results."),
    ("2. Paano n'yo napatunayan na hindi ito overfitted?", "5-Year Backtest with realistic slippage + real FTMO Phase 1 pass proof."),
    ("3. Ano ang worst-case drawdown?", "Historical max DD is ~12-15% sa backtest, but only 2.98% sa conservative live FTMO run."),
    ("4. Paano kung magbago ang market behavior?", "May adaptive news filters at session checks. regular updates are provided to the community."),
    ("5. Paano sumali o makakuha ng access?", "Exclusive muna sa pioneer community. Profit-sharing model for trusted members."),
    ("6. May plan ba sa EURUSD o Crypto?", "Gold muna para sa maximum optimization. Stability is our priority over quantity."),
    ("7. Paano ko maveverify ang performance?", "Documented FTMO certificates at live metrics dashboard sa loob ng portal."),
    ("8. Ano ang exit strategy pag nag-fail?", "Auto DD limits at Growth Fund buffer para sa reinvestment sa bagong challenges."),
    ("9. Paano protektado ang system sa piracy?", "Encrypted license XOR keys at MT5 login binding. Remote revoke capability included."),
    ("10. Ano ang ultimate vision mo sa KMFX EA?", "Build KMFX EA Foundations: Education and financial freedom for the next generation.")
]

for q, a in faqs:
    with st.expander(q):
        st.write(a)

# ────────────────────────────────────────────────
# 4. LOGIN & AUTH GUARD
# ────────────────────────────────────────────────
st.markdown("<div style='margin-top: 5rem;'></div>", unsafe_allow_html=True)
tab_owner, tab_admin, tab_client = st.tabs(["👑 Owner", "🛠️ Admin", "👥 Client"])

def render_login(role, page):
    with st.form(key=f"login_{role}"):
        u = st.text_input("Username").strip().lower()
        p = st.text_input("Password", type="password")
        if st.form_submit_button(f"Login as {role}"):
            if login_user(u, p, expected_role=role.lower()):
                st.session_state.role = role.lower()
                st.success("Redirecting...")
                st.switch_page(page)
            else:
                st.error("Invalid credentials.")

with tab_owner: render_login("Owner", "pages/👤_Admin_Management.py")
with tab_admin: render_login("Admin", "pages/👤_Admin_Management.py")
with tab_client: render_login("Client", "pages/🏠_Dashboard.py")

if not is_authenticated():
    st.stop()