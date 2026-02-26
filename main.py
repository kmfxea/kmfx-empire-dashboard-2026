# main.py - KMFX EA Public Landing + Login Page (Updated Feb 2026 with TradingView realtime gold widget)
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
accent_gold   = "#ffd700"
accent_glow   = "#ffd70050"
accent_primary = "#00ffaa"
accent_hover = "#ffea80"
bg_color      = "#0d1117"
card_bg       = "rgba(20, 25, 40, 0.88)"
border_color  = "rgba(255,215,0,0.22)"
text_primary  = "#e2e8f0"
text_muted    = "#a0aec0"
card_shadow   = "0 8px 32px rgba(0,0,0,0.55)"

# ────────────────────────────────────────────────
# IMPROVED CSS
# ────────────────────────────────────────────────
st.markdown(f"""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">
<style>
    html, body, [class*="css-"] {{
        font-family: 'Inter', system-ui, sans-serif !important;
        font-size: 16px !important;
        line-height: 1.65;
    }}
    .stApp {{
        background: {bg_color};
        color: {text_primary};
    }}
    .main .block-container {{
        max-width: 1140px !important;
        padding: 1.5rem 2.5rem !important;
        margin: 0 auto !important;
    }}
    h1, h2, h3, h4 {{
        font-family: 'Playfair Display', serif;
        color: {accent_gold} !important;
        letter-spacing: 0.6px;
        text-shadow: 0 0 14px {accent_glow};
    }}
    h1 {{ font-size: 3.4rem; margin: 1.4rem 0 0.8rem; text-align: center; }}
    h2 {{ font-size: 2.5rem; margin: 2.5rem 0 1.2rem; text-align: center; }}
    h3 {{ font-size: 2rem; margin: 2rem 0 1rem; }}
    p, div, span, label {{
        color: {text_primary};
    }}
    small, .muted {{
        color: {text_muted};
    }}
    .glass-card {{
        background: {card_bg};
        backdrop-filter: blur(18px);
        border-radius: 16px;
        border: 1px solid {border_color};
        padding: 2.2rem 2.6rem;
        box-shadow: {card_shadow};
        margin: 2rem auto;
        transition: all 0.3s ease;
    }}
    .glass-card:hover {{
        box-shadow: 0 14px 40px {accent_glow};
        transform: translateY(-5px);
    }}
    button[kind="primary"] {{
        background: linear-gradient(90deg, {accent_primary}, {accent_hover}) !important;
        color: #000 !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 1rem 2rem !important;
        font-size: 1.15rem !important;
        font-weight: 600 !important;
        box-shadow: 0 5px 18px {accent_glow} !important;
    }}
    button[kind="primary"]:hover {{
        background: {accent_hover} !important;
        box-shadow: 0 10px 30px {accent_glow} !important;
        transform: translateY(-3px);
    }}
    header[data-testid="stHeader"] {{ background: {bg_color} !important; }}
    section[data-testid="stSidebar"] {{ display: none !important; }}
    .stForm > div {{ gap: 1.2rem !important; }}
    @media (max-width: 992px) {{
        .main .block-container {{ padding: 1.2rem 1.6rem !important; }}
        h1 {{ font-size: 2.8rem !important; }}
        h2 {{ font-size: 2.1rem !important; }}
    }}
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# LANGUAGE TOGGLE
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

c1, c2 = st.columns([9,1])
with c2:
    if st.button("EN / TL", key="lang_toggle"):
        st.session_state.language = "tl" if st.session_state.language == "en" else "en"
        st.rerun()

# ────────────────────────────────────────────────
# LOGO + HERO
# ────────────────────────────────────────────────
st.image("assets/logo.png", width=260, use_column_width=False)

st.markdown(f"""
<h1>{txt('hero_title')}</h1>
<h2>{txt('hero_sub')}</h2>
<p style='text-align:center; font-size:1.3rem; color:{text_muted}; max-width:760px; margin:1.2rem auto;'>
    {txt('hero_desc')}
</p>
<p style='text-align:center; color:{text_muted}; font-size:1.1rem;'>
    Mark Jeff Blando – Founder & Developer • 2026
</p>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# LIVE GOLD PRICE + REALTIME TRADINGVIEW MINI CHART
# ────────────────────────────────────────────────
@st.cache_data(ttl=25)
def get_gold_price():
    try:
        t = yf.Ticker("GC=F").info
        price = t.get('regularMarketPrice') or t.get('previousClose')
        ch = t.get('regularMarketChangePercent', 0)
        return price, ch
    except:
        return None, 0

price, change = get_gold_price()

if price:
    st.markdown(f"""
    <div style="text-align:center; font-size:3.5rem; font-weight:700; color:{accent_gold}; 
                text-shadow:0 0 18px {accent_glow}; margin:1.8rem 0 0.6rem;">
        ${price:,.1f}
    </div>
    <p style="text-align:center; font-size:1.4rem; margin:0;">
        <span style="color:{'#00ffaa' if change >= 0 else '#ff5555'}; font-weight:600;">
            {change:+.2f}%
        </span> • Live Gold (XAU/USD)
    </p>
    """, unsafe_allow_html=True)

# TradingView Realtime Mini Chart (modern web component)
st.components.v1.html("""
<div class="tradingview-widget-container" style="height:180px; width:100%; margin:1.5rem auto 2.5rem;">
  <tv-mini-chart 
    symbol="OANDA:XAUUSD" 
    color-theme="dark" 
    locale="en" 
    autosize 
  ></tv-mini-chart>
  <script type="module" src="https://widgets.tradingview-widget.com/w/en/tv-mini-chart.js" async></script>
</div>
""", height=200)

# ────────────────────────────────────────────────
# WAITLIST FORM – nicer look
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
            # → Insert your Supabase logic here ←
            st.success(txt("success"))
        else:
            st.error("Email is required")

st.markdown("</div>", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# PIONEERS (compact flip cards)
# ────────────────────────────────────────────────
st.markdown("<div class='glass-card' style='padding:1.8rem 2rem;'>", unsafe_allow_html=True)
st.markdown(f"<h2 style='text-align:center; margin-bottom:1.6rem;'>{txt('pioneers_title')}</h2>", unsafe_allow_html=True)

pioneers = [
    {"name":"Weber", "since":"Dec 2025", "earnings":"+$1,284", "gain":"+128.4%", "quote":"Best decision ever!", "photo":"assets/weber.jpg"},
    {"name":"Ramil", "since":"Jan 2026", "earnings":"+$2,150", "gain":"+215%", "quote":"Stable daily profits.", "photo":"assets/ramil.jpg"},
    # Pwede kang magdagdag dito ng marami pang pioneers kung gusto mo
    # Halimbawa:
    # {"name":"Sheldon", "since":"Feb 2026", "earnings":"+$980", "gain":"+98%", "quote":"Consistent and stress-free", "photo":"assets/sheldon.jpg"},
]

cols = st.columns(min(4, len(pioneers)))
for i, p in enumerate(pioneers):
    with cols[i]:
        photo = p.get("photo", f"https://via.placeholder.com/110/222/ffd700?text={p['name'][0]}")
        st.markdown(f"""
        <div class="flip-card" style="margin:0 auto; max-width:220px;">
            <div class="flip-card-inner">
                <div class="flip-card-front">
                    <img src="{photo}" class="circular" style="width:100px; height:100px; object-fit:cover;">
                    <div style="font-weight:600; margin:0.6rem 0 0.3rem; font-size:1.1rem;">{p['name']}</div>
                    <small style="opacity:0.8;">Pioneer since {p['since']}</small>
                </div>
                <div class="flip-card-back">
                    <div style="font-size:1.5rem; color:{accent_gold}; font-weight:700; margin-bottom:0.4rem;">{p['earnings']}</div>
                    <div style="font-size:1.2rem; font-weight:600; margin-bottom:0.4rem;">{p['gain']}</div>
                    <small style="font-style:italic; opacity:0.9;">"{p['quote']}"</small>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# ORIGIN STORY / JOURNEY (condensed spacing)
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
# FULL JOURNEY EXPANDER (with improved spacing inside)
# ────────────────────────────────────────────────
if "show_full_journey" not in st.session_state:
    st.session_state.show_full_journey = False

st.markdown("<div class='glass-card' style='text-align:center; padding:2rem;'>", unsafe_allow_html=True)
st.markdown("<h2 style='margin-bottom:1rem;'>Want the Full Story Behind KMFX EA?</h2>", unsafe_allow_html=True)
st.markdown("<p style='font-size:1.35rem; opacity:0.9; margin-bottom:1.5rem;'>From OFW in Saudi to building an automated empire...</p>", unsafe_allow_html=True)

if st.button("👑 Read My Full Trading Journey (2014–2026)", type="primary", use_container_width=True):
    st.session_state.show_full_journey = True
    st.rerun()

if st.session_state.show_full_journey:
    st.markdown("<div style='border-left:5px solid #ffd700; padding:1.8rem; background:rgba(20,25,40,0.9); border-radius:12px;'>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; margin-bottom:2rem;'>My Trading Journey: From 2014 to KMFX EA 2026</h2>", unsafe_allow_html=True)

    # 2014 Section
    st.markdown(f"<h3 style='color:{accent_gold}; text-align:center; margin:1.5rem 0;'>🌍 2014: The Beginning in Saudi Arabia</h3>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        resized1 = make_same_size("assets/saudi1.jpg", target_width=800, target_height=700)
        if resized1: st.image(resized1, use_column_width=True, caption="Team Saudi Boys 🇸🇦")
    with col2:
        resized2 = make_same_size("assets/saudi2.jpg", target_width=800, target_height=700)
        if resized2: st.image(resized2, use_column_width=True, caption="Selfie with STC Cap")
    st.markdown("Your 2014 story text here... (paste your full 2014 paragraph)", unsafe_allow_html=True)

    # ... (ilagay mo na rin yung ibang years tulad ng 2017, 2019-2021, etc. kung gusto mo buong detailed expander)
    # Para hindi masyadong mahaba ang sagot, iniwan ko yung structure lang. Pwede mong i-paste yung full content mo rito.

    # Realization & Vision
    st.markdown(f"<h3 style='color:{accent_gold}; text-align:center; margin:2rem 0 1rem;'>✨ Realization & Future Vision</h3>", unsafe_allow_html=True)
    try:
        vision_image = Image.open("assets/journey_vision.jpg")
        st.image(vision_image, use_column_width=True, caption="Built by Faith, Shared for Generations 👑")
    except:
        st.info("assets/journey_vision.jpg not found")

    st.markdown("Your final realization paragraph here...", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("Close Journey", use_container_width=True):
        st.session_state.show_full_journey = False
        st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# WHY CHOOSE KMFX EA? (complete benefits list)
# ────────────────────────────────────────────────
st.markdown("<div class='glass-card' style='padding:2rem 2.4rem; margin:2.5rem auto;'>", unsafe_allow_html=True)
st.markdown("<h2 class='gold-text' style='text-align:center; margin-bottom:1.5rem;'>Why Choose KMFX EA?</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; opacity:0.9; font-size:1.25rem; margin-bottom:2rem;'>"
            "Hindi lang isa pang EA — ito ang automated system na galing sa totoong 12+ years journey, "
            "pinatunayan sa FTMO, at ginawa with discipline, persistence, at faith.</p>", unsafe_allow_html=True)

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
# IN-DEPTH FAQs (complete list)
# ────────────────────────────────────────────────
st.markdown("<div class='glass-card' style='padding:2rem 2.4rem; margin:2.5rem auto;'>", unsafe_allow_html=True)
st.markdown("<h2 class='gold-text' style='text-align:center; margin-bottom:1.5rem;'>In-Depth Questions About KMFX EA</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; opacity:0.9; margin-bottom:1.8rem;'>"
            "Diretsong sagot sa mga tanong ng seryosong traders — walang paligoy-ligoy, puro facts.", unsafe_allow_html=True)

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
        st.markdown(a.strip())

st.markdown("</div>", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# MEMBER LOGIN SECTION (full 3 tabs)
# ────────────────────────────────────────────────
st.markdown("<div class='glass-card' style='text-align:center; padding:2.8rem 3rem; max-width:820px; margin:3rem auto;'>", unsafe_allow_html=True)
st.markdown("<h2 class='gold-text' style='margin-bottom:1.2rem;'>Already a Pioneer or Member?</h2>", unsafe_allow_html=True)
st.markdown("<p style='font-size:1.25rem; opacity:0.9; margin-bottom:2rem;'>"
            "Access your elite dashboard, realtime balance, profit shares, EA versions, and empire tools</p>", unsafe_allow_html=True)

tab_owner, tab_admin, tab_client = st.tabs(["👑 Owner Login", "🛠️ Admin Login", "👥 Client Login"])

with tab_owner:
    with st.form("owner_login_form", clear_on_submit=True):
        st.markdown("<p style='opacity:0.8; margin-bottom:1rem;'>Owner-only access</p>", unsafe_allow_html=True)
        owner_username = st.text_input("Username", placeholder="e.g. kingminted", key="owner_user")
        owner_password = st.text_input("Password", type="password", key="owner_pass")
        if st.form_submit_button("Login as Owner →", type="primary", use_container_width=True):
            success = login_user(owner_username.strip().lower(), owner_password, expected_role="owner")
            if success:
                st.success("Owner login successful! Redirecting...")
                st.session_state.role = "owner"
                st.switch_page("pages/👤_Admin_Management.py")
            else:
                st.error("Login failed – check credentials or role")

with tab_admin:
    with st.form("admin_login_form", clear_on_submit=True):
        st.markdown("<p style='opacity:0.8; margin-bottom:1rem;'>Admin access</p>", unsafe_allow_html=True)
        admin_username = st.text_input("Username", placeholder="Your admin username", key="admin_user")
        admin_password = st.text_input("Password", type="password", key="admin_pass")
        if st.form_submit_button("Login as Admin →", type="primary", use_container_width=True):
            success = login_user(admin_username.strip().lower(), admin_password, expected_role="admin")
            if success:
                st.success("Admin login successful! Redirecting...")
                st.session_state.role = "admin"
                st.switch_page("pages/👤_Admin_Management.py")
            else:
                st.error("Login failed – check credentials or role")

with tab_client:
    with st.form("client_login_form", clear_on_submit=True):
        st.markdown("<p style='opacity:0.8; margin-bottom:1rem;'>Client / Pioneer access</p>", unsafe_allow_html=True)
        client_username = st.text_input("Username", placeholder="Your username", key="client_user")
        client_password = st.text_input("Password", type="password", key="client_pass")
        if st.form_submit_button("Login as Client →", type="primary", use_container_width=True):
            success = login_user(client_username.strip().lower(), client_password, expected_role="client")
            if success:
                st.success("Welcome back! Redirecting to dashboard...")
                st.session_state.role = "client"
                st.switch_page("pages/🏠_Dashboard.py")
            else:
                st.error("Login failed – check credentials or role")

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