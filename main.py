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

# ── Centralized imports from utils ───────────────────────────────────────
from utils.supabase_client import supabase
from utils.auth import login_user, is_authenticated
from utils.helpers import (
    upload_to_supabase,
    make_same_size,
    log_action,
    start_keep_alive_if_needed
)

# Optional keep-alive for Streamlit Cloud
start_keep_alive_if_needed()

# ────────────────────────────────────────────────
# Handle logout success message FIRST (before anything renders)
# ────────────────────────────────────────────────
if st.session_state.pop("logging_out", False):
    st.success("You have been logged out successfully! 👋")
    # Clean up any leftover flags
    for k in ["just_logged_in", "_sidebar_rendered"]:
        st.session_state.pop(k, None)

# ────────────────────────────────────────────────
# Determine authentication state EARLY
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
    # Hide sidebar completely on public landing
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

# ────────────────────────────────────────────────
# THEME & COLORS
# ────────────────────────────────────────────────
if "theme" not in st.session_state:
    st.session_state.theme = "dark" if not authenticated else "light"

theme = st.session_state.theme
accent_primary = "#00ffaa"
accent_gold   = "#ffd700"
accent_glow   = "#00ffaa40"
accent_hover  = "#00ffcc"
bg_color      = "#f8fbff" if theme == "light" else "#0a0d14"
card_bg       = "rgba(255,255,255,0.75)" if theme == "light" else "rgba(15,20,30,0.70)"
border_color  = "rgba(0,0,0,0.08)" if theme == "light" else "rgba(100,100,100,0.15)"
text_primary  = "#0f172a" if theme == "light" else "#ffffff"
text_muted    = "#64748b" if theme == "light" else "#aaaaaa"
card_shadow   = "0 8px 25px rgba(0,0,0,0.12)" if theme == "light" else "0 10px 30px rgba(0,0,0,0.5)"
sidebar_bg    = "rgba(248,251,255,0.95)" if theme == "light" else "rgba(10,13,20,0.95)"

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
            st.session_state.username = user["username"].lower()
            st.session_state.full_name = user["full_name"] or user["username"]
            st.session_state.role = user["role"]
            st.session_state.theme = "light"
            st.session_state.just_logged_in = True
            log_action("QR Login Success", f"User: {user['full_name']} | Role: {user['role']}")
            st.query_params.clear()
            st.rerun()  # Force rerun so main.py sees authenticated=True
        else:
            st.error("Invalid or revoked QR code")
            st.query_params.clear()
    except Exception as e:
        st.error(f"QR login failed: {str(e)}")
        st.query_params.clear()

# ────────────────────────────────────────────────
# AUTHENTICATED REDIRECT + WELCOME MESSAGE
# ────────────────────────────────────────────────
if authenticated:
    # Show welcome message only on fresh login
    if st.session_state.get("just_logged_in"):
        st.success(f"Welcome back, {st.session_state.full_name}! 🚀")
        st.session_state.pop("just_logged_in")
    
    # Redirect to dashboard
    st.switch_page("pages/🏠_Dashboard.py")

