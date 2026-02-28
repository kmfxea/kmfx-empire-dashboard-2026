# utils/styles.py
# =====================================================================
# KMFX EA - FULL CONSOLIDATED STYLES (v3.13 – Final Solid Gold Enhancement)
# Enhanced Golden Gradient, Darker Background Contrast, Solid Glow
# =====================================================================
import streamlit as st

def apply_global_styles(public: bool = True):
    """
    Apply global styles across the app.
    - public=True → dark theme for landing/login
    - public=False → respect session theme for dashboard/admin
    """
    theme = "dark" if public else st.session_state.get("theme", "dark")

    # --- COLOR PALETTE DEFINITION ---
    # Enhanced for "Solid Gold" Landing Page
    accent_primary = "#FFD700"  # Core Gold
    accent_gold_dark = "#B8860B" # Deep Gold
    accent_gold_light = "#FFECB3" # Highlight Gold
    
    # Enhanced Gradient for Titles/Buttons
    solid_gold_gradient = f"linear-gradient(135deg, {accent_gold_light} 0%, {accent_primary} 40%, {accent_gold_dark} 100%)"
    
    accent_glow = "rgba(255, 215, 0, 0.2)" # Golden Glow
    accent_hover = "#FFECB3"

    bg_color = "#05070a" if theme == "dark" else "#f8fbff" # Darker background
    card_bg = "rgba(15,20,30,0.85)" if theme == "dark" else "rgba(255,255,255,0.82)"
    border_color = "rgba(255,215,0,0.15)" if theme == "dark" else "rgba(0,0,0,0.09)" # Gold border tint
    text_primary = "#ffffff" if theme == "dark" else "#0f172a"
    text_muted = "#d1d5db" if theme == "dark" else "#64748b"
    card_shadow = "0 10px 35px rgba(0,0,0,0.6)" if theme == "dark" else "0 8px 25px rgba(0,0,0,0.13)"
    sidebar_bg = "rgba(8,11,16,0.98)" if theme == "dark" else "rgba(248,251,255,0.97)"

    st.markdown(f"""
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">

    <style>
        :root {{
            --accent-primary: {accent_primary};
            --accent-gold: {accent_primary};
            --accent-glow: {accent_glow};
            --gold-gradient: {solid_gold_gradient};
            --metric-white: #FFFFFF;
            --max-app-width: 1320px;
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

        /* GOLDEN TITLES - STRONG & CLEAN */
        h1, h2, h3, .gold-text {{
            background: var(--gold-gradient) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            font-family: 'Playfair Display', serif !important;
            font-weight: 800 !important;
            letter-spacing: 0.5px !important;
            text-shadow: 0 4px 8px rgba(0,0,0,0.4) !important;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3)) !important;
        }}

        h1 {{ font-size: clamp(2.8rem, 7vw, 5rem) !important; margin: 0.4rem 0 0.6rem !important; }}
        h2 {{ font-size: clamp(1.8rem, 5vw, 3.2rem) !important; margin: 1.5rem 0 0.8rem !important; }}
        h3 {{ font-size: clamp(1.4rem, 4vw, 2.2rem) !important; margin: 1.8rem 0 1rem !important; }}

        /* METRICS BOX - FIXED */
        .metrics-box {{
            background: rgba(255,255,255,0.03) !important;
            backdrop-filter: blur(14px) !important;
            border: 1px solid {border_color} !important;
            border-radius: 20px !important;
            padding: 2.5rem 2rem !important;
            margin: 2.2rem auto !important;
            max-width: 1100px !important;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5) !important;
            text-align: center !important;
        }}

        .metrics-box [data-testid="stMetricLabel"] {{
            color: {text_muted} !important;
            font-size: 1rem !important;
            font-weight: 500 !important;
            margin-bottom: 0.5rem !important;
            letter-spacing: 1px;
            text-transform: uppercase;
        }}

        .metrics-box [data-testid="stMetricValue"] {{
            color: #ffffff !important;
            font-size: 3rem !important;
            font-weight: 800 !important;
            line-height: 1 !important;
            text-shadow: 0 0 15px rgba(255,215,0,0.3) !important;
        }}

        /* GLASS CARDS */
        .glass-card {{
            background: {card_bg} !important;
            backdrop-filter: blur(25px);
            border: 1px solid {border_color} !important;
            border-radius: 20px !important;
            padding: 2.2rem !important;
            box-shadow: {card_shadow} !important;
            transition: all 0.3s ease !important;
        }}
        .glass-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 35px var(--accent-glow) !important;
            border-color: rgba(255,215,0,0.4) !important;
        }}

        /* BUTTONS - SOLID GOLDEN GRADIENT */
        button[kind="primary"],
        div.stFormSubmitButton > button {{
            background: var(--gold-gradient) !important;
            color: #000000 !important;
            border: none !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
            text-transform: uppercase;
            letter-spacing: 1px;
            box-shadow: 0 4px 15px rgba(184,134,11,0.3) !important;
            transition: all 0.3s ease !important;
            padding: 0.75rem 1.5rem !important;
        }}

        button[kind="primary"]:hover,
        div.stFormSubmitButton > button:hover {{
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 25px rgba(184,134,11,0.5) !important;
            color: #000000 !important;
            filter: brightness(1.1);
        }}

        /* INPUT LABELS - GOLDEN */
        .stTextInput label,
        .stTextArea label,
        .stForm label {{
            color: {accent_primary} !important;
            font-weight: 600 !important;
            letter-spacing: 0.5px !important;
        }}

        /* LOGIN BOX */
        .login-box {{
            background: rgba(10,12,18,0.8) !important;
            backdrop-filter: blur(20px);
            border: 1px solid {border_color} !important;
            border-radius: 20px !important;
            padding: 40px !important;
            box-shadow: 0 20px 50px rgba(0,0,0,0.6) !important;
            max-width: 480px !important;
            margin: 2rem auto;
        }}

        [data-baseweb="tab-list"] {{
            background: rgba(255,255,255,0.05) !important;
            border-radius: 10px !important;
        }}
        [data-baseweb="tab"] {{
            color: {text_muted} !important;
            font-weight: 600 !important;
        }}
        [aria-selected="true"] {{
            color: {accent_primary} !important;
        }}

        /* SCROLLBAR */
        ::-webkit-scrollbar {{ width: 8px; }}
        ::-webkit-scrollbar-track {{ background: {bg_color}; }}
        ::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.1); border-radius: 10px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: {accent_primary}; }}
    </style>
    """, unsafe_allow_html=True)