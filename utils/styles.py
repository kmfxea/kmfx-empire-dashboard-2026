# utils/styles.py
# =====================================================================
# KMFX EA - OPTIMIZED RESPONSIVE STYLES (v3.11 – Mobile First)
# =====================================================================
import streamlit as st

def apply_global_styles(public: bool = True):
    """
    Apply global styles with heavy mobile-first optimization.
    """
    theme = "dark" if public else st.session_state.get("theme", "dark")

    # --- COLOR PALETTE ---
    accent_primary = "#00ffaa"
    accent_gold    = "#ffd700"
    gold_gradient  = "linear-gradient(135deg, #FFD700 0%, #B8860B 100%)"
    
    bg_color       = "#0a0d14" if theme == "dark" else "#f8fbff"
    text_primary   = "#ffffff" if theme == "dark" else "#0f172a"
    text_muted     = "#bbbbbb" if theme == "dark" else "#64748b"
    card_bg        = "rgba(20,25,35,0.78)" if theme == "dark" else "rgba(255,255,255,0.82)"
    border_color   = "rgba(255,255,255,0.08)" if theme == "dark" else "rgba(0,0,0,0.06)"
    
    st.markdown(f"""
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">

    <style>
        :root {{
            --accent-primary: {accent_primary};
            --accent-gold: {accent_gold};
            --gold-gradient: {gold_gradient};
            --max-app-width: 1320px;
        }}

        /* --- GLOBAL --- */
        html, body, .stApp {{
            font-family: 'Poppins', sans-serif !important;
            background-color: {bg_color} !important;
            color: {text_primary} !important;
        }}

        /* --- LAYOUT - Responsiveness Fix --- */
        .main .block-container {{
            max-width: var(--max-app-width) !important;
            padding-top: 1rem !important;
            padding-bottom: 2rem !important;
            /* Adaptive Padding */
            padding-left: clamp(1rem, 5vw, 3rem) !important;
            padding-right: clamp(1rem, 5vw, 3rem) !important;
        }}

        /* --- TYPOGRAPHY - Fluid Scaling --- */
        h1, h2, h3 {{
            background: var(--gold-gradient) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            font-weight: 800 !important;
            letter-spacing: -0.5px !important;
        }}

        h1 {{ font-size: clamp(2.2rem, 6vw, 4rem) !important; line-height: 1.1 !important; margin-bottom: 1rem !important; }}
        h2 {{ font-size: clamp(1.7rem, 4vw, 2.5rem) !important; margin-top: 1.5rem !important; }}
        h3 {{ font-size: clamp(1.3rem, 3vw, 1.8rem) !important; }}

        .gold-text {{
            background: var(--gold-gradient) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            font-weight: 700;
        }}

        /* --- METRICS BOX - Optimized for All Screens --- */
        .metrics-box {{
            background: rgba(255,255,255,0.03) !important;
            backdrop-filter: blur(10px) !important;
            border: 1px solid {border_color} !important;
            border-radius: 20px !important;
            padding: 1.5rem !important; /* Smaller padding for mobile */
            margin: 1.5rem auto !important;
            box-shadow: 0 8px 30px rgba(0,0,0,0.3) !important;
        }}

        @media (min-width: 768px) {{
            .metrics-box {{ padding: 2.5rem !important; }} /* Desktop padding */
        }}

        [data-testid="stMetricLabel"] {{
            font-size: 0.9rem !important;
            color: {text_muted} !important;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        [data-testid="stMetricValue"] {{
            font-size: clamp(1.8rem, 4vw, 2.8rem) !important;
            font-weight: 800 !important;
            color: {text_primary} !important;
        }}

        /* --- GLASS CARDS --- */
        .glass-card {{
            background: {card_bg} !important;
            backdrop-filter: blur(20px) !important;
            border: 1px solid {border_color} !important;
            border-radius: 20px !important;
            padding: clamp(1rem, 3vw, 2rem) !important;
            transition: transform 0.3s ease, box-shadow 0.3s ease !important;
        }}
        
        .glass-card:hover {{
            transform: translateY(-5px);
            border-color: rgba(0, 255, 170, 0.3) !important;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3) !important;
        }}

        /* --- BUTTONS - Touch Friendly --- */
        button[kind="primary"],
        div.stFormSubmitButton > button {{
            background: var(--gold-gradient) !important;
            color: #000000 !important;
            border: none !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 0.75rem 1.5rem !important;
            width: 100% !important; /* Full width on mobile by default */
            transition: all 0.2s ease !important;
        }}

        @media (min-width: 768px) {{
            button[kind="primary"],
            div.stFormSubmitButton > button {{
                width: auto !important; /* Auto width on desktop */
            }}
        }}

        button[kind="primary"]:hover {{
            filter: brightness(1.1);
            transform: translateY(-2px);
        }}

        /* --- INPUTS --- */
        .stTextInput label, .stTextArea label {{
            color: {accent_gold} !important;
            font-weight: 600 !important;
            margin-bottom: 0.2rem !important;
        }}
        
        /* Remove default streamlit border-radius for inputs */
        div[data-baseweb="input"] > div {{
            border-radius: 10px !important;
        }}

        /* --- LOGIN CARD --- */
        .login-box {{
            background: rgba(10,13,20,0.8) !important;
            backdrop-filter: blur(20px) !important;
            border: 1px solid rgba(255,215,0,0.15) !important;
            border-radius: 24px !important;
            padding: clamp(1.5rem, 5vw, 3rem) !important;
            box-shadow: 0 20px 50px rgba(0,0,0,0.5) !important;
            max-width: 500px !important;
            margin: 1rem auto;
        }}

        /* --- TABS --- */
        [data-baseweb="tab-list"] {{
            background-color: rgba(255,255,255,0.05) !important;
            border-radius: 12px !important;
            padding: 4px !important;
        }}

        [data-baseweb="tab"] {{
            border-radius: 10px !important;
            color: {text_muted} !important;
        }}
        
        [aria-selected="true"] {{
            background: rgba(255,255,255,0.1) !important;
            color: white !important;
        }}

        /* --- SCROLLBAR --- */
        ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
        ::-webkit-scrollbar-track {{ background: transparent; }}
        ::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.1); border-radius: 3px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: var(--accent-primary); }}

    </style>
    """, unsafe_allow_html=True)