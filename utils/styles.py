# utils/styles.py
# =====================================================================
# KMFX EA - FULL CONSOLIDATED STYLES (v3.2 – Feb 2026)
# Centralized, theme-aware CSS – call once per page
# Merged from original main.py + fixes for consistency
# =====================================================================
import streamlit as st

def apply_global_styles(public: bool = True):
    """
    Apply global app styles.
    - public=True  → forced dark theme + public/landing look
    - public=False → respect st.session_state.theme (dashboard/admin)
    """
    # Theme logic
    theme = "dark" if public else st.session_state.get("theme", "dark")

    # Color palette
    accent_primary = "#00ffaa"
    accent_gold   = "#ffd700"
    accent_glow   = "#00ffaa40"
    accent_hover  = "#00ffcc"
    gold_soft     = "#f0d060"           # softer gold for backgrounds / placeholders
    gold_border   = "#e8c547"

    bg_color      = "#0a0d14" if theme == "dark" else "#f8fbff"
    card_bg       = "rgba(15,20,30,0.78)" if theme == "dark" else "rgba(255,255,255,0.82)"
    border_color  = "rgba(100,100,100,0.18)" if theme == "dark" else "rgba(0,0,0,0.09)"
    text_primary  = "#ffffff" if theme == "dark" else "#0f172a"
    text_muted    = "#bbbbbb" if theme == "dark" else "#64748b"
    card_shadow   = "0 10px 35px rgba(0,0,0,0.58)" if theme == "dark" else "0 8px 25px rgba(0,0,0,0.13)"
    sidebar_bg    = "rgba(10,13,20,0.97)" if theme == "dark" else "rgba(248,251,255,0.97)"

    # ── Inject fonts + main CSS ────────────────────────────────────────
    st.markdown(f"""
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --accent-primary: {accent_primary};
            --accent-gold:    {accent_gold};
            --accent-glow:    {accent_glow};
            --gold-gradient:  linear-gradient(135deg, #FFD700 0%, #B8860B 100%);
            --gold-soft:      {gold_soft};
            --gold-border:    {gold_border};
            --metric-white:   #FFFFFF;
            --max-app-width:  1320px;
        }}

        /* ── GLOBAL BASE ── */
        html, body, .stApp {{
            font-family: 'Poppins', sans-serif !important;
            background: {bg_color} !important;
            color: {text_primary} !important;
            scroll-behavior: smooth;
        }}

        .main .block-container {{
            max-width: var(--max-app-width) !important;
            margin: 0 auto !important;
            padding: 2rem 1.5rem !important;
        }}

        /* ── METRIC CARDS ── */
        [data-testid="stMetricLabel"] {{
            color: var(--metric-white) !important;
            font-size: clamp(0.9rem, 2vw, 1.1rem) !important;
            font-weight: 500 !important;
            letter-spacing: 0.5px;
            opacity: 0.9;
        }}
        [data-testid="stMetricValue"] {{
            color: var(--metric-white) !important;
            font-size: clamp(1.8rem, 4vw, 2.6rem) !important;
            font-weight: 700 !important;
            text-shadow: 0 0 15px rgba(255,255,255,0.25);
        }}
        [data-testid="stMetric"] {{
            background: rgba(255,255,255,0.05) !important;
            border-radius: 20px !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
            padding: 1.5rem !important;
            transition: all 0.3s ease;
        }}
        [data-testid="stMetric"]:hover {{
            transform: translateY(-6px);
            border-color: var(--accent-gold) !important;
            background: rgba(255,255,255,0.08) !important;
        }}

        /* ── GLASS CARDS ── */
        .glass-card {{
            background: {card_bg} !important;
            backdrop-filter: blur(24px);
            -webkit-backdrop-filter: blur(24px);
            border: 1px solid {border_color} !important;
            border-radius: 22px !important;
            padding: clamp(1.6rem, 5vw, 2.6rem) !important;
            box-shadow: {card_shadow} !important;
            transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
            margin: 1.8rem auto;
        }}
        .glass-card:hover {{
            transform: translateY(-8px);
            box-shadow: 0 22px 55px var(--accent-glow) !important;
            border-color: var(--accent-primary)90 !important;
        }}

        /* ── GOLD TEXT ── */
        .gold-text {{
            background: var(--gold-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 700;
            letter-spacing: 0.6px;
            filter: drop-shadow(0 1px 3px rgba(0,0,0,0.4));
        }}

        /* ── PRIMARY BUTTONS ── */
        button[kind="primary"] {{
            background: var(--accent-primary) !important;
            color: #000000 !important;
            border: none !important;
            border-radius: 14px !important;
            padding: 0.85rem 2.4rem !important;
            font-weight: 700 !important;
            text-transform: uppercase;
            letter-spacing: 1px;
            box-shadow: 0 5px 16px var(--accent-glow) !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }}
        button[kind="primary"]:hover {{
            transform: translateY(-2px) scale(1.02);
            box-shadow: 0 10px 25px {accent_glow}cc !important;
        }}

        /* Form submit & lang toggle */
        button[key="lang_toggle_public"],
        div[data-testid="stFormSubmitButton"] button {{
            background: #00ffa2 !important;
            color: #000000 !important;
        }}

        /* ── FORM INPUTS (normal) ── */
        .stTextInput input,
        .stTextArea textarea {{
            background: rgba(255,255,255,0.14) !important;
            color: white !important;
            border: 1px solid rgba(255,215,0,0.22) !important;
            border-radius: 12px !important;
            padding: 12px 16px !important;
        }}

        /* ── GOLDEN USERNAME + PASSWORD FIELDS ── */
        input[type="text"][aria-label*="username" i],
        input[type="text"][aria-label*="Username" i],
        input[type="text"][placeholder*="username" i],
        input[type="text"][placeholder*="Username" i],
        input[type="password"],
        input[type="password"][aria-label*="password" i],
        input[type="password"][aria-label*="Password" i] {{
            background: rgba(255, 215, 0, 0.08) !important;           /* subtle gold tint */
            border: 1px solid var(--gold-border) !important;
            color: var(--gold-soft) !important;
        }}

        input[type="text"][aria-label*="username" i]:focus,
        input[type="text"][aria-label*="Username" i]:focus,
        input[type="password"]:focus {{
            background: rgba(255, 215, 0, 0.22) !important;
            border-color: var(--accent-gold) !important;
            box-shadow: 0 0 16px rgba(255,215,0,0.45) !important;
            color: white !important;
        }}

        input[type="text"][aria-label*="username" i]::placeholder,
        input[type="text"][aria-label*="Username" i]::placeholder,
        input[type="password"]::placeholder {{
            color: rgba(255,215,0,0.55) !important;     /* golden placeholder */
            opacity: 0.9 !important;
        }}

        /* ── SUCCESS BOX ── */
        .success-box {{
            background: linear-gradient(135deg, rgba(0,255,162,0.16) 0%, rgba(0,255,162,0.09) 100%) !important;
            border: 1px solid #00ffa2 !important;
            padding: 22px !important;
            border-radius: 16px !important;
            text-align: center;
            color: white !important;
        }}

        /* ── LOGIN CARD & TABS ── */
        .login-box {{
            background: rgba(20,20,35,0.68) !important;
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255,215,0,0.22) !important;
            border-radius: 20px !important;
            padding: 40px !important;
            box-shadow: 0 25px 55px rgba(0,0,0,0.55) !important;
            max-width: 540px !important;
            margin: 2rem auto;
        }}

        [data-baseweb="tab-list"] {{
            background: rgba(0,0,0,0.35) !important;
            border-radius: 14px !important;
            padding: 6px !important;
            gap: 8px !important;
            display: flex !important;
            justify-content: stretch !important;
        }}

        [data-baseweb="tab"] {{
            flex: 1 !important;
            color: #FFD700 !important;
            font-weight: 700 !important;
            border-radius: 10px !important;
            transition: all 0.3s ease;
        }}

        [aria-selected="true"] {{
            background: var(--gold-gradient) !important;
            color: #000000 !important;
            box-shadow: 0 4px 16px rgba(255,215,0,0.4) !important;
        }}

        /* ── HEADER & SIDEBAR ── */
        header[data-testid="stHeader"] {{
            background-color: transparent !important;
            backdrop-filter: blur(12px) !important;
        }}
        section[data-testid="stSidebar"] {{
            background: {sidebar_bg} !important;
            border-right: 1px solid {border_color} !important;
        }}

        /* ── MOBILE OPTIMIZATIONS ── */
        @media (max-width: 768px) {{
            .main .block-container {{ max-width: 100% !important; padding: 1rem !important; }}
            .glass-card {{ padding: 1.3rem !important; border-radius: 18px !important; }}
            button[kind="primary"] {{ width: 100% !important; padding: 1.1rem !important; }}
        }}

        /* ── SCROLLBAR ── */
        ::-webkit-scrollbar {{ width: 8px; }}
        ::-webkit-scrollbar-track {{ background: {bg_color}; }}
        ::-webkit-scrollbar-thumb {{ background: {border_color}; border-radius: 10px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: var(--accent-gold); }}

        /* ── HR SEPARATOR ── */
        hr {{
            border: 0;
            height: 1px;
            background: rgba(255,255,255,0.06);
            border-bottom: 1px solid rgba(0,0,0,0.45);
            margin: 2.8rem 0 !important;
            box-shadow: 0 1px 3px rgba(255,215,0,0.08);
        }}
    </style>
    """, unsafe_allow_html=True)