# utils/styles.py
# =====================================================================
# KMFX EA - FULL CONSOLIDATED STYLES (v3.1)
# All CSS from main.py merged & optimized - One call only
# =====================================================================
import streamlit as st

def apply_global_styles(public: bool = True):
    # Theme handling
    theme = "dark" if public else st.session_state.get("theme", "light")
    
    accent_primary = "#00ffaa"
    accent_gold = "#ffd700"
    accent_glow = "#00ffaa40"
    accent_hover = "#00ffcc"
    bg_color = "#0a0d14" if theme == "dark" else "#f8fbff"
    card_bg = "rgba(15,20,30,0.75)" if theme == "dark" else "rgba(255,255,255,0.75)"
    border_color = "rgba(100,100,100,0.15)" if theme == "dark" else "rgba(0,0,0,0.08)"
    text_primary = "#ffffff" if theme == "dark" else "#0f172a"
    text_muted = "#aaaaaa" if theme == "dark" else "#64748b"
    card_shadow = "0 10px 30px rgba(0,0,0,0.5)" if theme == "dark" else "0 8px 25px rgba(0,0,0,0.12)"
    sidebar_bg = "rgba(10,13,20,0.95)" if theme == "dark" else "rgba(248,251,255,0.95)"

    st.markdown(f"""
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --accent-glow: {accent_glow};
            --gold-gradient: linear-gradient(135deg, #FFD700 0%, #B8860B 100%);
            --max-app-width: 1300px;
        }}
        
        /* GLOBAL */
        html, body, [class*="css-"] {{
            font-family: 'Poppins', sans-serif !important;
            font-size: 16px;
            scroll-behavior: smooth;
        }}
        .stApp {{
            background: {bg_color} !important;
            color: {text_primary} !important;
        }}
        .main .block-container {{
            max-width: var(--max-app-width) !important;
            margin: 0 auto !important;
            padding: 2rem 1.5rem !important;
        }}

        /* METRICS */
        [data-testid="stMetricLabel"] {{ color: #FFFFFF !important; font-size: clamp(0.9rem, 2vw, 1.1rem) !important; font-weight: 500 !important; }}
        [data-testid="stMetricValue"] {{ color: #FFFFFF !important; font-size: clamp(1.8rem, 4vw, 2.5rem) !important; font-weight: 700 !important; text-shadow: 0 0 15px rgba(255,255,255,0.2); }}
        [data-testid="stMetric"] {{
            background: rgba(255,255,255,0.04) !important;
            border-radius: 20px !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
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
            border-radius: 24px !important;
            border: 1px solid {border_color} !important;
            padding: clamp(1.5rem, 5vw, 2.5rem) !important;
            box-shadow: {card_shadow} !important;
            transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1) !important;
        }}
        .glass-card:hover {{
            transform: translateY(-8px);
            box-shadow: 0 20px 50px var(--accent-glow) !important;
            border-color: {accent_primary}88 !important;
        }}

        /* GOLD TEXT & BUTTONS */
        .gold-text {{
            background: var(--gold-gradient) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            font-weight: 700 !important;
        }}
        button[kind="primary"] {{
            background: {accent_primary} !important;
            color: #000000 !important;
            border-radius: 14px !important;
            font-weight: 700 !important;
            text-transform: uppercase;
            letter-spacing: 1px;
            box-shadow: 0 4px 15px {accent_glow} !important;
        }}
        button[key="lang_toggle_public"],
        div[data-testid="stFormSubmitButton"] button {{
            background: #00ffa2 !important;
            color: #000000 !important;
        }}

        /* FORM INPUTS - WHITE BACKGROUND ON FOCUS */
        .stTextInput input, .stTextArea textarea {{
            background: rgba(255,255,255,0.15) !important;
            color: white !important;
            border: 1px solid rgba(255,215,0,0.2) !important;
            border-radius: 12px !important;
        }}
        .stTextInput input:focus, .stTextArea textarea:focus {{
            background: #FFFFFF !important;
            color: #000000 !important;
            border-color: #FFD700 !important;
            box-shadow: 0 0 10px rgba(255,215,0,0.3) !important;
        }}
        .stTextInput input::placeholder, .stTextArea textarea::placeholder {{
            color: rgba(255,255,255,0.5) !important;
        }}

        /* SUCCESS BOX */
        .success-box {{
            background: linear-gradient(135deg, rgba(0,255,162,0.15) 0%, rgba(0,255,162,0.08) 100%) !important;
            border: 1px solid #00ffa2 !important;
            padding: 20px !important;
            border-radius: 15px !important;
            text-align: center;
            color: white;
        }}

        /* LOGIN SPECIFIC (ULTIMATE CONSOLIDATED) */
        .login-box {{
            background: rgba(20,20,35,0.6) !important;
            backdrop-filter: blur(15px) !important;
            border: 1px solid rgba(255,215,0,0.2) !important;
            padding: 40px !important;
            border-radius: 20px !important;
            box-shadow: 0 25px 50px rgba(0,0,0,0.5) !important;
        }}
        [data-baseweb="tab-list"] {{
            background: rgba(0,0,0,0.3) !important;
            border-radius: 15px !important;
        }}
        [data-baseweb="tab"] {{
            color: #FFD700 !important;
            font-weight: 700 !important;
        }}
        [aria-selected="true"] {{
            background: var(--gold-gradient) !important;
            color: black !important;
        }}

        /* HEADER & SIDEBAR */
        header[data-testid="stHeader"] {{ background-color: transparent !important; }}
        section[data-testid="stSidebar"] {{ background: {sidebar_bg} !important; }}

        /* MOBILE OPTIMIZATION */
        @media (max-width: 768px) {{
            .main .block-container {{ max-width: 100% !important; padding: 1rem !important; }}
            .glass-card {{ padding: 1.2rem !important; border-radius: 18px !important; }}
            button[kind="primary"] {{ width: 100% !important; padding: 1rem !important; }}
        }}

        /* SCROLLBAR */
        ::-webkit-scrollbar {{ width: 8px; }}
        ::-webkit-scrollbar-track {{ background: {bg_color}; }}
        ::-webkit-scrollbar-thumb {{ background: {border_color}; border-radius: 10px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: {accent_gold}; }}

        /* HR SEPARATOR */
        hr {{
            border: 0;
            height: 1px;
            background: rgba(255,255,255,0.05);
            border-bottom: 1px solid rgba(0,0,0,0.5);
            margin: 2.5rem 0 !important;
        }}
    </style>
    """, unsafe_allow_html=True)