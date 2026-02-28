# utils/styles.py
# =====================================================================
# KMFX EA - FULL CONSOLIDATED STYLES (v3.3 – Complete & Fixed Feb 2026)
# All original CSS from main.py merged, optimized, theme-aware
# Parameter: public: bool = True (for landing/public dark mode)
# =====================================================================
import streamlit as st

def apply_global_styles(public: bool = True):
    """
    Apply global styles across the app.
    - public=True  → forced dark theme (landing/login)
    - public=False → respect st.session_state.theme (dashboard/admin)
    """
    # Theme decision
    theme = "dark" if public else st.session_state.get("theme", "dark")

    # Color palette
    accent_primary = "#00ffaa"
    accent_gold    = "#ffd700"
    accent_glow    = "#00ffaa40"
    accent_hover   = "#00ffcc"

    bg_color       = "#0a0d14" if theme == "dark" else "#f8fbff"
    card_bg        = "rgba(15,20,30,0.78)" if theme == "dark" else "rgba(255,255,255,0.82)"
    border_color   = "rgba(100,100,100,0.18)" if theme == "dark" else "rgba(0,0,0,0.09)"
    text_primary   = "#ffffff" if theme == "dark" else "#0f172a"
    text_muted     = "#bbbbbb" if theme == "dark" else "#64748b"
    card_shadow    = "0 10px 35px rgba(0,0,0,0.58)" if theme == "dark" else "0 8px 25px rgba(0,0,0,0.13)"
    sidebar_bg     = "rgba(10,13,20,0.97)" if theme == "dark" else "rgba(248,251,255,0.97)"

    # ── Inject Google Fonts + Main CSS ─────────────────────────────────
    st.markdown(f"""
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">

    <style>
        :root {{
            --accent-glow: {accent_glow};
            --gold-gradient: linear-gradient(135deg, #FFD700 0%, #B8860B 100%);
            --metric-white: #FFFFFF;
            --max-app-width: 1320px;
        }}

        /* GLOBAL RESET & TYPOGRAPHY */
        html, body, [class*="css-"] {{
            font-family: 'Poppins', sans-serif !important;
            font-size: 16px;
            scroll-behavior: smooth;
        }}
        .stApp {{
            background: {bg_color} !important;
            color: {text_primary} !important;
        }}

        /* CENTERED CONTENT LAYOUT */
        .main .block-container {{
            max-width: var(--max-app-width) !important;
            margin: 0 auto !important;
            padding: 2rem 1.5rem !important;
        }}

        /* METRIC CARDS - WHITE TEXT ENHANCED */
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
            background: rgba(255,255,255,0.04) !important;
            padding: 1.5rem !important;
            border-radius: 20px !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            transition: all 0.3s ease;
        }}
        [data-testid="stMetric"]:hover {{
            transform: translateY(-5px);
            border-color: {accent_gold} !important;
            background: rgba(255,255,255,0.07) !important;
        }}

        /* RESPONSIVE HEADINGS */
        h1 {{ font-size: clamp(2rem, 5vw, 3.5rem) !important; font-weight: 700 !important; }}
        h2 {{ font-size: clamp(1.5rem, 4vw, 2.5rem) !important; font-weight: 600 !important; }}

        /* GLASSMORPHISM CARDS */
        .glass-card {{
            background: {card_bg} !important;
            backdrop-filter: blur(25px);
            -webkit-backdrop-filter: blur(25px);
            border-radius: 24px !important;
            border: 1px solid {border_color} !important;
            padding: clamp(1.5rem, 5vw, 2.5rem) !important;
            box-shadow: {card_shadow} !important;
            transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
            margin: 1.5rem auto;
            max-width: 100%;
        }}
        .glass-card:hover {{
            box-shadow: 0 20px 50px var(--accent-glow) !important;
            transform: translateY(-8px);
            border-color: {accent_primary}88 !important;
        }}

        /* GOLD TEXT EFFECT */
        .gold-text {{
            background: var(--gold-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 700;
            letter-spacing: 0.8px;
            filter: drop-shadow(0px 2px 4px rgba(0,0,0,0.3));
        }}

        /* PRIMARY BUTTONS - LUXURY STYLE */
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
        button[kind="primary"]:hover {{
            transform: translateY(-2px) scale(1.02);
            box-shadow: 0 8px 25px {accent_glow}cc !important;
        }}

        /* LANG TOGGLE & FORM SUBMIT BUTTONS */
        button[key="lang_toggle_public"],
        div[data-testid="stFormSubmitButton"] button {{
            background: #00ffa2 !important;
            color: #000000 !important;
        }}
        button[key="lang_toggle_public"] p {{
            color: #000000 !important;
        }}

        /* FORM INPUTS - DARK MODE FRIENDLY */
        .stTextInput input,
        .stTextArea textarea {{
            background: rgba(255,255,255,0.15) !important;
            color: white !important;
            border: 1px solid rgba(255,215,0,0.2) !important;
            border-radius: 12px !important;
            padding: 12px 15px !important;
        }}
        .stTextInput input:focus,
        .stTextArea textarea:focus {{
            border-color: #FFD700 !important;
            background: rgba(255,255,255,0.22) !important;
            box-shadow: 0 0 10px rgba(255,215,0,0.3) !important;
            color: #000000 !important;
        }}
        .stTextInput input::placeholder,
        .stTextArea textarea::placeholder {{
            color: rgba(255,255,255,0.5) !important;
        }}

        /* SUCCESS BOX */
        .success-box {{
            background: linear-gradient(135deg, rgba(0,255,162,0.15) 0%, rgba(0,255,162,0.08) 100%) !important;
            border: 1px solid #00ffa2 !important;
            padding: 20px !important;
            border-radius: 15px !important;
            text-align: center;
            color: white !important;
        }}

        /* LOGIN CARD & TABS - PREMIUM */
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
            text-align: center;
        }}
        [aria-selected="true"] {{
            background: var(--gold-gradient) !important;
            color: #000000 !important;
            box-shadow: 0 4px 16px rgba(255,215,0,0.4) !important;
        }}

        /* HEADER & SIDEBAR */
        header[data-testid="stHeader"] {{
            background-color: transparent !important;
            backdrop-filter: blur(15px) !important;
        }}
        section[data-testid="stSidebar"] {{
            background: {sidebar_bg} !important;
            border-right: 1px solid {border_color} !important;
        }}

        /* MOBILE OPTIMIZATION */
        @media (max-width: 768px) {{
            html, body {{ font-size: 14px; }}
            .glass-card {{ padding: 1.2rem !important; border-radius: 18px !important; }}
            [data-testid="stMetricValue"] {{ font-size: 1.8rem !important; }}
            button[kind="primary"] {{ width: 100% !important; padding: 1rem !important; }}
            .main .block-container {{ max-width: 100% !important; padding: 1rem !important; }}
        }}

        /* CUSTOM SCROLLBAR */
        ::-webkit-scrollbar {{ width: 8px; }}
        ::-webkit-scrollbar-track {{ background: {bg_color}; }}
        ::-webkit-scrollbar-thumb {{
            background: {border_color};
            border-radius: 10px;
        }}
        ::-webkit-scrollbar-thumb:hover {{ background: {accent_gold}; }}

        /* 3D ENGRAVED HR */
        hr {{
            border: 0;
            height: 1px;
            background: rgba(255,255,255,0.05);
            border-bottom: 1px solid rgba(0,0,0,0.5);
            margin: 2.5rem 0 !important;
            box-shadow: 0px 1px 2px rgba(255,215,0,0.05);
        }}
    </style>
    """, unsafe_allow_html=True)