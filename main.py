# main.py - KMFX EA Public Landing + Login Page
# Updated: February 2026 with improved mobile/tablet responsiveness
import streamlit as st
import yfinance as yf
from datetime import datetime, timedelta
from PIL import Image
from utils.supabase_client import supabase
from utils.auth import login_user, is_authenticated
from utils.helpers import (
    upload_to_supabase,
    make_same_size,
    log_action,
    start_keep_alive_if_needed
)

start_keep_alive_if_needed()

# ────────────────────────────────────────────────
# SESSION & AUTH CHECK FIRST
# ────────────────────────────────────────────────
authenticated = is_authenticated()

if authenticated:
    st.set_page_config(
        page_title="KMFX Empire Dashboard",
        page_icon="👑",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    st.switch_page("pages/🏠_Dashboard.py")
else:
    st.set_page_config(
        page_title="KMFX EA - Elite Gold Automation",
        page_icon="👑",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

# ────────────────────────────────────────────────
# THEME VARIABLES
# ────────────────────────────────────────────────
accent_gold = "#ffd700"
accent_glow = "#ffd70050"
accent_primary = "#00ffaa"
accent_hover = "#ffea80"
bg_color = "#0d1117"
card_bg = "rgba(20, 25, 40, 0.88)"
border_color = "rgba(255,215,0,0.22)"
text_primary = "#e2e8f0"
text_muted = "#a0aec0"
card_shadow = "0 8px 32px rgba(0,0,0,0.55)"

st.markdown(f"""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@600;700;800&display=swap" rel="stylesheet">

<style>
    /* ── Safe global resets ── */
    * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }}

    html, body, [class*="css-"] {{
        font-family: 'Inter', system-ui, sans-serif;
        font-size: 16px;
        line-height: 1.6;
        color: {text_primary};
    }}

    .stApp {{
        background: linear-gradient(135deg, {bg_color} 0%, #0f1622 100%);
    }}

    /* ── Main container ── */
    .main .block-container {{
        max-width: 1180px;
        padding: 2.5rem 4rem;
        margin: 0 auto;
    }}

    /* ── Typography – orange titles like before + gold glow for accent ── */
    h1, h2, h3, h4 {{
        font-family: 'Playfair Display', serif;
        color: #ff6200;                 /* ← orange main title color */
        text-align: center;
        text-shadow: 0 0 12px rgba(255,98,0,0.5);
        margin: 1rem 0 0.8rem;
    }}

    h1 {{ font-size: 3.8rem; font-weight: 800; letter-spacing: -0.6px; }}
    h2 {{ font-size: 2.7rem; font-weight: 700; margin: 2.8rem 0 1.6rem; }}
    h3 {{ font-size: 2.1rem; font-weight: 600; }}

    /* ── Gold accent text (for prices, gains, etc.) ── */
    .gold-text {{
        color: {accent_gold};
        text-shadow: 0 0 14px {accent_glow};
    }}

    /* ── Glass cards (common) ── */
    .glass-card {{
        background: rgba(20,25,40,0.92);
        backdrop-filter: blur(18px);
        border-radius: 20px;
        border: 1px solid rgba(255,215,0,0.18);
        padding: 2.2rem 2.6rem;
        box-shadow: 0 10px 35px rgba(0,0,0,0.45);
        margin: 2.5rem auto;
        max-width: 1100px;
    }}

    /* ── Primary button ── */
    button[kind="primary"] {{
        background: linear-gradient(90deg, #00ffaa, #ffea80);
        color: #000;
        border: none;
        border-radius: 12px;
        padding: 0.9rem 2rem;
        font-size: 1.1rem;
        font-weight: 600;
        box-shadow: 0 5px 18px rgba(0,255,170,0.4);
    }}
    button[kind="primary"]:hover {{
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 10px 30px rgba(0,255,170,0.6);
    }}

    /* ── RESPONSIVE ── */
    @media (max-width: 992px) {{
        .main .block-container {{ padding: 2rem 3rem; }}
        h1 {{ font-size: 3.2rem; }}
        h2 {{ font-size: 2.4rem; }}
    }}

    @media (max-width: 768px) {{
        .main .block-container {{ padding: 1.6rem 2.2rem; }}
        h1 {{ font-size: 2.7rem; }}
        h2 {{ font-size: 2.1rem; }}
        .glass-card {{ padding: 1.8rem 2rem; }}
    }}

    @media (max-width: 480px) {{
        .main .block-container {{ padding: 1.3rem 1.6rem; }}
        h1 {{ font-size: 2.3rem; }}
        h2 {{ font-size: 1.9rem; }}
        .glass-card {{ padding: 1.5rem 1.6rem; margin: 2rem auto; }}
    }}
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# LANGUAGE TOGGLE – orange background, top-right, fixed & mobile-friendly
# ────────────────────────────────────────────────
if "language" not in st.session_state:
    st.session_state.language = "en"

texts = {
    "en": {
        "hero_title": "KMFX EA",
        "hero_sub": "Automated Gold Trading for Financial Freedom",
        "hero_desc": "Passed FTMO Phase 1 • +3,071% 5-Year Backtest • Building Legacies of Generosity",
        "join_waitlist": "Join Waitlist – Early Access",
        "name": "Full Name",
        "email": "Email",
        "why_join": "Why do you want to join KMFX? (optional)",
        "submit": "Join Waitlist 👑",
        "success": "Success! You're on the list. Check your email soon 🚀",
        "pioneers_title": "Our Pioneers",
    },
    "tl": {
        "hero_title": "KMFX EA",
        "hero_sub": "Awtomatikong Pangangalakal ng Ginto para sa Kalayaang Pinansyal",
        "hero_desc": "Naipasa ang FTMO Phase 1 • +3,071% 5-Taon Backtest • Bumubuo ng Pamana ng Kagandahang-loob",
        "join_waitlist": "Sumali sa Waitlist – Maagang Access",
        "name": "Buong Pangalan",
        "email": "Email",
        "why_join": "Bakit gusto mong sumali sa KMFX? (opsyonal)",
        "submit": "Sumali sa Waitlist 👑",
        "success": "Tagumpay! Nasa listahan ka na. Check mo ang email mo soon 🚀",
        "pioneers_title": "Mga Pioneer Namin",
    }
}

def txt(key):
    return texts[st.session_state.language].get(key, key)

# ── Custom CSS: orange theme, top-right fixed ──
st.markdown("""
<style>
    .lang-toggle-container {
        position: fixed;                    /* fixed para laging nasa top-right kahit scroll */
        top: 1.2rem;
        right: 1.8rem;
        z-index: 1000;                      /* siguradong nasa ibabaw ng lahat */
    }

    .lang-toggle-btn {
        background: linear-gradient(135deg, #ff6200, #ff8533) !important;  /* orange gradient */
        color: white !important;
        border: none !important;
        border-radius: 999px !important;    /* pill shape */
        padding: 0.75rem 1.5rem !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        box-shadow: 0 6px 20px rgba(255,98,0,0.5) !important;
        transition: all 0.3s ease !important;
        cursor: pointer;
        letter-spacing: 0.5px;
    }

    .lang-toggle-btn:hover {
        background: linear-gradient(135deg, #ff8533, #ff6200) !important;
        transform: scale(1.08) translateY(-2px) !important;
        box-shadow: 0 12px 30px rgba(255,98,0,0.7) !important;
    }

    .lang-toggle-btn:active {
        transform: scale(0.97) !important;
    }

    /* Mobile / tablet adjustments */
    @media (max-width: 992px) {
        .lang-toggle-container {
            top: 1rem;
            right: 1.2rem;
        }
        .lang-toggle-btn {
            padding: 0.65rem 1.3rem !important;
            font-size: 1rem !important;
        }
    }

    @media (max-width: 480px) {
        .lang-toggle-container {
            top: 0.9rem;
            right: 1rem;
        }
        .lang-toggle-btn {
            padding: 0.6rem 1.2rem !important;
            font-size: 0.95rem !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# Container + Button – top-right
st.markdown('<div class="lang-toggle-container">', unsafe_allow_html=True)

if st.button("EN / TL", key="lang_toggle", help="Switch to English / Tagalog"):
    st.session_state.language = "tl" if st.session_state.language == "en" else "en"
    st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ────────────────────────────────────────────────
# LOGO + HERO – ultra-reliable centering on all devices
# ────────────────────────────────────────────────

st.markdown('<div style="text-align:center; margin:2.5rem 0 2rem;">', unsafe_allow_html=True)
st.image("assets/logo.png", use_column_width=False)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown(f"""
<div style="text-align:center; max-width:900px; margin:0 auto;">
    <h1>{txt('hero_title')}</h1>
    <h2 style="color:{text_primary};">{txt('hero_sub')}</h2>
    <p style="font-size:1.35rem; opacity:0.92; margin:1rem auto; max-width:800px;">
        {txt('hero_desc')}
    </p>
    <p style="font-size:1.1rem; opacity:0.8;">
        Mark Jeff Blando – Founder & Developer • 2026
    </p>
</div>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# LIVE GOLD PRICE + REALTIME TRADINGVIEW MINI CHART – back to original ticker, better size & reliability
# ────────────────────────────────────────────────

@st.cache_data(ttl=30)  # medyo mas matagal para hindi masyadong mag-re-fetch, pero sapat pa rin
def get_gold_price():
    try:
        t = yf.Ticker("GC=F").info
        price = t.get('regularMarketPrice') or t.get('previousClose') or t.get('regularMarketPreviousClose')
        ch = t.get('regularMarketChangePercent', 0)
        return round(price, 1) if price else None, ch
    except Exception as e:
        # Optional: tahimik na fallback, wag mag-warning sa user para clean
        return None, 0

price, change = get_gold_price()

# ── Prominent pero hindi sobrang laki na price display (mas balanced sa lahat ng screen) ──
if price:
    st.markdown(f"""
    <div style="
        text-align: center;
        font-size: 4.2rem;                /* mas maliit kaysa 5.2rem pero prominent pa rin */
        font-weight: 800;
        color: {accent_gold};
        text-shadow: 0 0 24px {accent_glow}, 0 0 48px {accent_glow};
        margin: 2rem 0 0.8rem 0;
        letter-spacing: -0.5px;
        line-height: 1.05;
    ">
        ${price:,.1f}
    </div>
    <p style="
        text-align: center;
        font-size: 1.55rem;
        margin: 0 0 2rem 0;
        color: {text_primary};
        opacity: 0.95;
    ">
        <span style="
            color: {'#00ffaa' if change >= 0 else '#ff5555'};
            font-weight: 700;
            font-size: 1.65rem;
        ">
            {change:+.2f}%
        </span>
        <span> • Live Gold (XAU/USD) • GC=F Futures</span>
    </p>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div style="
        text-align: center;
        font-size: 3.2rem;
        color: {text_muted};
        margin: 2.5rem 0;
        opacity: 0.7;
    ">
        Gold Price (Loading or Delayed...)
    </div>
    """, unsafe_allow_html=True)

# ── TradingView mini-chart – inayos para mas maganda sa tablet/mobile (hindi clipped) ──
st.components.v1.html("""
<div class="tradingview-widget-container" style="
    width: 100%;
    height: 45vw;                     /* balanced aspect ratio */
    min-height: 200px;
    max-height: 280px;
    margin: 1.5rem auto 2.8rem auto;
    position: relative;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 6px 24px rgba(0,0,0,0.45);
">
  <tv-mini-chart
    symbol="OANDA:XAUUSD"
    color-theme="dark"
    locale="en"
    autosize
  ></tv-mini-chart>
  <script type="module" src="https://widgets.tradingview-widget.com/w/en/tv-mini-chart.js" async></script>
</div>
""", height=300)  # binigyan ng konting extra space para hindi ma-cut sa edges

# ────────────────────────────────────────────────
# WAITLIST FORM
# ────────────────────────────────────────────────
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.markdown(f"<h2 style='margin-bottom:1.8rem;'>{txt('join_waitlist')}</h2>", unsafe_allow_html=True)

with st.form("waitlist_form", clear_on_submit=True):
    col1, col2 = st.columns([1, 1.4])
    with col1:
        full_name = st.text_input(txt("name"), placeholder="Juan Dela Cruz")
    with col2:
        email = st.text_input(txt("email"), placeholder="your@email.com")
    message = st.text_area(txt("why_join"), height=120, placeholder="Optional: Share your trading goal...")
    
    if st.form_submit_button(txt("submit"), type="primary", use_container_width=True):
        if email.strip():
            # You can add your real Supabase insert logic here later
            # Example: supabase.table("waitlist").insert({...}).execute()
            st.success(txt("success"))
        else:
            st.error("Email is required")

st.markdown("</div>", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# PIONEERS SECTION – horizontal carousel, premium circular cards, smooth UX
# ────────────────────────────────────────────────

st.markdown(f"""
<div class="glass-card" style="max-width:1200px; margin:3rem auto; padding:2.5rem 2rem;">
    <h2 style="text-align:center; margin-bottom:2.2rem;">{txt('pioneers_title')}</h2>

    <div class="pioneers-carousel-container">
        <button class="carousel-arrow left-arrow" onclick="document.querySelector('.pioneers-carousel').scrollBy({{left: -320, behavior: 'smooth'}})">‹</button>

        <div class="pioneers-carousel">
""", unsafe_allow_html=True)

pioneers = [
    {
        "name": "Weber",
        "since": "Dec 2025",
        "earnings": "+$1,284",
        "gain": "+128.4%",
        "quote": "Best decision ever!",
        "photo": "assets/weber.jpg"
    },
    {
        "name": "Ramil",
        "since": "Jan 2026",
        "earnings": "+$2,150",
        "gain": "+215%",
        "quote": "Stable daily profits.",
        "photo": "assets/ramil.jpg"
    },
    # You can add more here — they extend horizontally automatically
]

for p in pioneers:
    photo_url = p.get("photo", f"https://via.placeholder.com/140/222/ffd700?text={p['name'][0]}")
    st.markdown(f"""
    <div class="pioneer-card">
        <div class="card-inner">
            <div class="card-front">
                <img src="{photo_url}" class="pioneer-photo" alt="{p['name']}">
                <div class="pioneer-name">{p['name']}</div>
                <div class="pioneer-since">since {p['since']}</div>
            </div>
            <div class="card-back">
                <div class="earnings">{p['earnings']}</div>
                <div class="gain">{p['gain']}</div>
                <div class="quote">“{p['quote']}”</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<style>
    /* Pioneers – horizontal only, perfect circle photos */
    .pioneers-carousel-container {
        position: relative;
        overflow: hidden;
        padding: 1.5rem 0;
    }

    .pioneers-carousel {
        display: flex;
        flex-direction: row;
        flex-wrap: nowrap;
        gap: 2rem;
        overflow-x: auto;
        scroll-snap-type: x mandatory;
        scroll-behavior: smooth;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: none;
        padding: 1rem 0;
    }

    .pioneers-carousel::-webkit-scrollbar {
        display: none;
    }

    .pioneer-card {
        flex: 0 0 280px;
        width: 280px;
        min-width: 280px;
        height: 380px;
        border-radius: 24px;
        overflow: hidden;
        background: rgba(30,35,55,0.9);
        border: 1px solid rgba(255,215,0,0.2);
        box-shadow: 0 10px 30px rgba(0,0,0,0.45);
        transition: all 0.35s ease;
        scroll-snap-align: center;
    }

    .pioneer-card:hover {
        transform: translateY(-12px) scale(1.05);
        box-shadow: 0 20px 50px rgba(255,98,0,0.3);
    }

    .pioneer-photo {
        width: 140px;
        height: 140px;
        border-radius: 50%;
        border: 4px solid #ff6200;           /* orange border para match sa title */
        margin: 2.2rem auto 1.5rem;
        display: block;
        object-fit: cover;
        box-shadow: 0 6px 20px rgba(255,98,0,0.35);
    }

    .pioneer-name {
        font-size: 1.45rem;
        font-weight: 700;
        color: #ff6200;
        margin: 0.5rem 0;
    }

    .pioneer-since {
        font-size: 1rem;
        color: {text_muted};
        opacity: 0.9;
    }

    /* Force horizontal on small screens too */
    @media (max-width: 768px) {
        .pioneer-card {
            flex: 0 0 300px;
            min-width: 300px;
        }
    }

    @media (max-width: 480px) {
        .pioneer-card {
            flex: 0 0 90%;
            min-width: 90%;
            max-width: 360px;
            margin: 0 auto 1.5rem;
        }
        .pioneer-photo {
            width: 130px;
            height: 130px;
            margin: 2rem auto 1.2rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# ORIGIN STORY / JOURNEY (condensed version – shown by default)
# ────────────────────────────────────────────────
st.markdown("<div class='glass-card' style='padding:2rem 2.4rem;'>", unsafe_allow_html=True)
st.markdown("<h2 class='gold-text' style='text-align:center; margin-bottom:1.8rem;'>My Journey & Motivation</h2>", unsafe_allow_html=True)

journey_sections = [
    ("Origin & Motivation (2024)", """
Noong 2024, frustrated ako sa manual trading — paulit-ulit na losses dahil sa emotions, lack of discipline, at timing issues.
Realization: "Kung hindi professional, maloloss ka lang sa market."
Decided to build my own EA to remove human error, achieve consistency, and become a professional trader through automation.
Early inspiration came from ~2016 trading days, sharing ideas with friend Ramil.
    """),
    ("Development Phase (2024)", """
- Full year of self-study in MQL5 programming
- Trial-and-error: Combined multiple indicators, price action rules, risk management filters
- Hundreds of backtests, forward tests, debugging — almost 1 year of experiment before stability
    """),
    ("Official Launch & Early Testing (2025)", """
- January 2025: Breakthrough — EA fully functional and running smoothly. Officially named KMFX EA
- Focused exclusively on XAUUSD (GOLD) for its volatility and opportunities
- September 2025: Formed KMFX EA TESTER group (Weber most active, Ramil, Sheldon, Jai) — ~2 months forward testing
- Late 2025 (Oct-Dec): Mastered backtesting 2021–2025, polished entries/exits, added filters for news volatility
    """),
    ("Major Milestones & Tools (2025)", """
- October 15, 2025: Launched KMFX EA MT5 Client Tracker dashboard at kmfxea.streamlit.app
- December 2025: Pioneer community formed — 14 believers contributed ₱17,000 PHP (₱1,000 per unit)
  Profit sharing: 30% of profits proportional to units
  Thank you to: Mark, Jai, Doc, Weber (2 units), Don, Mark Fernandez (3 units), Ramil, Cristy, Meg, Roland, Mila, Malruz, Julius, Joshua
    """),
    ("FTMO Prop Firm Journey – First Attempt (Dec 2025 - Jan 2026)", """
- December 13, 2025: Started FTMO 10K Challenge
- December 26, 2025: **PASSED Phase 1 in just ~13 days!**
  Stats: $10,000 → $11,040.58 (+10.41%), 2.98% max DD, 118 trades (longs only), 52% win rate, +12,810.8 pips, profit factor 1.52
  Avg trade duration: ~43 minutes (scalping-style)
    """),
    ("Phase 2 (Verification) Attempt & Lesson", """
- Goal: 5% profit target with strict risk limits
- Outcome: Failed due to emotional intervention (manual adjustments out of fear)
- Key Insight: Untouched simulation (Jan 1–16, 2026) showed ~$2,000 additional gain — would have passed easily
- Big Lesson: Trust the System No Matter What. Emotions are the real enemy.
    """),
    ("Current Attempt (Jan 2026)", """
- New FTMO 10K Challenge (Phase 1) ongoing
- Full trust mode: 100% hands-off — no tweaks, no manual trades, pure automated execution
- Confidence high from previous pass and untouched sim results
    """),
    ("Dual Product Evolution (2026)", """
- Prop Firm Version (KMFX EA – Locked): Strict for FTMO/challenges, no intervention allowed
- Personal/Client Version (in progress): Same core strategy, more flexible for real accounts and clients
    """),
    ("Performance Proof", """
- FTMO Phase 1 Passed: +10.41%, 2.98% max DD
- 2025 Backtest: +187.97%
- 5-Year Backtest (2021-2025): +3,071%
- Safety First: 1% risk per trade, no martingale/grid, controlled drawdown
    """)
]

for title, content in journey_sections:
    st.markdown(f"<h3 class='gold-text' style='margin:1.8rem 0 0.8rem;'>{title}</h3>", unsafe_allow_html=True)
    st.markdown(content.strip(), unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# FULL JOURNEY EXPANDER (detailed 2014–2026 story with images)
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
        "<div class='glass-card' style='padding:3rem; margin:3rem auto; max-width:1100px; border-left:6px solid #ffd700;'>",
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
        f"<h3 style='color:{accent_gold}; text-align:center; font-size:1.8rem; margin:2.5rem 0 1rem;'>🌍 2014: The Beginning in Saudi Arabia</h3>",
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        try:
            img1 = make_same_size("assets/saudi1.jpg", target_width=800, target_height=700)
            if img1:
                st.image(img1, use_column_width=True, caption="Team Saudi Boys 🇸🇦")
        except:
            st.info("Image: assets/saudi1.jpg")
    with col2:
        try:
            img2 = make_same_size("assets/saudi2.jpg", target_width=800, target_height=700)
            if img2:
                st.image(img2, use_column_width=True, caption="Selfie with STC Cap")
        except:
            st.info("Image: assets/saudi2.jpg")

    st.markdown("""
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
        f"<h3 style='color:{accent_gold}; text-align:center; font-size:1.8rem; margin:3rem 0 1rem;'>🏠 2017: Umuwi sa Pinas at Crypto Era</h3>",
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        try:
            img = make_same_size("assets/family1.jpg", target_width=800, target_height=700)
            if img:
                st.image(img, use_column_width=True, caption="Date with her ❤️")
        except:
            pass
    with col2:
        try:
            img = make_same_size("assets/family2.jpg", target_width=800, target_height=700)
            if img:
                st.image(img, use_column_width=True, caption="Selfie My Family 👨‍👩‍👧")
        except:
            pass

    st.markdown("""
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
*Little did I know, 'yung mga losses at scams na 'yun ang magiging stepping stones para sa KMFX EA — natuto akong tanggalin emotions at mag-build ng system.*
    """)

    # 2019–2021: Pandemic Days & Biggest Lesson
    st.markdown(
        f"<h3 style='color:{accent_gold}; text-align:center; font-size:1.8rem; margin:3rem 0 1rem;'>🦠 2019–2021: Pandemic Days & Biggest Lesson</h3>",
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        try:
            img = make_same_size("assets/klever1.jpg", target_width=800, target_height=700)
            if img:
                st.image(img, use_column_width=True, caption="Part of Gain almost 20k$+ Max gain 🔥")
        except:
            pass
    with col2:
        try:
            img = make_same_size("assets/klever2.jpg", target_width=800, target_height=700)
            if img:
                st.image(img, use_column_width=True, caption="Klever Exchange Set Buy Sell Instant")
        except:
            pass

    st.markdown("""
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
        f"<h3 style='color:{accent_gold}; text-align:center; font-size:1.8rem; margin:3rem 0 1rem;'>🤖 2024–2025: The Professional Shift</h3>",
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        try:
            img = make_same_size("assets/ai1.jpg", target_width=800, target_height=700)
            if img:
                st.image(img, use_column_width=True, caption="New Tech Found")
        except:
            pass
    with col2:
        try:
            img = make_same_size("assets/ai2.jpg", target_width=800, target_height=700)
            if img:
                st.image(img, use_column_width=True, caption="Using Old Laptop to Build")
        except:
            pass

    st.markdown("""
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
        f"<h3 style='color:{accent_gold}; text-align:center; font-size:1.8rem; margin:3rem 0 1rem;'>🏆 2025–2026: FTMO Challenges & Comeback</h3>",
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        try:
            img = make_same_size("assets/ftmo.jpeg", target_width=800, target_height=700)
            if img:
                st.image(img, use_column_width=True, caption="Passed Phase 1 in 13 days! 🎉")
        except:
            pass
    with col2:
        try:
            img = make_same_size("assets/ongoing.jpg", target_width=800, target_height=700)
            if img:
                st.image(img, use_column_width=True, caption="Current challenge - full trust mode 🚀")
        except:
            pass

    st.markdown("""
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

    # Final Vision
    st.markdown(
        f"<h3 style='color:{accent_gold}; text-align:center; font-size:1.8rem; margin:3rem 0 1rem;'>✨ Realization & Future Vision</h3>",
        unsafe_allow_html=True,
    )

    # Vision image (full width)
    try:
        vision_img = Image.open("assets/journey_vision.jpg")
        st.image(
            vision_img,
            use_column_width=True,
            caption="Built by Faith, Shared for Generations 👑"
        )
    except Exception:
        st.info("Vision image: assets/journey_vision.jpg (place it in assets folder)")

    st.markdown("""
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

    if st.button("× Close Full Journey", type="primary", use_container_width=True):
        st.session_state.show_full_journey = False
        st.rerun()

st.markdown("</div>", unsafe_allow_html=True)
# ────────────────────────────────────────────────
# WHY CHOOSE KMFX EA? (complete benefits grid – 3 columns on desktop, stacks on mobile)
# ────────────────────────────────────────────────
st.markdown("<div class='glass-card' style='padding:2rem 2.4rem; margin:2.5rem auto;'>", unsafe_allow_html=True)
st.markdown("<h2 class='gold-text' style='text-align:center; margin-bottom:1.5rem;'>Why Choose KMFX EA?</h2>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align:center; opacity:0.9; font-size:1.25rem; margin-bottom:2rem;'>"
    "Hindi lang isa pang EA — ito ang automated system na galing sa totoong 12+ years journey, "
    "pinatunayan sa FTMO, at ginawa with discipline, persistence, at faith.</p>",
    unsafe_allow_html=True
)

benefits = [
    {
        "emoji": "👑",
        "title": "100% Hands-Off Automation",
        "points": [
            "Run and forget — walang kailangang galawin pag naka-set na",
            "Removes emotions completely (yung pinakamalaking killer sa trading)",
            "Pure MQL5 logic + strict risk rules = consistent execution"
        ]
    },
    {
        "emoji": "📈",
        "title": "Gold (XAUUSD) Focused Edge",
        "points": [
            "Optimized for Gold volatility — best market para sa scalping & swing",
            "+3,071% 5-Year Backtest • +187% 2025 • Low DD <3%",
            "Proven sa real FTMO challenge (Phase 1 passed in 13 days!)"
        ]
    },
    {
        "emoji": "🔒",
        "title": "Prop Firm Ready & Safe",
        "points": [
            "FTMO-compatible — strict no-martingale, no-grid, 1% risk per trade",
            "Locked version para sa challenges • Flexible personal version",
            "Full transparency: journey, stats, at community pioneer sharing"
        ]
    },
    {
        "emoji": "🙏",
        "title": "Built by Faith & Real Experience",
        "points": [
            "Galing sa 12 taon na totoong trading journey (2014 hanggang 2026)",
            "Hindi basta code — may purpose: tulungan ang marami sa financial freedom",
            "Discipline + surrender to God's plan = sustainable success"
        ]
    },
    {
        "emoji": "🤝",
        "title": "Pioneer Community & Sharing",
        "points": [
            "Early believers get proportional profit share (30% pool)",
            "Real accountability group — testers, pioneers, at future foundation",
            "Hindi solo — sama-sama tayo sa pag-scale ng empire"
        ]
    },
    {
        "emoji": "💰",
        "title": "Passive Income + Legacy Vision",
        "points": [
            "Goal: true passive income para mas maraming time sa pamilya at Lord",
            "Dream: KMFX EA Foundations — turuan ang aspiring traders maging pro",
            "Built by faith, shared for generations — legacy na hindi matitigil"
        ]
    }
]

# 3-column layout (stacks automatically on mobile/tablet)
cols = st.columns(3)
for i, benefit in enumerate(benefits):
    with cols[i % 3]:
        st.markdown(f"""
        <div style='text-align:center; padding:1.2rem 0.8rem;'>
            <div style='font-size:3.2rem; margin-bottom:0.8rem;'>{benefit['emoji']}</div>
            <h4 style='color:{accent_gold}; margin:0.6rem 0; font-size:1.25rem;'>{benefit['title']}</h4>
            <ul style='text-align:left; padding-left:1.4rem; margin:0.6rem 0 0; opacity:0.9; font-size:0.98rem;'>
                {''.join(f'<li style="margin:0.4rem 0; line-height:1.45;">{p}</li>' for p in benefit['points'])}
            </ul>
        </div>
        """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# IN-DEPTH QUESTIONS ABOUT KMFX EA (detailed FAQ – expandable)
# ────────────────────────────────────────────────
st.markdown("<div class='glass-card' style='padding:2rem 2.4rem; margin:2.5rem auto;'>", unsafe_allow_html=True)
st.markdown("<h2 class='gold-text' style='text-align:center; margin-bottom:1.5rem;'>In-Depth Questions About KMFX EA</h2>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align:center; opacity:0.9; margin-bottom:1.8rem;'>"
    "Diretsong sagot sa mga tanong ng seryosong traders — walang paligoy-ligoy, puro facts at transparency.</p>",
    unsafe_allow_html=True
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

for question, answer in faqs:
    with st.expander(question):
        st.markdown(answer.strip())

st.markdown("</div>", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# MEMBER LOGIN SECTION
# ────────────────────────────────────────────────
st.markdown("<div class='glass-card' style='text-align:center; padding:2.5rem; max-width:820px; margin:3rem auto;'>", unsafe_allow_html=True)
st.markdown("<h2 class='gold-text' style='margin-bottom:1.2rem;'>Already a Pioneer or Member?</h2>", unsafe_allow_html=True)

tab_owner, tab_admin, tab_client = st.tabs(["👑 Owner Login", "🛠️ Admin Login", "👥 Client Login"])

with tab_owner:
    with st.form("owner_login_form", clear_on_submit=True):
        owner_username = st.text_input("Username", placeholder="e.g. kingminted", key="owner_user")
        owner_password = st.text_input("Password", type="password", key="owner_pass")
        if st.form_submit_button("Login as Owner →", type="primary", use_container_width=True):
            success = login_user(owner_username.strip().lower(), owner_password, expected_role="owner")
            if success:
                st.success("Owner login successful!")
                st.session_state.role = "owner"
                st.switch_page("pages/👤_Admin_Management.py")
            else:
                st.error("Login failed – check credentials")

with tab_admin:
    with st.form("admin_login_form", clear_on_submit=True):
        admin_username = st.text_input("Username", placeholder="Admin username", key="admin_user")
        admin_password = st.text_input("Password", type="password", key="admin_pass")
        if st.form_submit_button("Login as Admin →", type="primary", use_container_width=True):
            success = login_user(admin_username.strip().lower(), admin_password, expected_role="admin")
            if success:
                st.success("Admin login successful!")
                st.session_state.role = "admin"
                st.switch_page("pages/👤_Admin_Management.py")
            else:
                st.error("Login failed – check credentials")

with tab_client:
    with st.form("client_login_form", clear_on_submit=True):
        client_username = st.text_input("Username", placeholder="Your username", key="client_user")
        client_password = st.text_input("Password", type="password", key="client_pass")
        if st.form_submit_button("Login as Client →", type="primary", use_container_width=True):
            success = login_user(client_username.strip().lower(), client_password, expected_role="client")
            if success:
                st.success("Welcome back!")
                st.session_state.role = "client"
                st.switch_page("pages/🏠_Dashboard.py")
            else:
                st.error("Login failed – check credentials")

st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown(f"""
<div style='text-align:center; margin:5rem 0 3rem; padding-top:2.5rem; border-top:1px solid rgba(255,215,0,0.2); opacity:0.8;'>
    <p>KMFX EA • Built by Faith, Powered by Discipline</p>
    <p>© 2026 Mark Jeff Blando • All rights reserved</p>
</div>
""", unsafe_allow_html=True)

if not is_authenticated():
    st.stop()