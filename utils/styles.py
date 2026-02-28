# utils/styles.py
# =====================================================================
# KMFX EA - FULL CONSOLIDATED STYLES (v3.10 – Final Golden + Metrics Fix Feb 2026)
# Strong golden titles restored (like old version), fixed metrics box (white + centered), golden login buttons
# =====================================================================
import streamlit as st

def apply_global_styles(public: bool = True):
    """
    Apply global styles across the app.
    - public=True → dark theme for landing/login
    - public=False → respect session theme for dashboard/admin
    """
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
            padding: 0.5rem 1.5rem 2rem !important;  /* Very tight top for logo fit */
        }}

        /* STRONG GOLDEN TITLES - RESTORED EXACT LOOK FROM OLD MAIN.PY */
        h1, h2, h3, .gold-text {{
            background: var(--gold-gradient) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            font-weight: 800 !important;
            filter: drop-shadow(0 4px 10px rgba(0,0,0,0.7)) !important;
            letter-spacing: 1.2px !important;
            text-shadow: 0 0 15px rgba(255,215,0,0.6) !important;  /* Intense shine */
        }}

        h1 {{ font-size: clamp(3rem, 8vw, 6rem) !important; margin: 0.3rem 0 0.5rem !important; }}
        h2 {{ font-size: clamp(2rem, 5.5vw, 3.5rem) !important; margin: 1.4rem 0 0.7rem !important; }}
        h3 {{ font-size: clamp(1.6rem, 4.5vw, 2.4rem) !important; margin: 1.6rem 0 0.9rem !important; }}

        /* METRICS BOX - FIXED: centered, full white text/numbers, perfect spacing */
        .metrics-box {{
            background: rgba(255,255,255,0.05) !important;
            backdrop-filter: blur(14px) !important;
            border: 1px solid rgba(255,255,255,0.18) !important;
            border-radius: 20px !important;
            padding: 2.6rem 2.2rem !important;
            margin: 2.5rem auto !important;
            max-width: 1100px !important;
            box-shadow: 0 12px 35px rgba(0,0,0,0.45) !important;
            text-align: center !important;
        }}

        .metrics-box [data-testid="stMetricLabel"] {{
            color: #ffffff !important;
            font-size: 1.25rem !important;
            font-weight: 600 !important;
            margin-bottom: 1rem !important;
            letter-spacing: 0.6px;
        }}

        .metrics-box [data-testid="stMetricValue"] {{
            color: #ffffff !important;
            font-size: 2.9rem !important;
            font-weight: 900 !important;
            line-height: 1.1 !important;
            text-shadow: 0 0 16px rgba(255,255,255,0.35) !important;
        }}

        /* Center columns content */
        .metrics-box .stColumn {{
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
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

        /* PRIMARY BUTTONS + LOGIN SUBMIT BUTTONS - GOLDEN GRADIENT */
        button[kind="primary"],
        div.stFormSubmitButton > button {{
            background: var(--gold-gradient) !important;
            color: #000000 !important;
            border: none !important;
            border-radius: 14px !important;
            font-weight: 800 !important;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            box-shadow: 0 6px 18px rgba(255,215,0,0.5) !important;
            transition: all 0.3s ease !important;
            padding: 1rem 2rem !important;
        }}

        button[kind="primary"]:hover,
        div.stFormSubmitButton > button:hover {{
            transform: translateY(-3px) scale(1.03) !important;
            box-shadow: 0 12px 30px rgba(255,215,0,0.7) !important;
        }}

        /* EN/TL BUTTON - GOLDEN */
        button[key="lang_toggle_public"] {{
            background: var(--gold-gradient) !important;
            color: #000000 !important;
            border: none !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
            box-shadow: 0 4px 12px rgba(255,215,0,0.4) !important;
        }}

        /* INPUT LABELS - GOLDEN */
        .stTextInput label,
        .stTextArea label,
        .stForm label {{
            color: #FFD700 !important;
            font-weight: 700 !important;
            letter-spacing: 0.8px !important;
        }}

        /* JOURNEY IMAGES - UNIFORM SIZE (except vision) */
        .journey-image img {{
            max-height: 420px !important;
            object-fit: cover !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4) !important;
            width: 100% !important;
        }}
        .vision-image img {{
            max-height: none !important;
            object-fit: contain !important;
            width: 100% !important;
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

        header[data-testid="stHeader"] {{ background: transparent !important; }}
        section[data-testid="stSidebar"] {{ background: {sidebar_bg} !important; }}

        @media (max-width: 768px) {{
            .main .block-container {{ padding: 1rem !important; }}
            .glass-card {{ padding: 1.3rem !important; }}
            button[kind="primary"] {{ width: 100% !important; }}
        }}

        ::-webkit-scrollbar {{ width: 8px; }}
        ::-webkit-scrollbar-track {{ background: {bg_color}; }}
        ::-webkit-scrollbar-thumb {{ background: {border_color}; border-radius: 10px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: {accent_gold}; }}

        hr {{
            border: 0;
            height: 1px;
            background: rgba(255,255,255,0.06);
            border-bottom: 1px solid rgba(0,0,0,0.45);
            margin: 2.2rem 0 !important;
        }}
    </style>
    """, unsafe_allow_html=True)