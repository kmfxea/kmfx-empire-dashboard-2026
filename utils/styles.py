# utils/styles.py
# =====================================================================
# KMFX EA - FULL CONSOLIDATED STYLES (v3.4 – Fully Fixed Feb 2026)
# Adjusted spacing (logo + EN/TL), golden EN/TL button, golden labels
# =====================================================================
import streamlit as st

def apply_global_styles(public: bool = True):
    theme = "dark" if public else st.session_state.get("theme", "dark")

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

    st.markdown(f"""
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">

    <style>
        :root {{
            --accent-primary: {accent_primary};
            --accent-gold:    {accent_gold};
            --accent-glow:    {accent_glow};
            --gold-gradient:  linear-gradient(135deg, #FFD700 0%, #B8860B 100%);
            --metric-white:   #FFFFFF;
            --max-app-width:  1320px;
        }}

        html, body, .stApp {{
            font-family: 'Poppins', sans-serif !important;
            background: {bg_color} !important;
            color: {text_primary} !important;
            scroll-behavior: smooth;
        }}

        .main .block-container {{
            max-width: var(--max-app-width) !important;
            margin: 0 auto !important;
            padding: 1.2rem 1.5rem 2rem !important;  /* Reduced top padding for tighter hero fit */
        }}

        /* METRIC CARDS */
        [data-testid="stMetricLabel"] {{
            color: var(--metric-white) !important;
            font-size: clamp(0.9rem, 2vw, 1.1rem) !important;
            font-weight: 500 !important;
        }}
        [data-testid="stMetricValue"] {{
            color: var(--metric-white) !important;
            font-size: clamp(1.8rem, 4vw, 2.6rem) !important;
            font-weight: 700 !important;
        }}
        [data-testid="stMetric"] {{
            background: rgba(255,255,255,0.05) !important;
            border-radius: 20px !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
            transition: all 0.3s ease;
        }}
        [data-testid="stMetric"]:hover {{
            transform: translateY(-5px);
            border-color: {accent_gold} !important;
        }}

        /* GLASS CARDS */
        .glass-card {{
            background: {card_bg} !important;
            backdrop-filter: blur(25px);
            border: 1px solid {border_color} !important;
            border-radius: 24px !important;
            padding: 2.2rem !important;
            box-shadow: {card_shadow} !important;
            transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
        }}
        .glass-card:hover {{
            transform: translateY(-8px);
            box-shadow: 0 20px 50px var(--accent-glow) !important;
            border-color: {accent_primary}88 !important;
        }}

        /* GOLD TEXT */
        .gold-text {{
            background: var(--gold-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 700;
        }}

        /* PRIMARY BUTTONS */
        button[kind="primary"] {{
            background: {accent_primary} !important;
            color: #000000 !important;
            border-radius: 14px !important;
            font-weight: 700 !important;
            box-shadow: 0 4px 15px {accent_glow} !important;
            transition: all 0.3s !important;
        }}

        /* LANG TOGGLE - GOLDEN BACKGROUND ON LOAD */
        button[key="lang_toggle_public"] {{
            background: linear-gradient(135deg, #FFD700 0%, #B8860B 100%) !important;
            color: #000000 !important;
            border: none !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
            box-shadow: 0 4px 12px rgba(255,215,0,0.4) !important;
            transition: all 0.3s ease;
        }}
        button[key="lang_toggle_public"]:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(255,215,0,0.6) !important;
        }}

        /* FORM INPUT LABELS - FORCED GOLDEN */
        .stTextInput label,
        .stTextArea label,
        .stForm label {{
            color: #FFD700 !important;
            font-weight: 600 !important;
            letter-spacing: 0.5px;
            text-shadow: 0 0 6px rgba(255,215,0,0.3) !important;
        }}

        /* FORM INPUTS */
        .stTextInput input,
        .stTextArea textarea {{
            background: rgba(255,255,255,0.15) !important;
            color: white !important;
            border: 1px solid rgba(255,215,0,0.22) !important;
            border-radius: 12px !important;
        }}
        .stTextInput input:focus,
        .stTextArea textarea:focus {{
            border-color: #FFD700 !important;
            background: rgba(255,255,255,0.24) !important;
            box-shadow: 0 0 12px rgba(255,215,0,0.35) !important;
            color: #000000 !important;
        }}

        /* SUCCESS BOX */
        .success-box {{
            background: linear-gradient(135deg, rgba(0,255,162,0.16) 0%, rgba(0,255,162,0.09) 100%) !important;
            border: 1px solid #00ffa2 !important;
            padding: 22px !important;
            border-radius: 16px !important;
            text-align: center;
            color: white !important;
        }}

        /* LOGIN CARD & TABS */
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
            display: flex !important;
            justify-content: stretch !important;
        }}
        [data-baseweb="tab"] {{
            flex: 1 !important;
            color: #FFD700 !important;
            font-weight: 700 !important;
            border-radius: 10px !important;
        }}
        [aria-selected="true"] {{
            background: var(--gold-gradient) !important;
            color: #000000 !important;
        }}

        /* HEADER & SIDEBAR */
        header[data-testid="stHeader"] {{ background: transparent !important; }}
        section[data-testid="stSidebar"] {{ background: {sidebar_bg} !important; }}

        /* MOBILE */
        @media (max-width: 768px) {{
            .main .block-container {{ padding: 1rem !important; }}
            .glass-card {{ padding: 1.3rem !important; }}
            button[kind="primary"] {{ width: 100% !important; }}
        }}

        /* SCROLLBAR */
        ::-webkit-scrollbar {{ width: 8px; }}
        ::-webkit-scrollbar-track {{ background: {bg_color}; }}
        ::-webkit-scrollbar-thumb {{ background: {border_color}; border-radius: 10px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: {accent_gold}; }}

        /* HR */
        hr {{
            border: 0;
            height: 1px;
            background: rgba(255,255,255,0.06);
            border-bottom: 1px solid rgba(0,0,0,0.45);
            margin: 2.2rem 0 !important;
        }}

        /* EXTRA TIGHT HERO SPACING */
        .hero-section {{ margin-top: 0.5rem !important; padding-top: 0.5rem !important; }}
        .lang-toggle-container {{ margin-top: 0.8rem !important; margin-bottom: 1.2rem !important; }}
    </style>
    """, unsafe_allow_html=True)