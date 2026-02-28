# utils/styles.py
# =====================================================================
# KMFX EA - FULL CONSOLIDATED STYLES (v3.9 – First Good Fix Feb 28, 2026)
# Golden titles, black top font + emoji, white metrics, golden buttons, responsive
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
            --gold-gradient:  linear-gradient(135deg, #FFD700 0%, #DAA520 50%, #B8860B 100%);
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
            padding: 0.8rem 1.5rem 2rem !important;
        }}

        /* GOLDEN TITLES - CLEAN & STRONG */
        h1, h2, h3, .gold-text {{
            background: var(--gold-gradient) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            font-weight: 800 !important;
            letter-spacing: 1px !important;
            text-shadow: 0 2px 6px rgba(0,0,0,0.5) !important;
            filter: drop-shadow(0 2px 5px rgba(255,215,0,0.4)) !important;
        }}

        h1 {{ font-size: clamp(3rem, 8vw, 5.5rem) !important; margin: 0.4rem 0 0.6rem !important; }}
        h2 {{ font-size: clamp(2rem, 5.5vw, 3.5rem) !important; margin: 1.5rem 0 0.8rem !important; }}
        h3 {{ font-size: clamp(1.6rem, 4.5vw, 2.4rem) !important; margin: 1.8rem 0 1rem !important; }}

        /* TOP HERO - BLACK FONT + IMPROVED EMOJI */
        .hero-title {{
            color: #000000 !important;
            background: rgba(0,0,0,0.75) !important;
            padding: 0.8rem 1.5rem !important;
            border-radius: 16px !important;
            font-weight: 900 !important;
            letter-spacing: 2px !important;
            text-shadow: 0 2px 8px rgba(0,0,0,0.8) !important;
            display: inline-block !important;
            margin: 0.5rem auto !important;
            font-size: clamp(2.8rem, 7vw, 4.5rem) !important;
        }}

        .hero-subtitle {{
            color: #000000 !important;
            background: rgba(0,0,0,0.65) !important;
            padding: 0.6rem 1.2rem !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
            letter-spacing: 3px !important;
            font-size: clamp(1.1rem, 4vw, 1.4rem) !important;
            margin-top: 0.6rem !important;
            display: inline-block !important;
        }}

        /* METRICS BOX - WHITE + CENTERED */
        .metrics-box {{
            background: rgba(255,255,255,0.05) !important;
            backdrop-filter: blur(14px) !important;
            border: 1px solid rgba(255,255,255,0.18) !important;
            border-radius: 20px !important;
            padding: 2.5rem 2rem !important;
            margin: 2.2rem auto !important;
            max-width: 1100px !important;
            box-shadow: 0 10px 30px rgba(0,0,0,0.45) !important;
            text-align: center !important;
        }}

        .metrics-box [data-testid="stMetricLabel"] {{
            color: #ffffff !important;
            font-size: 1.2rem !important;
            font-weight: 600 !important;
            margin-bottom: 0.9rem !important;
        }}

        .metrics-box [data-testid="stMetricValue"] {{
            color: #ffffff !important;
            font-size: 2.8rem !important;
            font-weight: 900 !important;
            line-height: 1.1 !important;
        }}

        .metrics-box .stColumn {{
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
        }}

        /* GOLDEN BUTTONS */
        button[kind="primary"],
        div.stFormSubmitButton > button {{
            background: var(--gold-gradient) !important;
            color: #000000 !important;
            border: none !important;
            border-radius: 14px !important;
            font-weight: 800 !important;
            box-shadow: 0 6px 18px rgba(255,215,0,0.5) !important;
        }}

        button[kind="primary"]:hover {{
            transform: translateY(-3px) !important;
            box-shadow: 0 12px 30px rgba(255,215,0,0.7) !important;
        }}

        /* EN/TL BUTTON - GOLDEN */
        button[key="lang_toggle_public"] {{
            background: var(--gold-gradient) !important;
            color: #000000 !important;
            border: none !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
        }}

        /* INPUT LABELS - GOLDEN */
        .stTextInput label,
        .stTextArea label {{
            color: #FFD700 !important;
            font-weight: 700 !important;
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
            button[kind="primary"] {{ width: 100% !important; padding: 1rem !important; }}
            h1 {{ font-size: clamp(2.2rem, 8vw, 3.8rem) !important; }}
            h2 {{ font-size: clamp(1.6rem, 6vw, 2.8rem) !important; }}
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