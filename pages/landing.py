# pages/landing.py
# =====================================================================
# KMFX EA - FULL PUBLIC LANDING PAGE (COMPLETE v3.3 – fully synced Feb 2026)
# =====================================================================
import streamlit as st
import yfinance as yf
from utils.supabase_client import supabase
from utils.auth import login_user, is_authenticated
from utils.helpers import log_action
from utils.styles import apply_global_styles
from utils.qr_login import handle_qr_login
from collections import defaultdict

# ────────────────────────────────────────────────
# PAGE CONFIG & GLOBAL STYLES (must be first)
# ────────────────────────────────────────────────
st.set_page_config(
    page_title="KMFX EA - Elite Empire",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="collapsed"
)
apply_global_styles(public=True)

st.markdown("""
<style>
    section[data-testid="stSidebar"] { visibility: hidden !important; width: 0 !important; min-width: 0 !important; }
    .main .block-container { max-width: 1320px !important; margin: 0 auto !important; padding: 2rem 1.5rem !important; }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# QR LOGIN (early)
# ────────────────────────────────────────────────
handle_qr_login()

# ────────────────────────────────────────────────
# Redirect if already logged in
# ────────────────────────────────────────────────
if is_authenticated():
    role = st.session_state.get("role", "client").lower()
    if role in ["owner", "admin"]:
        st.switch_page("pages/👤_Admin_Management.py")
    else:
        st.switch_page("pages/🏠_Dashboard.py")
    st.stop()

# ────────────────────────────────────────────────
# CACHED DATA FUNCTIONS
# ────────────────────────────────────────────────
@st.cache_data(ttl=60)
def get_realtime_stats():
    try:
        accounts_count = supabase.table("ftmo_accounts").select("id", count="exact").execute().count or 0
        equity_data = supabase.table("ftmo_accounts").select("current_equity").execute().data or []
        total_equity = sum(acc.get("current_equity", 0) for acc in equity_data)
        gf_data = supabase.table("growth_fund_transactions").select("type", "amount").execute().data or []
        gf_balance = sum(t["amount"] if t["type"] == "In" else -t["amount"] for t in gf_data)
        members_count = supabase.table("users").select("id", count="exact").eq("role", "client").execute().count or 0
        return accounts_count, total_equity, gf_balance, members_count
    except Exception:
        return 0, 0, 0, 0

@st.cache_data(ttl=300)
def get_gold_price():
    try:
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
    except Exception:
        return None, 0.0

# ────────────────────────────────────────────────
# LANGUAGE SUPPORT
# ────────────────────────────────────────────────
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
    },
    "tl": {
        "join_waitlist": "Sumali sa Waitlist – Maagap na Access",
        "name": "Buong Pangalan",
        "email": "Email",
        "why_join": "Bakit gusto mong sumali sa KMFX? (opsyonal)",
        "submit": "Sumali sa Waitlist 👑",
        "success": "Tagumpay! Nasa listahan ka na. Check mo ang email mo soon 🚀",
    }
}

def txt(key):
    return texts.get(st.session_state.language, texts["en"]).get(key, key)

# ── Small Golden Sliding Toggle ──
st.markdown("""
    <style>
        .lang-toggle-wrapper {
            display: flex;
            justify-content: flex-end;
            align-items: center;
            margin: 1rem 0 1.5rem auto;
            font-family: 'Poppins', sans-serif;
        }
        .lang-toggle {
            position: relative;
            display: inline-block;
            width: 54px;
            height: 28px;
        }
        .lang-toggle input {
            opacity: 0;
            width: 0;
            height: 0;
        }
        .slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255,215,0,0.18);
            border: 1px solid #d4a01780;
            border-radius: 34px;
            transition: .4s;
        }
        .slider:before {
            position: absolute;
            content: "";
            height: 20px;
            width: 20px;
            left: 3px;
            bottom: 3px;
            background: #ffd700;
            border-radius: 50%;
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
            transition: .4s;
        }
        input:checked + .slider {
            background: linear-gradient(135deg, #ffd700 0%, #b8860b 100%);
            border-color: #ffd700;
        }
        input:checked + .slider:before {
            transform: translateX(26px);
            background: #000000;
        }
        .lang-indicator {
            font-size: 0.78rem;
            font-weight: 600;
            color: #ffd700;
            opacity: 0.6;
            margin: 0 6px;
            transition: opacity 0.3s;
        }
        input:checked ~ .lang-indicator-en { opacity: 0.6; }
        input:checked ~ .lang-indicator-tl { opacity: 1.0; font-weight: 700; }
        input:not(:checked) ~ .lang-indicator-en { opacity: 1.0; font-weight: 700; }
        input:not(:checked) ~ .lang-indicator-tl { opacity: 0.6; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="lang-toggle-wrapper">', unsafe_allow_html=True)
is_tl = st.session_state.language == "tl"
st.markdown(f"""
    <label class="lang-toggle">
        <input type="checkbox" {'checked' if is_tl else ''}
               onchange="parent.document.querySelector('form').submit();">
        <span class="slider"></span>
    </label>
    <span class="lang-indicator lang-indicator-en">EN</span>
    <span class="lang-indicator lang-indicator-tl">TL</span>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

if "lang_toggled" not in st.session_state:
    st.session_state.lang_toggled = False
if st.session_state.get("lang_toggled", False):
    st.session_state.language = "tl" if st.session_state.language == "en" else "en"
    st.session_state.lang_toggled = False
    st.rerun()

# ────────────────────────────────────────────────
# LOGO + HERO
# ────────────────────────────────────────────────
logo_col = st.columns([1, 4, 1])[1]
with logo_col:
    st.image("assets/logo.png", use_column_width=True)

st.markdown("<h1 class='gold-text' style='text-align:center; font-size: clamp(3rem,8vw,5.5rem); margin:1rem 0;'>KMFX EA</h1>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align:center; color:#ffffff;'>Automated Gold Trading for Financial Freedom</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; font-size:1.4rem; color:#aaaaaa;'>Passed FTMO Phase 1 • +3,071% 5-Year Backtest • Building Legacies of Generosity</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; font-size:1.2rem;'>Mark Jeff Blando – Founder & Developer • since 2014</p>", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# REALTIME STATS
# ────────────────────────────────────────────────
accounts_count, total_equity, gf_balance, members_count = get_realtime_stats()
stat_cols = st.columns(4)
with stat_cols[0]: st.metric("Active Accounts", accounts_count)
with stat_cols[1]: st.metric("Total Equity", f"${total_equity:,.0f}")
with stat_cols[2]: st.metric("Growth Fund", f"${gf_balance:,.0f}")
with stat_cols[3]: st.metric("Members", members_count)

# ────────────────────────────────────────────────
# LIVE GOLD PRICE
# ────────────────────────────────────────────────
price, change = get_gold_price()
if price:
    st.markdown(f"""
    <div style="text-align:center; font-size: clamp(3rem,9vw,4.5rem); font-weight:800; color:#ffd700; text-shadow:0 0 24px #00ffaa40; margin:2.2rem 0 0.8rem;">
        ${price:,.1f}
    </div>
    <p style="text-align:center; font-size:1.55rem; opacity:0.95;">
        <span style="color:{'#00ffaa' if change >=0 else '#ff5555'}; font-weight:700; font-size:1.65rem;">{change:+.2f}%</span>
         • Live Gold (XAU/USD) • GC=F Futures
    </p>
    """, unsafe_allow_html=True)
else:
    st.markdown("<p style='text-align:center; color:#aaaaaa; font-size:1.8rem;'>Gold Price (Loading or Market Closed...)</p>", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# TRADINGVIEW MINI CHART
# ────────────────────────────────────────────────
st.components.v1.html("""
<div class="tradingview-widget-container" style="width:100%; height:340px; min-height:220px; max-height:380px; margin:1.8rem auto 3rem; border-radius:14px; overflow:hidden; box-shadow:0 8px 28px rgba(0,0,0,0.5); background:rgba(13,17,23,0.6);">
  <div class="tradingview-widget-container__widget"></div>
  <script type="module" src="https://widgets.tradingview-widget.com/w/en/tv-mini-chart.js" async></script>
  <tv-mini-chart symbol="OANDA:XAUUSD" color-theme="dark" locale="en" height="100%" width="100%"></tv-mini-chart>
</div>
""", height=420)

# ────────────────────────────────────────────────
# BACKTEST VIDEO
# ────────────────────────────────────────────────
st.markdown("<h2 class='gold-text' style='text-align:center; margin:3rem 0 1.5rem;'>See the 2025 Backtest Results</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#cccccc; font-size:1.1rem; margin-bottom:1rem;'>1-Year Gold (XAUUSD) Performance: $500 → $3,906 (781% return)</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#aaaaaa; font-size:1rem; margin-bottom:2rem;'>Watch how KMFX EA performed in real historical test – win rate, drawdown, at full breakdown</p>", unsafe_allow_html=True)

st.markdown("""
<div class="video-container">
  <iframe
    src="https://www.youtube.com/embed/K7Ao_U0fuhk?rel=0&modestbranding=1&showinfo=0&controls=1"
    title="KMFX EA Backtest 2025 – Gold Strategy Test"
    frameborder="0"
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
    allowfullscreen
    loading="lazy">
  </iframe>
</div>
""", unsafe_allow_html=True)

st.markdown("<p style='text-align:center; color:#aaaaaa; font-size:0.95rem; margin-top:1rem;'>Backtest only – trading involves high risk. Past performance is not indicative of future results. Always do your own research.</p>", unsafe_allow_html=True)

st.markdown("<div style='height:3rem;'></div>", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# EMPIRE HEROES – PREMIUM LEADERBOARD STYLE (ULTRA COMPACT + REAL EARNINGS + EXACT JOINED DATE)
# ────────────────────────────────────────────────

st.markdown(
    "<h2 style='text-align:center; color:#ffd700; margin:2.5rem 0 1rem; font-weight:800; font-size:1.8rem;'>Empire Heroes Leaderboard</h2>",
    unsafe_allow_html=True
)
st.markdown(
    "<p style='text-align:center; color:#cccccc; font-size:0.95rem; margin-bottom:2rem; max-width:850px; margin-left:auto; margin-right:auto;'>"
    "Top legends rising fast. Earn badges, climb ranks, build your legacy. 👑</p>",
    unsafe_allow_html=True
)

@st.cache_data(ttl=120)
def get_featured_heroes(limit=10):
    try:
        response = supabase.table("client_badges") \
            .select("""
                user_id,
                badge_name,
                awarded_at,
                is_public,
                users!inner (
                    id, 
                    full_name, 
                    title, 
                    created_at,
                    total_profit          # Change to your actual earnings column if different
                )
            """) \
            .eq("is_public", True) \
            .eq("is_active", True) \
            .order("awarded_at", desc=True) \
            .execute()

        from collections import defaultdict
        user_badges = defaultdict(list)
        user_info = {}
        for row in response.data or []:
            user = row.get("users", {})
            uid = user.get("id")
            if uid:
                user_badges[uid].append(row["badge_name"])
                if uid not in user_info:
                    earnings_raw = user.get("total_profit", 0.0) or 0.0
                    joined_date = user.get("created_at", "")[:10]  # Exact YYYY-MM-DD from account creation
                    user_info[uid] = {
                        "full_name": user.get("full_name", "Unknown"),
                        "title": user.get("title", None),
                        "joined": joined_date,
                        "earnings_raw": earnings_raw,
                        "earnings_display": f"+${earnings_raw:,.2f}" if earnings_raw > 0 else f"-${abs(earnings_raw):,.2f}" if earnings_raw < 0 else "$0.00",
                    }

        heroes = []
        for uid, badges in user_badges.items():
            info = user_info.get(uid, {})
            first_name = info["full_name"].split()[0] if info["full_name"] != "Unknown" else "Hero"
            anon_id = f"#{abs(hash(str(uid))) % 10000 + 1:04d}"
            heroes.append({
                "first_name": first_name,
                "anon": anon_id,
                "badges": badges,
                "title": info["title"] or "Pioneer",
                "joined": info["joined"],
                "badge_count": len(badges),
                "earnings_raw": info["earnings_raw"],
                "earnings_display": info["earnings_display"],
            })

        # Sort: highest earnings → most badges → newest join (using exact joined date)
        heroes.sort(key=lambda x: (-x["earnings_raw"], -x["badge_count"], x["joined"]))
        return heroes[:limit]

    except Exception as e:
        st.warning(f"Hero fetch error: {str(e)}")
        return []

heroes = get_featured_heroes(limit=10)

if heroes:
    st.markdown("""
    <style>
        .empire-leaderboard {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            border-radius: 12px;
            padding: 0.9rem 0.6rem;
            box-shadow: 0 6px 20px rgba(0,0,0,0.55);
            border: 1px solid rgba(255,215,0,0.12);
            margin: 0 auto 2rem;
            max-width: 980px;
        }
        .rank-header {
            display: none;
        }
        .rank-row {
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 0.9rem 0.7rem;
            border-bottom: 1px solid rgba(255,215,0,0.06);
            transition: background 0.2s;
        }
        .rank-row:hover {
            background: rgba(255,215,0,0.03);
            border-radius: 8px;
        }
        .rank-position {
            font-size: 1.8rem;
            font-weight: 900;
            color: #e2e8f0;
            margin-bottom: 0.4rem;
            letter-spacing: -1px;
        }
        .rank-1 { color: #ffd700; text-shadow: 0 0 10px rgba(255,215,0,0.5); }
        .rank-2 { color: #e2e8f0; }
        .rank-3 { color: #fbbf24; }
        .rank-hero {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 0.4rem;
            margin-bottom: 0.6rem;
            width: 100%;
        }
        .rank-avatar {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: rgba(255,215,0,0.09);
            border: 2px solid rgba(255,215,0,0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.6rem;
        }
        .rank-name {
            font-size: 1.05rem;
            font-weight: 700;
            color: #f1f5f9;
            text-align: center;
        }
        .rank-name small {
            display: block;
            color: #94a3b8;
            font-size: 0.78rem;
            font-weight: 400;
        }
        .rank-earnings {
            font-size: 0.95rem;
            font-weight: 700;
            margin: 0.4rem 0;
        }
        .positive { color: #22c55e; }
        .negative { color: #ef4444; }
        .zero { color: #94a3b8; }
        .rank-badges-details {
            text-align: center;
            width: 100%;
        }
        .rank-badges {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 0.35rem 0.4rem;
            margin-bottom: 0.5rem;
        }
        .badge-tag {
            background: rgba(255,215,0,0.11);
            color: #ffea80;
            font-size: 0.75rem;
            padding: 0.25rem 0.6rem;
            border-radius: 999px;
            border: 1px solid rgba(255,215,0,0.22);
            white-space: nowrap;
        }
        .rank-details {
            color: #94a3b8;
            font-size: 0.8rem;
        }

        /* Tablet & Desktop – ultra compact grid */
        @media (min-width: 768px) {
            .rank-header {
                display: grid;
                grid-template-columns: 50px 200px 130px 1fr;
                background: rgba(255,215,0,0.04);
                padding: 0.7rem 0.9rem;
                border-radius: 9px;
                margin-bottom: 0.8rem;
                font-weight: 700;
                color: #ffea80;
                font-size: 0.82rem;
                text-align: left;
            }
            .rank-row {
                display: grid;
                grid-template-columns: 50px 200px 130px 1fr;
                align-items: center;
                padding: 0.8rem 0.9rem;
                border-bottom: 1px solid rgba(255,215,0,0.04);
            }
            .rank-position {
                font-size: 1.6rem;
                text-align: center;
                margin: 0;
            }
            .rank-hero {
                flex-direction: row;
                gap: 0.7rem;
                text-align: left;
            }
            .rank-avatar {
                width: 42px;
                height: 42px;
                font-size: 1.5rem;
            }
            .rank-name {
                font-size: 0.98rem;
            }
            .rank-name small {
                display: inline;
                font-size: 0.75rem;
            }
            .rank-earnings {
                text-align: center;
                font-size: 0.92rem;
            }
            .rank-badges-details {
                text-align: left;
            }
            .rank-badges {
                justify-content: flex-start;
                gap: 0.3rem;
            }
            .badge-tag {
                font-size: 0.72rem;
                padding: 0.22rem 0.55rem;
            }
            .rank-details {
                font-size: 0.78rem;
            }
        }
        @media (min-width: 1024px) {
            .empire-leaderboard { padding: 1rem 1rem; }
            .rank-row { padding: 0.85rem 1rem; }
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='empire-leaderboard'>", unsafe_allow_html=True)

    badge_emojis = {
        "Pioneer": "🛡️",
        "VIP Elite": "💎",
        "Consistency Star": "⭐",
    }

    for i, hero in enumerate(heroes, 1):
        rank_class = "rank-1" if i == 1 else "rank-2" if i == 2 else "rank-3" if i == 3 else ""
        avatar_emoji = badge_emojis.get(hero["badges"][0] if hero["badges"] else None, "🏆")
        
        badge_tags_html = "".join(
            f"<span class='badge-tag'>{badge_emojis.get(b, '🏆')} {b}</span>"
            for b in hero["badges"]
        )

        earnings_class = "positive" if hero["earnings_raw"] > 0 else "negative" if hero["earnings_raw"] < 0 else "zero"

        joined_text = f"Joined {hero['joined']}" if hero["joined"] else "Joined —"

        st.markdown(f"""
        <div class='rank-row'>
            <div class='rank-position {rank_class}'>{i}</div>
            <div class='rank-hero'>
                <div class='rank-avatar'>{avatar_emoji}</div>
                <div class='rank-name'>
                    {hero["first_name"]} <small>({hero["anon"]})</small>
                </div>
            </div>
            <div class='rank-earnings {earnings_class}'>{hero["earnings_display"]}</div>
            <div class='rank-badges-details'>
                <div class='rank-badges'>{badge_tags_html}</div>
                <div class='rank-details'>
                    {hero["title"]} • {joined_text}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div style='text-align:center; margin:2.5rem 0 4rem;'>
        <a href="#waitlist_form" style='display:inline-block; background:linear-gradient(90deg,#ffd700,#d4a017); color:#0f172a; font-weight:800; padding:0.7rem 2.2rem; border-radius:999px; text-decoration:none; box-shadow:0 6px 20px rgba(255,215,0,0.25); font-size:0.98rem;'>
            Join Waitlist – Start Your Rise Now 👑
        </a>
    </div>
    """, unsafe_allow_html=True)

else:
    st.info("No public heroes yet — be the first to earn a badge! 🚀")
# ────────────────────────────────────────────────
# WAITLIST FORM
# ────────────────────────────────────────────────
st.markdown("<div class='glass-card' style='padding: clamp(1.5rem, 5vw, 3rem); border: 1px solid rgba(255,215,0,0.3); position: relative; overflow: hidden;'>", unsafe_allow_html=True)
st.markdown("""
    <div style='position:absolute; top:-50px; right:-50px; width:150px; height:150px; background:rgba(255,215,0,0.1); filter:blur(50px); border-radius:50%; z-index:0;'></div>
""", unsafe_allow_html=True)
st.markdown(f"""
    <div style='text-align:center; position:relative; z-index:1;'>
        <h2 class='gold-text' style='margin-bottom:0.5rem;'>👑 {txt('join_waitlist')}</h2>
        <p style='color:rgba(255,255,255,0.7); font-size:1.1rem; margin-bottom:2rem; line-height:1.6; max-width:600px; margin-left:auto; margin-right:auto;'>
            Sumali sa waitlist para maunang makakuha ng access.
            <span style='color:#FFD700; font-weight:600;'>Limited slots</span> para sa mga pioneer — be part of the empire!
        </p>
    </div>
""", unsafe_allow_html=True)

with st.form("waitlist_form", clear_on_submit=True):
    col1, col2 = st.columns([1, 1])
    with col1:
        full_name = st.text_input(f"👤 {txt('name')}", placeholder="Juan Dela Cruz", key="waitlist_fullname")
    with col2:
        email_input = st.text_input(f"📧 {txt('email')}", placeholder="your@email.com", key="waitlist_email")
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
    submitted = st.form_submit_button(f"🚀 {txt('submit').upper()}", type="primary", use_container_width=True)

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
                    st.markdown(f"""
                        <div class='success-box'>
                            <h3 style='color:#00ffa2; margin-bottom:10px;'>MISSION SUCCESS! 👑</h3>
                            <p style='margin:0;'>Welcome to the pioneer circle, <b>{full_name_clean or 'Trader'}</b>.</p>
                            <p style='font-size:0.8rem; opacity:0.7;'>Check your inbox (and spam) for confirmation.</p>
                        </div>
                    """, unsafe_allow_html=True)
                    st.balloons()
                    try:
                        supabase.functions.invoke(
                            "send-waitlist-confirmation",
                            {"body": {"name": full_name_clean or "Anonymous", "email": email, "message": message_clean or "", "language": st.session_state.language}}
                        )
                    except:
                        pass
            except Exception as e:
                err_str = str(e).lower()
                if any(x in err_str for x in ["duplicate", "unique", "23505"]):
                    st.info("💡 " + ("You're already on the list! We'll reach out soon." if st.session_state.language == "en" else "Nasa waitlist ka na pala — salamat! Keep following lang."))
                else:
                    st.error(f"Error joining waitlist: {str(e)}")

st.markdown("</div>", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# PORTFOLIO STORY (FULL)
# ────────────────────────────────────────────────
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
        f"<div class='glass-card' style='padding:3rem; margin:3rem auto; max-width:1100px; border-left:6px solid #ffd700;'>",
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
        f"<h3 style='color:#ffd700; text-align:center; font-size:1.8rem; margin:2rem 0;'>"
        "🌍 2014: The Beginning in Saudi Arabia</h3>",
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        st.image("assets/saudi1.jpg", caption="Team Saudi Boys 🇸🇦", use_column_width=True)
    with col2:
        st.image("assets/saudi2.jpg", caption="Selfie with STC Cap", use_column_width=True)
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
        f"<h3 style='color:#ffd700; text-align:center; font-size:1.8rem; margin:2rem 0;'>"
        "🏠 2017: Umuwi sa Pinas at Crypto Era</h3>",
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        st.image("assets/family1.jpg", caption="Date with her ❤️", use_column_width=True)
    with col2:
        st.image("assets/family2.jpg", caption="Selfie My Family 👨‍👩‍👧", use_column_width=True)
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
        f"<h3 style='color:#ffd700; text-align:center; font-size:1.8rem; margin:2rem 0;'>"
        "🦠 2019–2021: Pandemic Days & Biggest Lesson</h3>",
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        st.image("assets/klever1.jpg", caption="Max gain almost $20k+ 🔥", use_column_width=True)
    with col2:
        st.image("assets/klever2.jpg", caption="Klever Exchange Setup", use_column_width=True)
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
        f"<h3 style='color:#ffd700; text-align:center; font-size:1.8rem; margin:2rem 0;'>"
        "🤖 2024–2025: The Professional Shift</h3>",
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        st.image("assets/ai1.jpg", caption="New Tech Found", use_column_width=True)
    with col2:
        st.image("assets/ai2.jpg", caption="Using Old Laptop to Build", use_column_width=True)
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
        f"<h3 style='color:#ffd700; text-align:center; font-size:1.8rem; margin:2rem 0;'>"
        "🏆 2025–2026: FTMO Challenges & Comeback</h3>",
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        st.image("assets/ftmo.jpeg", caption="Passed Phase 1 in 13 Days! 🎉", use_column_width=True)
    with col2:
        st.image("assets/ongoing.jpg", caption="Current challenge - full trust mode 🚀", use_column_width=True)
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

    # Realization & Future Vision
    st.markdown(
        f"<h3 style='color:#ffd700; text-align:center; font-size:1.8rem; margin:2rem 0;'>"
        "✨ Realization & Future Vision</h3>",
        unsafe_allow_html=True,
    )
    st.image("assets/journey_vision.jpg", use_column_width=True, caption="Built by Faith, Shared for Generations 👑")
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
# WHY CHOOSE KMFX EA?
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
            <h4 style='color:var(--accent-gold);'>{b['title']}</h4>
            <p style='font-size:0.9rem; opacity:0.8;'>{b['desc']}</p>
        </div>
        """, unsafe_allow_html=True)

# ────────────────────────────────────────────────
# IN-DEPTH FAQs
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

st.markdown("""
<style>
    .stExpander { background: rgba(255,255,255,0.02)!important; border:1px solid rgba(255,215,0,0.1)!important; border-radius:15px!important; margin-bottom:1rem!important; }
    .stExpander:hover { border-color: rgba(255,215,0,0.4)!important; background: rgba(255,255,255,0.05)!important; }
    .faq-ans { line-height:1.7; font-size:1rem; opacity:0.9; padding:1rem; }
    .faq-highlight { color:#FFD700; font-weight:600; }
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
# MEMBER LOGIN SECTION
# ────────────────────────────────────────────────
st.markdown("<div style='height: 4rem;'></div>", unsafe_allow_html=True)
st.markdown("""
    <div style='text-align:center;'>
        <h1 class='gold-text' style='margin-bottom:0;'>MEMBER ACCESS</h1>
        <p style='color:#FFD700; opacity:0.75; letter-spacing:3px; font-size:1.1rem; margin-top:5px;'>
            SECURE GATEWAY TO THE EMPIRE
        </p>
    </div>
""", unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

col_l, col_mid, col_r = st.columns([0.2, 1, 0.2])
with col_mid:
    st.markdown("<div class='login-box'>", unsafe_allow_html=True)
    tab_owner, tab_admin, tab_client = st.tabs(["👑 OWNER", "🛠️ ADMIN", "👥 CLIENT"])

    def render_secure_login(role_label: str, redirect_page: str):
        expected_role = role_label.lower()
        form_key = f"login_form_{expected_role}_v2026"
        user_key = f"username_{expected_role}_{form_key}"
        pwd_key = f"password_{expected_role}_{form_key}"
        submit_key = f"submit_{expected_role}_{form_key}"

        st.markdown(
            f"<p style='text-align:center; font-size:0.9rem; color:#FFD700; opacity:0.7; margin:0 0 1.2rem 0;'>"
            f"Authorized {role_label} Access Only</p>",
            unsafe_allow_html=True
        )

        with st.form(key=form_key, clear_on_submit=False):
            username = st.text_input("Username", placeholder="Enter your username", key=user_key, autocomplete="username")
            password = st.text_input("Password", type="password", placeholder="••••••••", key=pwd_key, autocomplete="current-password")
            st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
            submitted = st.form_submit_button(f"ENTER {role_label.upper()} DASHBOARD", use_container_width=True, key=submit_key)

            if submitted:
                if not username.strip() or not password:
                    st.error("Username and password are required")
                    return
                with st.spinner("Verifying access..."):
                    success, user_data = login_user(username.strip().lower(), password, expected_role=expected_role)
                    if success and user_data:
                        st.session_state.authenticated = True
                        st.session_state.username = user_data.get("username", username.lower())
                        st.session_state.full_name = user_data.get("full_name", username)
                        st.session_state.role = expected_role
                        st.session_state.just_logged_in = True
                        log_action("Login Success", f"{role_label} → {username}")
                        st.toast(f"Welcome back, {role_label}!", icon="👑")
                        st.success(f"Access granted → Redirecting...")
                        st.switch_page(redirect_page)
                    else:
                        st.error("Invalid credentials or role mismatch")

    with tab_owner:
        render_secure_login("Owner", "pages/👤_Admin_Management.py")
    with tab_admin:
        render_secure_login("Admin", "pages/👤_Admin_Management.py")
    with tab_client:
        render_secure_login("Client", "pages/🏠_Dashboard.py")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
        <p style='text-align:center; margin-top:2rem; font-size:0.85rem; color:#FFD700; opacity:0.6;'>
            Forgotten access? Contact KMFX Support.
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

if not st.session_state.get("authenticated", False):
    st.stop()