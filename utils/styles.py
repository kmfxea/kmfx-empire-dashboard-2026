# utils/styles.py
# =====================================================================
# KMFX EA - OPTIMIZED RESPONSIVE STYLES (v3.12 – Laptop Wide + Dark Header)
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
    card_bg        = "rgba(15,20,30,0.85)" if theme == "dark" else "rgba(255,255,255,0.9)"
    border_color   = "rgba(255,255,255,0.08)" if theme == "dark" else "rgba(0,0,0,0.06)"
    
    st.markdown(f"""
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">

    <style>
        :root {{
            --accent-primary: {accent_primary};
            --accent-gold: {accent_gold};
            --gold-gradient: {gold_gradient};
            --max-app-width: 1600px; /* --- WIDER FOR LAPTOP --- */
        }}

        /* --- GLOBAL --- */
        html, body, .stApp {{
            font-family: 'Poppins', sans-serif !important;
            background-color: {bg_color} !important;
            color: {text_primary} !important;
        }}

        /* --- TOP HEADER (Streamlit Navbar) - BLACK --- */
        header[data-testid="stHeader"] {{
            background-color: #000000 !important;
            border-bottom: 1px solid {border_color};
        }}

        /* --- LAYOUT - Responsiveness Fix --- */
        .main .block-container {{
            max-width: var(--max-app-width) !important;
            padding-top: 1rem !important;
            padding-bottom: 2rem !important;
            /* Adaptive Padding */
            padding-left: clamp(1rem, 5vw, 4rem) !important;
            padding-right: clamp(1rem, 5vw, 4rem) !important;
        }}

        /* --- TYPOGRAPHY - Fluid Scaling --- */
        h1, h2, h3 {{
            background: var(--gold-gradient) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            font-weight: 800 !important;
            letter-spacing: -0.5px !important;
        }}

        h1 {{ font-size: clamp(2.5rem, 6vw, 4.5rem) !important; line-height: 1.1 !important; margin-bottom: 1rem !important; }}
        h2 {{ font-size: clamp(1.8rem, 4vw, 3rem) !important; margin-top: 1.5rem !important; }}
        h3 {{ font-size: clamp(1.4rem, 3vw, 2.2rem) !important; }}

        /* --- METRICS BOX - Binalik ang Box/Shadow --- */
        .metrics-box {{
            background: rgba(255,255,255,0.03) !important;
            backdrop-filter: blur(15px) !important;
            border: 1px solid {border_color} !important;
            border-radius: 20px !important;
            padding: 2rem !important;
            margin: 2rem auto !important;
            box-shadow: 0 15px 40px rgba(0,0,0,0.5) !important; /* --- BOX SHADOW BACK --- */
        }}

        [data-testid="stMetricLabel"] {{
            font-size: 1rem !important;
            color: {text_muted} !important;
            text-transform: uppercase;
            letter-spacing: 1.5px;
        }}

        [data-testid="stMetricValue"] {{
            font-size: clamp(2.2rem, 5vw, 3.5rem) !important;
            font-weight: 800 !important;
            color: {text_primary} !important;
            text-shadow: 0 0 15px rgba(255,215,0,0.3) !important;
        }}

        /* --- GLASS CARDS --- */
        .glass-card {{
            background: {card_bg} !important;
            backdrop-filter: blur(20px) !important;
            border: 1px solid {border_color} !important;
            border-radius: 20px !important;
            padding: clamp(1.5rem, 3vw, 2.5rem) !important;
            transition: transform 0.3s ease, box-shadow 0.3s ease !important;
        }}
        
        .glass-card:hover {{
            transform: translateY(-5px);
            border-color: rgba(0, 255, 170, 0.4) !important;
            box-shadow: 0 15px 40px rgba(0,0,0,0.4) !important;
        }}

        /* --- BUTTONS - Laptop Stretch --- */
        button[kind="primary"],
        div.stFormSubmitButton > button {{
            background: var(--gold-gradient) !important;
            color: #000000 !important;
            border: none !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 1rem 2rem !important;
            
            /* STRETCH ON LAPTOP */
            width: 100% !important; 
            transition: all 0.2s ease !important;
        }}

        @media (min-width: 1024px) {{
            button[kind="primary"],
            div.stFormSubmitButton > button {{
                width: auto !important; /* Auto width on desktop for balance */
                min-width: 200px !important; /* Optional: para hindi sobrang nipis */
            }}
        }}

        button[kind="primary"]:hover {{
            filter: brightness(1.1);
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(255,215,0,0.3) !important;
        }}

        /* --- LOGIN & OWNER ADMIN CLIENT (Tabs) --- */
        .login-box {{
            background: rgba(10,13,20,0.85) !important;
            backdrop-filter: blur(20px) !important;
            border: 1px solid rgba(255,215,0,0.15) !important;
            border-radius: 24px !important;
            padding: clamp(2rem, 5vw, 3rem) !important;
            box-shadow: 0 25px 60px rgba(0,0,0,0.6) !important;
            max-width: 600px !important;
            margin: 2rem auto;
        }}

        [data-baseweb="tab-list"] {{
            background-color: rgba(0,0,0,0.5) !important;
            border-radius: 12px !important;
            padding: 5px !important;
        }}

        [data-baseweb="tab"] {{
            border-radius: 10px !important;
            color: {text_muted} !important;
            font-weight: 600;
        }}
        
        [aria-selected="true"] {{
            background: var(--gold-gradient) !important;
            color: #000000 !important;
        }}
    </style>
    """, unsafe_allow_html=True)