# This goes at the VERY TOP of your main app file (before any page logic or sidebar)
# ====================== PUBLIC LANDING GATE - ONLY SHOWN IF NOT AUTHENTICATED ======================
if not st.session_state.get("authenticated", False):
    # Force dark mode for public landing (same as old)
    if st.session_state.get("theme") != "dark":
        st.session_state.theme = "dark"
        st.rerun()

    # GLOBAL FIX: Zero top space + hide Streamlit header (public landing only)
    st.markdown("""
    <style>
    /* Remove all top space */
    .block-container {
        padding-top: 0rem !important;
        margin-top: 0rem !important;
    }
    .main > div {
        padding-top: 0rem !important;
    }
    header, .stApp > header {
        visibility: hidden !important;
        height: 0 !important;
    }
    .st-emotion-cache-1y4p8pa {
        padding-top: 0rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # === CENTERED LOGO AT VERY TOP ===
    logo_col = st.columns([1, 6, 1])[1]
    with logo_col:
        st.image("assets/logo.png", use_column_width=True)

    # === HERO TEXTS (exact old sizing & centering) ===
    st.markdown(
        f"<h1 class='gold-text' style='text-align: center; font-size: 4.5rem; margin: 1rem 0;'>KMFX EA</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"<h2 style='text-align: center; color: #e2e8f0; font-size: 2.2rem; margin: 0.5rem 0;'>"
        "Automated Gold Trading for Financial Freedom</h2>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='text-align: center; font-size: 1.4rem; color: #94a3b8; margin: 1rem 0;'>"
        "Passed FTMO Phase 1 • +3,071% 5-Year Backtest • Building Legacies of Generosity</p>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='text-align: center; font-size: 1.2rem; color: #64748b;'>"
        "Mark Jeff Blando – Founder & Developer • 2026</p>",
        unsafe_allow_html=True
    )

    # === REALTIME EMPIRE STATS (your exact code, but in clean columns) ===
    try:
        accounts_count = supabase.table("ftmo_accounts").select("id", count="exact").execute().count or 0
        equity_data = supabase.table("ftmo_accounts").select("current_equity").execute().data or []
        total_equity = sum(acc.get("current_equity", 0) for acc in equity_data)
        gf_data = supabase.table("growth_fund_transactions").select("type, amount").execute().data or []
        gf_balance = sum(t["amount"] if t["type"] == "In" else -t["amount"] for t in gf_data)
        members_count = supabase.table("users").select("id", count="exact").eq("role", "client").execute().count or 0
    except Exception:
        accounts_count = total_equity = gf_balance = members_count = 0

    stat_cols = st.columns(4)
    stat_cols[0].metric("Active Accounts", accounts_count)
    stat_cols[1].metric("Total Equity", f"${total_equity:,.0f}")
    stat_cols[2].metric("Growth Fund", f"${gf_balance:,.0f}")
    stat_cols[3].metric("Members", members_count)

    # ====================== PORTFOLIO STORY / ORIGIN & MOTIVATION ======================
    st.markdown("<div class='glass-card' style='margin:4rem 0; padding:3rem;'>", unsafe_allow_html=True)
    
    # Origin & Motivation (2024)
    st.markdown("<h2 class='gold-text'>Origin & Motivation (2024)</h2>", unsafe_allow_html=True)
    st.write("""
Noong 2024, frustrated ako sa manual trading — paulit-ulit na losses dahil sa emotions, lack of discipline, at timing issues. Realization: "Kung hindi professional, maloloss ka lang sa market."
Decided to build my own Expert Advisor (EA) to remove human error, achieve consistency, and become a professional trader through automation.
Early inspiration from ~2016 trading days, sharing ideas with friend Ramil.
    """)

    # Development Phase (2024)
    st.markdown("<h2 class='gold-text'>Development Phase (2024)</h2>", unsafe_allow_html=True)
    st.write("""
- Full year of self-study in MQL5 programming
- Trial-and-error: Combined multiple indicators, price action rules, risk management filters
- Hundreds of backtests, forward tests, debugging — almost 1 year of experiment before stability
    """)

    # Official Launch & Early Testing (2025)
    st.markdown("<h2 class='gold-text'>Official Launch & Early Testing (2025)</h2>", unsafe_allow_html=True)
    st.write("""
- January 2025: Breakthrough — EA fully functional and running smoothly. Officially named KMFX EA
- Focused exclusively on XAUUSD (GOLD) for its volatility and opportunities
- September 2025: Formed KMFX EA TESTER group (initial: Weber — most active, Ramil, Sheldon, Jai). ~2 months forward testing with multiple trials and real-time feedback
- Late 2025 (Oct-Dec): Mastered backtesting — ran historical data from 2021–2025. Game-changer: Quickly spotted weaknesses, polished entries/exits, filters for gold spikes/news volatility
    """)

    # Major Milestones & Tools (2025)
    st.markdown("<h2 class='gold-text'>Major Milestones & Tools (2025)</h2>", unsafe_allow_html=True)
    st.write("""
- October 15, 2025: Launched sleek KMFX EA MT5 Client Tracker dashboard at kmfxea.streamlit.app — premium portal for performance tracking (owner, admin, client logins)
- December 2025: Pioneer community formed — 14 believers contributed ₱17,000 PHP (₱1,000 per unit) to fund the real challenge phase
  - Profit sharing: 30% of profits proportional to units
  - Thank you to: Mark, Jai, Doc, Weber (2 units), Don, Mark Fernandez (3 units), Ramil, Cristy, Meg, Roland, Mila, Malruz, Julius, Joshua
    """)

    # FTMO Prop Firm Journey – First Attempt (Dec 2025 - Jan 2026)
    st.markdown("<h2 class='gold-text'>FTMO Prop Firm Journey – First Attempt (Dec 2025 - Jan 2026)</h2>", unsafe_allow_html=True)
    st.write("""
- December 13, 2025: Started FTMO 10K Challenge (Plan A, real evaluation)
- December 26, 2025: PASSED Phase 1 (Challenge) in just ~13 days!
  - Certificate issued: Proven profit target achieved + quality risk management
  - Stats snapshot: $10,000 → $11,040.58 (+10.41% gain), 2.98% max drawdown, 118 trades (longs only, 52% win rate), +12,810.8 pips, profit factor 1.52
  - Avg trade: 43 minutes (scalping-style on gold volatility)
    """)

    # Phase 2 (Verification) Attempt
    st.markdown("<h2 class='gold-text'>Phase 2 (Verification) Attempt</h2>", unsafe_allow_html=True)
    st.write("""
- Goal: 5% profit target, same strict risk limits (5% daily / 10% overall loss)
- Outcome: Failed due to emotional intervention — shaken by market noise, manually adjusted parameters and added trades
- Key Insight: Untouched sim run (Jan 1–16, 2026) showed ~$2,000 additional gain — would have passed easily
- Big Lesson: Trust the System No Matter What. Emotions are the real enemy; the EA is solid when left alone
- Turned failure into life rebuild: Discipline, patience, surrender to God's plan — applied to trading AND personal life
    """)

    # Current Attempt (Jan 2026)
    st.markdown("<h2 class='gold-text'>Current Attempt (Jan 2026)</h2>", unsafe_allow_html=True)
    st.write("""
- New FTMO 10K Challenge (Phase 1) ongoing
- Full trust mode: 100% hands-off — no tweaks, no manual trades, pure automated execution
- Confidence: Previous pass + untouched sims prove the edge. Goal: Pass with consistency, low DD, then Verification → funded account
    """)

    # Dual Product Evolution (2026)
    st.markdown("<h2 class='gold-text'>Dual Product Evolution (2026)</h2>", unsafe_allow_html=True)
    st.write("""
- Prop Firm Version (KMFX EA – Locked): For FTMO/challenges only — personal use, strict no-intervention during evaluations
- Personal/Client Version (in progress): Same core strategy, but client-friendly
  - Solid backtest results on historical GOLD data (consistent gains, controlled risk)
  - Future: Deployable on personal accounts, potential for clients/pioneers (with sharing or access via dashboard)
  - Advantage: Separate from prop rules — flexible for real-money growth
    """)

    # Performance Proof
    st.markdown("<h2 class='gold-text'>Performance Proof</h2>", unsafe_allow_html=True)
    st.write("""
- FTMO Phase 1 Passed: +10.41%, 2.98% max DD
- 2025 Backtest: +187.97%
- 5-Year Backtest (2021-2025): +3,071%
- Safety First: 1% risk per trade, no martingale/grid, controlled drawdown
    """)

    st.markdown("</div>", unsafe_allow_html=True)  # Close glass-card

    # ====================== FULL TRADING JOURNEY EXPANDER ======================
    if "show_full_journey" not in st.session_state:
        st.session_state.show_full_journey = False

    st.markdown(
        "<div class='glass-card' style='text-align:center; margin:5rem 0; padding:3rem;'>",
        unsafe_allow_html=True
    )
    st.markdown("<h2 class='gold-text'>Want the Full Story Behind KMFX EA?</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p style='font-size:1.4rem; opacity:0.9;'>From OFW in Saudi to building an automated empire — built by faith, lessons, and persistence.</p>",
        unsafe_allow_html=True
    )

    if st.button("👑 Read My Full Trading Journey (2014–2026)", type="primary", use_container_width=True):
        st.session_state.show_full_journey = True
        st.rerun()

    if st.session_state.show_full_journey:
        st.markdown(
            "<div class='glass-card' style='padding:3rem; margin:3rem 0;'>",
            unsafe_allow_html=True
        )
        st.markdown(
            "<h2 class='gold-text' style='text-align:center;'>My Trading Journey: From 2014 to KMFX EA 2026</h2>",
            unsafe_allow_html=True
        )
        st.markdown(
            "<p style='text-align:center; font-style:italic; font-size:1.3rem; opacity:0.9;'>"
            "Ako si <strong>Mark Jeff Blando</strong> (Codename: <em>Kingminted</em>) — "
            "simula 2014 hanggang ngayon 2026, pinagdaanan ko ang lahat: losses, wins, scams, pandemic gains, "
            "at sa wakas, pagbuo ng sariling automated system.<br><br>"
            "Ito ang kwento ko — <strong>built by faith, shared for generations</strong>.</p>",
            unsafe_allow_html=True
        )

        journey_sections = [
            ("🌍 2014: The Beginning in Saudi Arabia", """
Noong 2014, nandoon ako sa Saudi Arabia bilang Telecom Technician sa STC.
Everyday routine: work sa site, init ng desert... pero tuwing **Friday — off day ko** — may oras akong mag-explore online.
Nag-start ako mag-search ng ways para magdagdag ng income. Alam mo naman OFW life: padala sa pamilya, savings, pero gusto ko rin ng something para sa future.
Dun ko natuklasan ang **Philippine stock market**. Nagbukas ako ng account sa First Metro Sec, nag-download ng app, nagbasa ng news, PSE index... at sinubukan lahat ng basic — buy low sell high, tips sa forums, trial-and-error.
**Emotions? Grabe.** Sobrang saya kapag green — parang nanalo sa lotto! Pero kapag red? Lungkot talaga, "sayang 'yung overtime ko."
Paulit-ulit 'yun — wins, losses, lessons. Hindi pa seryoso noon, more like hobby lang habang nasa abroad... pero dun talaga nagsimula ang passion ko sa trading.
Around 2016, naging close friends ko sina Ramil, Mheg, at Christy. Nagsha-share kami ng ideas sa chat, stock picks, charts kahit liblib na oras.
Yun 'yung simula ng **"team" feeling** — hindi pa pro, pero may spark na.
*Little did I know, 'yung mga simpleng usapan na 'yun ang magiging foundation ng KMFX EA years later.*
            """),
            ("🏠 2017: Umuwi sa Pinas at Crypto Era", """
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
            """),
            # ... (add the rest of your sections here in the same format)
            # For brevity, I only showed the first two — copy-paste the rest from your old code
        ]

        for date_title, content in journey_sections:
            st.markdown(f"<h3 style='color:{accent_gold}; text-align:center; margin:2rem 0;'>{date_title}</h3>", unsafe_allow_html=True)
            st.markdown(content.replace("\n", "<br>"), unsafe_allow_html=True)

        if st.button("Close Journey", use_container_width=True):
            st.session_state.show_full_journey = False
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)  # Close teaser glass-card

    # ====================== WHY KMFX EA? BENEFITS GRID ======================
    st.markdown("<div class='glass-card' style='margin:4rem 0; padding:3rem;'>", unsafe_allow_html=True)
    st.markdown("<h2 class='gold-text' style='text-align:center;'>Why Choose KMFX EA?</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center; opacity:0.9; font-size:1.3rem; margin-bottom:3rem;'>"
        "Hindi lang isa pang EA — ito ang automated system na galing sa totoong 12+ years journey, "
        "pinatunayan sa FTMO, at ginawa with discipline, persistence, at faith.</p>",
        unsafe_allow_html=True
    )

    benefit_cols = st.columns(3)
    benefits = [
        ("👑 100% Hands-Off Automation", [
            "Run and forget — walang kailangang galawin pag naka-set na",
            "Removes emotions completely (yung pinakamalaking killer sa trading)",
            "Pure MQL5 logic + strict risk rules = consistent execution"
        ]),
        ("📈 Gold (XAUUSD) Focused Edge", [
            "Optimized for Gold volatility — best market para sa scalping & swing",
            "+3,071% 5-Year Backtest • +187% 2025 • Low DD <3%",
            "Proven sa real FTMO challenge (Phase 1 passed in 13 days!)"
        ]),
        ("🔒 Prop Firm Ready & Safe", [
            "FTMO-compatible — strict no-martingale, no-grid, 1% risk per trade",
            "Locked version para sa challenges • Flexible personal version",
            "Full transparency: journey, stats, at community pioneer sharing"
        ]),
        ("🙏 Built by Faith & Real Experience", [
            "Galing sa 12 taon na totoong trading journey (2014 hanggang 2026)",
            "Hindi basta code — may purpose: tulungan ang marami sa financial freedom",
            "Discipline + surrender to God's plan = sustainable success"
        ]),
        ("🤝 Pioneer Community & Sharing", [
            "Early believers get proportional profit share (30% pool)",
            "Real accountability group — testers, pioneers, at future foundation",
            "Hindi solo — sama-sama tayo sa pag-scale ng empire"
        ]),
        ("💰 Passive Income + Legacy Vision", [
            "Goal: true passive income para mas maraming time sa pamilya at Lord",
            "Dream: KMFX EA Foundations — turuan ang aspiring traders maging pro",
            "Built by faith, shared for generations — legacy na hindi matitigil"
        ])
    ]

    for i, (title, points) in enumerate(benefits):
        with benefit_cols[i % 3]:
            st.markdown(f"<h4 style='color:{accent_gold}; text-align:center;'>{title}</h4>", unsafe_allow_html=True)
            st.markdown(
                "<ul style='text-align:left; padding-left:1.5rem;'>" +
                "".join(f"<li style='margin:0.5rem 0;'>{p}</li>" for p in points) +
                "</ul>",
                unsafe_allow_html=True
            )

    st.markdown("</div>", unsafe_allow_html=True)

    # ====================== CALL TO ACTION ======================
    st.markdown(
        "<div style='text-align:center; margin:5rem 0;'>",
        unsafe_allow_html=True
    )
    st.markdown("<h2 class='gold-text'>Ready to Join the Empire?</h2>", unsafe_allow_html=True)
    if st.button("Login to Dashboard →", type="primary", use_container_width=True):
        # Your login flow here (e.g., set authenticated or redirect)
        st.session_state.authenticated = False  # or trigger login modal
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # IMPORTANT: Stop rendering authenticated content
    st.stop()

# ────────────────────────────────────────────────
# AUTHENTICATED CONTENT BELOW (your normal multi-page logic)
# ────────────────────────────────────────────────
# Sidebar, page selection, etc. goes here...

# ────────────────────────────────────────────────
# SECURE MEMBER LOGIN – ROLE-AWARE TABS
# ────────────────────────────────────────────────
st.markdown("<div class='glass-card' style='text-align:center; margin:5rem auto; padding:4rem; max-width:800px;'>", unsafe_allow_html=True)
st.markdown("<h2 class='gold-text'>Already a Pioneer or Member?</h2>", unsafe_allow_html=True)
st.markdown("<p style='font-size:1.4rem; opacity:0.9;'>Access your elite dashboard, realtime balance, profit shares, EA versions, and empire tools</p>", unsafe_allow_html=True)

tab_owner, tab_admin, tab_client = st.tabs(["👑 Owner Login", "🛠️ Admin Login", "👥 Client Login"])

# OWNER LOGIN
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
            st.rerun()  # Let main.py handle the redirect

# ADMIN LOGIN
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
            st.rerun()

# CLIENT LOGIN
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
            st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# STOP IF NOT AUTHENTICATED (public content already rendered above)
# ────────────────────────────────────────────────
if not authenticated:
    st.stop()