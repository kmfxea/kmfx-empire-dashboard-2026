# =====================================================================
# KMFX EA - PUBLIC LANDING + LOGIN PAGE (MULTI-PAGE ENTRY POINT)
# Updated with all Part 1 features: language toggle, forced dark public, SEO, etc.
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
# ADDITIONAL IMPORTS FOR NEW FEATURES
# ────────────────────────────────────────────────
import yfinance as yf
from datetime import datetime, timedelta
from streamlit_lightweight_charts import renderLightweightCharts

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
    # Hide sidebar completely on public page
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
# MULTI-PAGE REDIRECT LOGIC (your existing top logic)
# ────────────────────────────────────────────────
if authenticated:
    st.switch_page("pages/🏠_Dashboard.py")
else:
    if st.session_state.pop("logging_out", False):
        msg = st.session_state.pop("logout_message", None)
        if msg:
            st.success(msg)
        st.session_state.pop("_sidebar_rendered", None)
    
    # Hide sidebar again for safety on public
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
# QR AUTO-LOGIN (keep your existing block if still needed)
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
            st.switch_page("pages/🏠_Dashboard.py")
        else:
            st.error("Invalid or revoked QR code")
            st.query_params.clear()
    except Exception as e:
        st.error(f"QR login failed: {str(e)}")
        st.query_params.clear()

# ────────────────────────────────────────────────
# SESSION STATE INIT FOR NEW FEATURES
# ────────────────────────────────────────────────
if "language" not in st.session_state:
    st.session_state.language = "en"

if "show_journey_photos" not in st.session_state:
    st.session_state.show_journey_photos = False

# ────────────────────────────────────────────────
# LANGUAGE DICTIONARY
# ────────────────────────────────────────────────
texts = {
    "en": {
        "hero_title": "KMFX EA",
        "hero_sub": "Automated Gold Trading for Financial Freedom",
        "hero_desc": "Passed FTMO Phase 1 • +3,071% 5-Year Backtest • Building Legacies of Generosity",
        "join_waitlist": "Join the Waitlist – Early Access",
        "name": "Full Name",
        "email": "Email",
        "why_join": "Why do you want to join KMFX? (optional)",
        "submit": "Join Waitlist 👑",
        "success": "Success! You're on the list. Check your email soon 🚀",
        "pioneer_title": "Our Pioneers",
        "journey_title": "My Full Trading Journey (2014–2026)",
        "show_photos": "Tap to see journey pics 👀",
        "hide_photos": "Hide photos",
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
        "pioneer_title": "Mga Pioneer Namin",
        "journey_title": "Aking Kumpletong Paglalakbay sa Trading (2014–2026)",
        "show_photos": "Tap para makita ang mga larawan sa paglalakbay 👀",
        "hide_photos": "Itago ang mga larawan",
    }
}

def get_text(key):
    return texts[st.session_state.language].get(key, key)

# ────────────────────────────────────────────────
# FORCED DARK MODE + FULL CSS (public only)
# ────────────────────────────────────────────────
if not authenticated:
    st.session_state.theme = "dark"

st.markdown("""
<style>
    /* Deep luxury dark for public */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0a0d14 0%, #1a1a2e 100%) !important;
    }
    .stApp { background: transparent !important; }
    
    .glass-card {
        background: rgba(15, 20, 30, 0.78) !important;
        backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(255, 215, 0, 0.22) !important;
        border-radius: 20px !important;
        padding: 2.2rem !important;
        box-shadow: 0 10px 35px rgba(0,0,0,0.55) !important;
        transition: all 0.3s ease;
        margin: 2rem auto;
        max-width: 1100px;
    }
    .glass-card:hover {
        box-shadow: 0 15px 45px rgba(255,215,0,0.18) !important;
        transform: translateY(-4px);
    }
    
    .gold-text {
        color: #ffd700 !important;
        text-shadow: 0 0 12px rgba(255,215,0,0.7) !important;
    }
    
    h1, h2, h3 { color: #ffd700 !important; }
    p, div, span, label { color: #e0e0ff !important; }
    
    /* Mobile polish */
    @media (max-width: 768px) {
        h1 { font-size: 2.4rem !important; line-height: 1.1 !important; }
        .glass-card { padding: 1.6rem !important; max-width: 96% !important; margin: 1.2rem auto !important; }
        button { min-height: 52px !important; font-size: 1.1rem !important; }
        .stColumns { flex-direction: column !important; gap: 1.2rem !important; }
    }
    
    /* Flip card */
    .flip-card {
        perspective: 1000px;
        width: 180px;
        height: 240px;
        margin: 1.2rem auto;
    }
    .flip-card-inner {
        position: relative;
        width: 100%;
        height: 100%;
        transition: transform 0.65s;
        transform-style: preserve-3d;
    }
    .flip-card:hover .flip-card-inner,
    .flip-card:active .flip-card-inner {
        transform: rotateY(180deg);
    }
    .flip-card-front, .flip-card-back {
        position: absolute;
        width: 100%;
        height: 100%;
        backface-visibility: hidden;
        border-radius: 50%;
        background: #1e1e3c;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
        padding: 1rem;
        text-align: center;
    }
    .flip-card-back {
        transform: rotateY(180deg);
        background: linear-gradient(135deg, #2a2a50, #1e1e3c);
    }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# SEO META TAGS
# ────────────────────────────────────────────────
st.markdown("""
<meta property="og:title" content="KMFX EA – Automated Gold Trading | +3,071% 5-Year Backtest">
<meta property="og:description" content="Passed FTMO Phase 1 • Built by Mark Jeff Blando • Join the elite empire now – Early access waitlist open">
<meta property="og:image" content="https://your-supabase-public-url/assets/journey_vision.jpg">
<meta property="og:url" content="https://your-streamlit-app-url">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# LANGUAGE TOGGLE BUTTON (top right)
# ────────────────────────────────────────────────
col1, col2 = st.columns([9, 1])
with col2:
    if st.button("EN / TL", key="lang_toggle"):
        st.session_state.language = "tl" if st.session_state.language == "en" else "en"
        st.rerun()

# ────────────────────────────────────────────────
# END OF PART 1 – DITO NA MAGSISIMULA ANG LOGO / HERO / STATS MO
# Example: st.image("assets/logo.png", use_column_width=True)
# ────────────────────────────────────────────────
# ────────────────────────────────────────────────
# PART 2 – HERO SECTION + LIVE GOLD PRICE + MINI CHART + WAITLIST + PIONEERS
# Paste this RIGHT AFTER the language toggle block in Part 1
# ────────────────────────────────────────────────

# ================== LOGO (centered) ==================
logo_col = st.columns([1, 4, 1])[1]
with logo_col:
    st.image("assets/logo.png", use_column_width=True)

# ================== HERO SECTION ==================
st.markdown(f"""
<h1 class='gold-text' style='text-align:center; margin-bottom:0.5rem;'>
    {get_text('hero_title')}
</h1>
""", unsafe_allow_html=True)

st.markdown(f"""
<h2 style='text-align:center; color:#e0e0ff; margin:0.5rem 0;'>
    {get_text('hero_sub')}
</h2>
""", unsafe_allow_html=True)

st.markdown(f"""
<p style='text-align:center; font-size:1.4rem; color:#aaaaaa; margin-top:0.5rem;'>
    {get_text('hero_desc')}
</p>
""", unsafe_allow_html=True)

st.markdown("<p style='text-align:center; font-size:1.1rem; color:#888888;'>Mark Jeff Blando – Founder & Developer • 2026</p>", unsafe_allow_html=True)

# ================== LIVE GOLD PRICE METRIC ==================
@st.cache_data(ttl=30)  # refresh every 30 seconds
def get_gold_price():
    try:
        ticker = yf.Ticker("GC=F")
        info = ticker.info
        price = info.get('regularMarketPrice') or info.get('previousClose', 'N/A')
        change_pct = info.get('regularMarketChangePercent', 0)
        return price, change_pct
    except Exception:
        return 'N/A', 0

price, change = get_gold_price()

st.markdown("<div style='text-align:center; margin:1.5rem 0;'>", unsafe_allow_html=True)
st.metric(
    label="Live Gold Price (XAU/USD)",
    value=f"${price:,.2f}" if isinstance(price, (int, float)) else price,
    delta=f"{change:+.2f}%",
    delta_color="normal" if change >= 0 else "inverse"
)
st.markdown("</div>", unsafe_allow_html=True)

# ================== MINI GOLD CHART (7-day candlestick) ==================
@st.cache_data(ttl=300)  # refresh every 5 minutes
def get_gold_chart_data():
    try:
        end = datetime.now()
        start = end - timedelta(days=7)
        df = yf.download("GC=F", start=start, end=end, interval="1h")
        if df.empty:
            return []
        df = df[['Open', 'High', 'Low', 'Close']].reset_index()
        df['time'] = (df['Datetime'].astype('int64') // 10**9).astype(int)
        return [
            {
                "time": int(row['time']),
                "open": float(row['Open']),
                "high": float(row['High']),
                "low": float(row['Low']),
                "close": float(row['Close'])
            }
            for _, row in df.iterrows()
        ]
    except:
        return []

chart_data = get_gold_chart_data()

if chart_data:
    st.markdown("<h3 style='text-align:center; color:#ffd700; margin:1.5rem 0;'>Gold 7-Day Mini Chart</h3>", unsafe_allow_html=True)
    
    chart_options = {
        "width": "100%",
        "height": 280,
        "layout": {
            "background": {"color": "#1a1a2e"},
            "textColor": "#d1d4dc",
            "fontSize": 12
        },
        "grid": {
            "vertLines": {"color": "#334158"},
            "horzLines": {"color": "#334158"}
        },
        "timeScale": {
            "timeVisible": True,
            "secondsVisible": False,
            "borderColor": "#334158"
        },
        "rightPriceScale": {
            "borderColor": "#334158"
        }
    }
    
    renderLightweightCharts(
        [{
            "chart": chart_options,
            "series": [{
                "type": "Candlestick",
                "data": chart_data,
                "options": {
                    "upColor": "#26a69a",
                    "downColor": "#ef5350",
                    "borderVisible": False,
                    "wickUpColor": "#26a69a",
                    "wickDownColor": "#ef5350"
                }
            }]
        }],
        key="gold_mini_chart_public"
    )
else:
    st.info("Gold chart data temporarily unavailable – will retry soon.")

# ================== WAITLIST FORM ==================
st.markdown(f"""
<h3 style='text-align:center; color:#ffd700; margin:2.5rem 0 1rem;'>
    {get_text('join_waitlist')}
</h3>
""", unsafe_allow_html=True)

with st.form("waitlist_form_public", clear_on_submit=True):
    col_name, col_email = st.columns([1, 1.5])
    with col_name:
        full_name = st.text_input(get_text("name"), key="waitlist_name")
    with col_email:
        email = st.text_input(get_text("email"), placeholder="your@email.com", key="waitlist_email")
    
    message = st.text_area(get_text("why_join"), height=90, key="waitlist_message")
    
    submitted = st.form_submit_button(get_text("submit"), type="primary", use_container_width=True)

if submitted:
    if not email.strip():
        st.error("Email is required!")
    else:
        email_clean = email.strip().lower()
        try:
            # Check for duplicate
            existing = supabase.table("waitlist").select("id").eq("email", email_clean).execute()
            if existing.data:
                st.warning("This email is already registered. You'll receive updates soon!")
            else:
                insert_data = {
                    "full_name": full_name.strip() or None,
                    "email": email_clean,
                    "message": message.strip() or None,
                }
                response = supabase.table("waitlist").insert(insert_data).execute()
                if response.data:
                    st.success(get_text("success"))
                    st.balloons()
                else:
                    st.error("Failed to submit. Please try again or contact support.")
        except Exception as e:
            st.error(f"Error submitting waitlist: {str(e)}")

# ================== PIONEER FLIP CARDS SECTION ==================
st.markdown(f"""
<h2 class='gold-text' style='text-align:center; margin:3rem 0 1.5rem;'>
    {get_text('pioneer_title')}
</h2>
""", unsafe_allow_html=True)

# Fetch from Supabase
try:
    pioneers_resp = supabase.table("pioneers") \
        .select("*") \
        .eq("is_active", True) \
        .order("display_order") \
        .execute()
    pioneers = pioneers_resp.data or []
except Exception as e:
    st.warning(f"Could not load pioneers: {e}. Using fallback data.")
    pioneers = []

# Fallback if no data from DB
if not pioneers:
    pioneers = [
        {
            "name": "Weber",
            "since_date": "Dec 2025",
            "earnings": "+$1,284",
            "pct_gain": "+128.4%",
            "quote": "Best decision ever! Consistent gains with zero stress.",
            "photo_url": "assets/weber.jpg"  # ← siguraduhin na nandyan ang file
        },
        {
            "name": "Ramil",
            "since_date": "Jan 2026",
            "earnings": "+$2,150",
            "pct_gain": "+215%",
            "quote": "Stable daily profits. Trust the system!",
            "photo_url": "assets/ramil.jpg"
        },
        # Add more pioneers here with their actual photo paths/URLs
        # Example:
        # {
        #     "name": "Jai",
        #     "since_date": "Feb 2026",
        #     "earnings": "+$980",
        #     "pct_gain": "+98%",
        #     "quote": "Finally, no more emotional trading!",
        #     "photo_url": "assets/jai.jpg"
        # },
    ]

# Responsive columns (4 on desktop, 2-1 on mobile)
num_cols = min(4, len(pioneers)) if len(pioneers) > 1 else 1
p_cols = st.columns(num_cols)

for i, pioneer in enumerate(pioneers):
    with p_cols[i % num_cols]:
        photo_url = pioneer.get("photo_url", "https://via.placeholder.com/120?text=" + pioneer.get("name", "Pioneer")[0])
        
        st.markdown(f"""
        <div class="flip-card">
            <div class="flip-card-inner">
                <div class="flip-card-front">
                    <!-- Circular photo with subtle glow border -->
                    <div style="position:relative; width:120px; height:120px; margin:0 auto 12px;">
                        <img src="{photo_url}" 
                             style="width:100%; height:100%; border-radius:50%; object-fit:cover; 
                                    border:3px solid #ffd70033; box-shadow:0 0 15px rgba(255,215,0,0.4);">
                    </div>
                    <b style="font-size:1.1rem;">{pioneer.get('name', 'Pioneer')}</b><br>
                    <small style="opacity:0.8;">Pioneer since {pioneer.get('since_date', '2025')}</small>
                </div>
                <div class="flip-card-back">
                    <b style="font-size:1.3rem; color:#ffd700;">{pioneer.get('earnings', 'N/A')}</b><br>
                    <b style="font-size:1.1rem;">{pioneer.get('pct_gain', 'N/A')}</b><br>
                    <small style="opacity:0.9; font-style:italic;">"{pioneer.get('quote', 'Solid performer')}"</small>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ────────────────────────────────────────────────
# END OF PART 2
# Next (Part 3): Journey expander with lazy images + auto-rerun for live data
# ────────────────────────────────────────────────
# ────────────────────────────────────────────────
# PART 3 – COMPLETE PUBLIC LANDING PAGE FINISH (Journey → Why Choose → FAQs → Login → Footer → STOP)
# Paste this RIGHT AFTER the pioneer flip cards loop in your main.py
# This is the FULL ending — no placeholders, no missing parts
# ────────────────────────────────────────────────

# ================== JOURNEY EXPANDER with CLICK-TO-REVEAL LAZY IMAGES ==================
if "show_full_journey" not in st.session_state:
    st.session_state.show_full_journey = False

st.markdown(
    """
    <div class='glass-card' style='text-align:center; margin:5rem auto; padding:3rem; max-width:1100px;'>
        <h2 class='gold-text'>Want the Full Story Behind KMFX EA?</h2>
        <p style='font-size:1.4rem; opacity:0.9; margin:1rem 0;'>
            From OFW in Saudi to building an automated empire — built by faith, lessons, and persistence.
        </p>
    """,
    unsafe_allow_html=True
)

if st.button("👑 Read My Full Trading Journey (2014–2026)", type="primary", use_container_width=True):
    st.session_state.show_full_journey = True
    st.rerun()

if st.session_state.show_full_journey:
    st.markdown(
        """
        <div class='glass-card' style='padding:3rem; margin:3rem auto; max-width:1100px; border-left:6px solid #ffd700;'>
            <h2 class='gold-text' style='text-align:center;'>My Trading Journey: From 2014 to KMFX EA 2026</h2>
            <p style='text-align:center; font-style:italic; font-size:1.3rem; opacity:0.9;'>
                Ako si <strong>Mark Jeff Blando</strong> (Codename: <em>Kingminted</em>) — 
                simula 2014 hanggang ngayon 2026, pinagdaanan ko ang lahat: losses, wins, scams, pandemic gains, 
                at sa wakas, pagbuo ng sariling automated system.<br><br>
                Ito ang kwento ko — <strong>built by faith, shared for generations</strong>.
            </p>
        """,
        unsafe_allow_html=True
    )

    # 2014: Saudi Arabia
    st.markdown(
        "<h3 style='color:#ffd700; text-align:center; font-size:1.8rem; margin:2.5rem 0 1rem;'>🌍 2014: The Beginning in Saudi Arabia</h3>",
        unsafe_allow_html=True
    )
    col1, col2 = st.columns(2)
    with col1:
        st.image("assets/saudi1.jpg", use_column_width=True, caption="Team Saudi Boys 🇸🇦")
    with col2:
        st.image("assets/saudi2.jpg", use_column_width=True, caption="Selfie with STC Cap")
    st.write("""
Noong 2014, nandoon ako sa Saudi Arabia bilang Telecom Technician sa STC.
Everyday routine: work sa site, init ng desert... pero tuwing Friday — off day ko — may oras akong mag-explore online.
Nag-start ako mag-search ng ways para magdagdag ng income. Alam mo naman OFW life: padala sa pamilya, savings, pero gusto ko rin ng something para sa future.
Dun ko natuklasan ang Philippine stock market. Nagbukas ako ng account sa First Metro Sec, nag-download ng app, nagbasa ng news, PSE index... at sinubukan lahat ng basic — buy low sell high, tips sa forums, trial-and-error.
Emotions? Grabe. Sobrang saya kapag green — parang nanalo sa lotto! Pero kapag red? Lungkot talaga, "sayang 'yung overtime ko."
Paulit-ulit 'yun — wins, losses, lessons. Hindi pa seryoso noon, more like hobby lang habang nasa abroad... pero dun talaga nagsimula ang passion ko sa trading.
Around 2016, naging close friends ko sina Ramil, Mheg, at Christy. Nagsha-share kami ng ideas sa chat, stock picks, charts kahit liblib na oras.
Yun 'yung simula ng "team" feeling — hindi pa pro, pero may spark na.
    """)

    # 2017: Umuwi sa Pinas & Crypto
    st.markdown(
        "<h3 style='color:#ffd700; text-align:center; font-size:1.8rem; margin:2.5rem 0 1rem;'>🏠 2017: Umuwi sa Pinas at Crypto Era</h3>",
        unsafe_allow_html=True
    )
    col1, col2 = st.columns(2)
    with col1:
        st.image("assets/family1.jpg", use_column_width=True, caption="Date with her ❤️")
    with col2:
        st.image("assets/family2.jpg", use_column_width=True, caption="Selfie My Family 👨‍👩‍👧")
    st.write("""
Noong 2017, desisyon ko na — umuwi na ako sa Pilipinas para mag-start ng family life.
Matagal na rin akong OFW, at 30+ na si misis 😊. Gusto ko nang makasama sila araw-araw, hindi na video call lang tuwing weekend.
Yung feeling ng pagbalik? Airport pickup, yakap ng pamilya, settle sa Quezon City. Parang fresh start — walang desert heat, puro quality time na.
Pero dun din sumabog ang crypto wave! Bitcoin skyrocket hanggang ₱1M+ — grabe 'yung hype!
From stock learnings ko sa PSE, na-curious ako agad. 24/7 market kasi — mas madali mag-trade kahit busy sa bahay.
Ginamit ko 'yung basics: charts, news, patterns. Pero newbie pa rin talaga ako sa crypto.
Na-scam ako sa Auroramining (fake cloud mining). Sinubukan futures — leverage, high risk, manalo bigla tapos natatalo rin agad.
Walang solid strategy pa, walang discipline. Emosyon ang nagdedesisyon: FOMO kapag pump, panic kapag dump.
Paulit-ulit na cycle ng highs at lows... pero dun talaga natuto ako ng malalim na lessons sa volatility at risk.
Yung panahon na 'yun: mix ng saya sa family life at excitement (at sakit) sa crypto world.
    """)

    # 2019–2021: Pandemic & Klever
    st.markdown(
        "<h3 style='color:#ffd700; text-align:center; font-size:1.8rem; margin:2.5rem 0 1rem;'>🦠 2019–2021: Pandemic Days & Biggest Lesson</h3>",
        unsafe_allow_html=True
    )
    col1, col2 = st.columns(2)
    with col1:
        st.image("assets/klever1.jpg", use_column_width=True, caption="Part of Gain almost 20k$+ Max gain 🔥")
    with col2:
        st.image("assets/klever2.jpg", use_column_width=True, caption="Klever Exchange Set Buy Sell Instant")
    st.write("""
Noong 2019 hanggang 2021, dumating ang pandemic — isa sa pinakamahaba sa mundo.
Lahat kami nasa bahay, walang labas, puro quarantine.
Pero sa gitna ng gulo, natagpuan ko 'yung Klever token (KLV). May feature na "Ninja Move" — set buy order tapos instant sell sa target.
Ginawa ko 'yun religiously — sobrang laki ng gains! Kasama ko si Michael, nag-team up kami, nag-celebrate sa chat kapag green.
Pero bigla, glitch sa platform — half lang ng profits 'yung nabalik. Sakit sa puso 'yun.
D un dumating ang pinakamalaking realization: May pera talaga sa market kung may right strategy + discipline + emotion control.
After 2021 crash (BTC 60k → 20k) — market bloodbath. Dun ako nag-decide: lumayo muna, mag-reflect, mag-heal, mag-build ng matibay na foundation.
    """)

    # 2024–2025: EA Build
    st.markdown(
        "<h3 style='color:#ffd700; text-align:center; font-size:1.8rem; margin:2.5rem 0 1rem;'>🤖 2024–2025: The Professional Shift</h3>",
        unsafe_allow_html=True
    )
    col1, col2 = st.columns(2)
    with col1:
        st.image("assets/ai1.jpg", use_column_width=True, caption="New Tech Found")
    with col2:
        st.image("assets/ai2.jpg", use_column_width=True, caption="Using Old Laptop to Build")
    st.write("""
Noong 2024-2025, biglang nauso ang AI sa lahat — news, work, trading.
Nakita ko 'yung potential: bakit hindi gamitin 'yung tech para tanggalin 'yung human weaknesses?
Dun ko naisip: oras na gumawa ng sariling Expert Advisor (EA).
Buong halos isang taon akong nag-self-study ng MQL5 programming. Gabi-gabi, after work at family time — nakaupo sa laptop, nagbabasa, nanonood tutorials, nagko-code, nagde-debug.
Pinagsama ko lahat ng natutunan mula 2014: stock basics, crypto volatility, pandemic lessons, Klever moves, at lahat ng sakit sa manual trading.
January 2025: Breakthrough! Fully working na 'yung KMFX EA — focused sa Gold (XAUUSD).
Agad testing kasama sina Weber (super active), Jai, Sheldon, Ramil. Real-time results, adjustments.
End of 2025: Pioneer community formed — mga believers na sumali at naging part ng journey.
    """)

    # FTMO Journey
    st.markdown(
        "<h3 style='color:#ffd700; text-align:center; font-size:1.8rem; margin:2.5rem 0 1rem;'>🏆 2025–2026: FTMO Challenges & Comeback</h3>",
        unsafe_allow_html=True
    )
    col1, col2 = st.columns(2)
    with col1:
        st.image("assets/ftmo.jpeg", use_column_width=True, caption="Passed Phase 1 in 13 days! 🎉")
    with col2:
        st.image("assets/ongoing.jpg", use_column_width=True, caption="Current challenge - full trust mode 🚀")
    st.write("""
December 13, 2025: Start ng first 10K Challenge.
December 26, 2025: PASSED Phase 1 in 13 days! +10.41% gain, 2.98% max DD.
Pero Phase 2: Failed — emotional intervention.
Key insight: Untouched sim run = +$2,000 more — madali sanang na-pass.
Big lesson: Emotions ang tunay na kalaban. Full trust lang — run and forget mode.
January 2026: New challenge — 100% hands-off, pure automated.
Confidence high. Comeback stronger — para sa legacy, community, financial freedom.
    """)

    # Lazy Image Reveal
    st.markdown("<h4 style='text-align:center; color:#ffd700; margin:3rem 0 1.5rem;'>Journey Highlights – Tap to Reveal Photos</h4>", unsafe_allow_html=True)

    if not st.session_state.show_journey_photos:
        if st.button(get_text("show_photos"), type="primary", use_container_width=True):
            st.session_state.show_journey_photos = True
            st.rerun()

    if st.session_state.show_journey_photos:
        photo_pairs = [
            ("Saudi Arabia Days (2014)", "assets/saudi1.jpg", "assets/saudi2.jpg", "Team Saudi Boys 🇸🇦", "Selfie with STC Cap"),
            ("Family Life (2017)", "assets/family1.jpg", "assets/family2.jpg", "Date with her ❤️", "Selfie My Family 👨‍👩‍👧"),
            ("Klever Era Gains (2019–2021)", "assets/klever1.jpg", "assets/klever2.jpg", "Part of Gain almost 20k$+ Max gain 🔥", "Klever Exchange Set Buy Sell Instant"),
            ("FTMO & Current Phase (2025–2026)", "assets/ftmo.jpeg", "assets/ongoing.jpg", "Passed Phase 1 in 13 days! 🎉", "Current challenge - full trust mode 🚀"),
        ]

        for title, img1, img2, cap1, cap2 in photo_pairs:
            st.markdown(f"<p style='text-align:center; font-weight:bold; margin:2rem 0 1rem;'>{title}</p>", unsafe_allow_html=True)
            cols = st.columns(2)
            with cols[0]:
                st.markdown(f'<img src="{img1}" loading="lazy" style="width:100%; border-radius:12px; box-shadow:0 4px 15px rgba(0,0,0,0.4);">', unsafe_allow_html=True)
                st.caption(cap1)
            with cols[1]:
                st.markdown(f'<img src="{img2}" loading="lazy" style="width:100%; border-radius:12px; box-shadow:0 4px 15px rgba(0,0,0,0.4);">', unsafe_allow_html=True)
                st.caption(cap2)

        if st.button(get_text("hide_photos"), use_container_width=True):
            st.session_state.show_journey_photos = False
            st.rerun()

    # Vision Image
    st.markdown("<h3 style='color:#ffd700; text-align:center; margin:3rem 0 1rem;'>✨ Realization & Future Vision</h3>", unsafe_allow_html=True)
    st.image("assets/journey_vision.jpg", use_column_width=True, caption="Built by Faith, Shared for Generations 👑")

    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("Close Journey", use_container_width=True):
        st.session_state.show_full_journey = False
        st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

# ================== WHY CHOOSE KMFX EA? ==================
st.markdown(
    """
    <div class='glass-card' style='margin:4rem auto; padding:3rem; max-width:1100px;'>
        <h2 class='gold-text' style='text-align:center;'>Why Choose KMFX EA?</h2>
        <p style='text-align:center; opacity:0.9; font-size:1.3rem; margin-bottom:3rem;'>
            Hindi lang isa pang EA — ito ang automated system na galing sa totoong 12+ years journey, 
            pinatunayan sa FTMO, at ginawa with discipline, persistence, at faith.
        </p>
    """,
    unsafe_allow_html=True
)

why_cols = st.columns(3)
benefits = [
    {"emoji": "👑", "title": "100% Hands-Off Automation", "desc": "Run and forget — walang kailangang galawin pag naka-set na. Removes emotions completely."},
    {"emoji": "📈", "title": "Gold Focused Edge", "desc": "+3,071% 5-Year Backtest • Proven sa real FTMO Phase 1 pass."},
    {"emoji": "🔒", "title": "Prop Firm Ready & Safe", "desc": "FTMO-compatible — strict no-martingale, 1% risk per trade."},
    {"emoji": "🙏", "title": "Built by Faith & Real Experience", "desc": "Galing sa 12 taon na totoong trading journey."},
    {"emoji": "🤝", "title": "Pioneer Community", "desc": "Early believers get proportional profit share."},
    {"emoji": "💰", "title": "Passive Income Vision", "desc": "Goal: true passive income para mas maraming time sa pamilya."},
]

for i, b in enumerate(benefits):
    with why_cols[i % 3]:
        st.markdown(f"""
            <div style='text-align:center; padding:1.5rem;'>
                <div style='font-size:3.5rem; margin-bottom:1rem;'>{b['emoji']}</div>
                <h4 style='color:#ffd700; margin:0.8rem 0;'>{b['title']}</h4>
                <p style='opacity:0.9;'>{b['desc']}</p>
            </div>
        """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ================== IN-DEPTH FAQs ==================
st.markdown(
    """
    <div class='glass-card' style='margin:4rem auto; padding:3rem; max-width:1100px;'>
        <h2 class='gold-text' style='text-align:center;'>In-Depth Questions About KMFX EA</h2>
        <p style='text-align:center; opacity:0.9; font-size:1.2rem; margin-bottom:2.5rem;'>
            Diretsong sagot sa mga tanong na tinatanong ng mga seryosong traders — walang paligoy-ligoy, puro facts at transparency.
        </p>
    """,
    unsafe_allow_html=True
)

faqs = [
    ("Ano ang edge ng KMFX EA kumpara sa ibang Gold EAs?", "Tunay na focused sa XAUUSD volatility patterns na pinag-aralan mula 2021–2025 backtests. Walang over-optimization — daan-daang forward tests + real FTMO proof."),
    ("Paano napatunayan na hindi overfitted?", "5-Year Backtest (2021–2025): +3,071% na may realistic slippage & spread. Real FTMO Phase 1 pass — hindi lang curve-fitted."),
    ("Ano ang worst-case drawdown?", "Max historical DD ~12–15% sa malalakas na crashes. Real FTMO: 2.98% max DD lang."),
    ("Paano kung magbago ang market?", "May adaptive filters (news volatility, session checks, momentum rules). Regular forward testing at community feedback."),
    ("Paano sumali o makakuha ng access?", "Available sa community members at trusted users. May profit-sharing model base sa contribution."),
    ("May plan ba magdagdag ng ibang pairs?", "Gold lang muna para focused at optimized. Future versions: possible multi-pair pag na-master na ang Gold edge."),
    ("Paano i-backtest o i-verify?", "Pwede — may documented stats, sample reports, at live metrics sa dashboard."),
    ("Ano ang exit strategy?", "Auto DD limits + manual override option. Community feedback loop — kung underperform, titigil o i-a-adjust."),
    ("Paano pinoprotektahan laban sa piracy?", "Encrypted license key, MT5 login binding, revoke capability kung violation."),
    ("Ano ang ultimate vision?", "Build KMFX EA Foundations: education + tools para sa aspiring Pinoy traders. Scale sa multiple accounts + legacy."),
]

for question, answer in faqs:
    with st.expander(question):
        st.write(answer)

st.markdown("</div>", unsafe_allow_html=True)

# ================== SECURE MEMBER LOGIN SECTION ==================
st.markdown(
    """
    <div class='glass-card' style='text-align:center; margin:5rem auto; padding:4rem; max-width:800px;'>
        <h2 class='gold-text'>Already a Pioneer or Member?</h2>
        <p style='font-size:1.4rem; opacity:0.9; margin-bottom:2rem;'>
            Access your elite dashboard, realtime balance, profit shares, EA versions, and empire tools
        </p>
    """,
    unsafe_allow_html=True
)

# Tabs for role-based login
tab_owner, tab_admin, tab_client = st.tabs(["👑 Owner Login", "🛠️ Admin Login", "👥 Client / Pioneer Login"])

# ── OWNER LOGIN ────────────────────────────────────────────────
with tab_owner:
    with st.form("owner_login_form", clear_on_submit=True):
        st.markdown("<p style='opacity:0.8; margin-bottom:1rem;'>Owner-only access (Mark Jeff / Admin level)</p>", unsafe_allow_html=True)
        owner_username = st.text_input("Username", placeholder="e.g. kingminted", key="owner_username")
        owner_password = st.text_input("Password", type="password", placeholder="Enter your password", key="owner_password")
        submit_owner = st.form_submit_button("Login as Owner →", type="primary", use_container_width=True)

    if submit_owner:
        if not owner_username.strip() or not owner_password:
            st.error("Username and password are required.")
        else:
            success = login_user(owner_username.strip().lower(), owner_password, expected_role="owner")
            if success:
                st.success("Owner login successful! Redirecting to admin panel...")
                st.session_state.role = "owner"
                time.sleep(0.8)  # small delay for success message visibility
                st.switch_page("pages/👤_Admin_Management.py")
            else:
                st.error("Login failed – invalid credentials or role mismatch.")

# ── ADMIN LOGIN ────────────────────────────────────────────────
with tab_admin:
    with st.form("admin_login_form", clear_on_submit=True):
        st.markdown("<p style='opacity:0.8; margin-bottom:1rem;'>Admin access (management & monitoring)</p>", unsafe_allow_html=True)
        admin_username = st.text_input("Username", placeholder="Your admin username", key="admin_username")
        admin_password = st.text_input("Password", type="password", placeholder="Enter your password", key="admin_password")
        submit_admin = st.form_submit_button("Login as Admin →", type="primary", use_container_width=True)

    if submit_admin:
        if not admin_username.strip() or not admin_password:
            st.error("Username and password are required.")
        else:
            success = login_user(admin_username.strip().lower(), admin_password, expected_role="admin")
            if success:
                st.success("Admin login successful! Redirecting to management panel...")
                st.session_state.role = "admin"
                time.sleep(0.8)
                st.switch_page("pages/👤_Admin_Management.py")
            else:
                st.error("Login failed – invalid credentials or role mismatch.")

# ── CLIENT / PIONEER LOGIN ──────────────────────────────────────
with tab_client:
    with st.form("client_login_form", clear_on_submit=True):
        st.markdown("<p style='opacity:0.8; margin-bottom:1rem;'>Client / Pioneer access (dashboard & profit sharing)</p>", unsafe_allow_html=True)
        client_username = st.text_input("Username", placeholder="Your username", key="client_username")
        client_password = st.text_input("Password", type="password", placeholder="Enter your password", key="client_password")
        submit_client = st.form_submit_button("Login as Client →", type="primary", use_container_width=True)

    if submit_client:
        if not client_username.strip() or not client_password:
            st.error("Username and password are required.")
        else:
            success = login_user(client_username.strip().lower(), client_password, expected_role="client")
            if success:
                st.success("Welcome back! Redirecting to your personal dashboard...")
                st.session_state.role = "client"
                time.sleep(0.8)
                st.switch_page("pages/🏠_Dashboard.py")
            else:
                st.error("Login failed – invalid credentials or role mismatch.")

st.markdown("</div>", unsafe_allow_html=True)

# ================== FINAL FOOTER ==================
st.markdown(
    """
    <div style='text-align:center; margin:5rem 0 3rem; padding:2rem; opacity:0.7; font-size:0.95rem; border-top:1px solid rgba(255,215,0,0.15);'>
        <p style='margin-bottom:0.5rem;'>KMFX EA • Built by Faith, Powered by Discipline</p>
        <p style='margin:0.5rem 0;'>Mark Jeff Blando © 2026 • All rights reserved</p>
        <small>For inquiries or support: <a href="mailto:admin@kmfxea.com" style="color:#ffd700;">admin@kmfxea.com</a></small>
    </div>
    """,
    unsafe_allow_html=True
)

# ================== FINAL STOP – Prevent access to authenticated pages for public users ==================
if not is_authenticated():
    st.stop()