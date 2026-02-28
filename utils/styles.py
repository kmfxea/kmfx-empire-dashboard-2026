# utils/styles.py
# =====================================================================
# KMFX EA - FULL CONSOLIDATED STYLES (v3.5 – Spacing + Golden Fixes Feb 2026)
# Adjusted: tighter hero/logo spacing, golden EN/TL, golden labels, image uniformity
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
            padding: 0.8rem 1.5rem 2rem !important;  /* Reduced top padding para mas mataas logo */
        }}

        /* TIGHTER HERO SPACING */
        .hero-container {{
            margin-top: 0.5rem !important;
            padding-top: 0.5rem !important;
            text-align: center;
        }}

        /* METRICS - Centered with breathing room */
        .metrics-box {{
            background: rgba(255,255,255,0.04) !important;
            border-radius: 20px !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
            padding: 2rem 1.5rem !important;
            margin: 1.5rem auto !important;
            max-width: 1100px !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important;
        }}
        .metrics-box [data-testid="stMetric"] {{
            background: transparent !important;
            border: none !important;
        }}
        .metrics-box h3 {{
            color: {accent_gold} !important;
            text-align: center;
            margin-bottom: 1.5rem !important;
        }}

        /* GOLDEN LABELS FOR INPUTS */
        .stTextInput label,
        .stTextArea label,
        .stForm label {{
            color: #FFD700 !important;
            font-weight: 700 !important;
            letter-spacing: 0.8px;
            text-shadow: 0 0 6px rgba(255,215,0,0.4) !important;
        }}

        /* EN/TL BUTTON - GOLDEN BACKGROUND */
        button[key="lang_toggle_public"] {{
            background: var(--gold-gradient) !important;
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

        /* JOURNEY IMAGES - UNIFORM SIZE (except vision) */
        .journey-image img {{
            max-height: 420px !important;
            object-fit: cover !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4) !important;
        }}
        .vision-image img {{
            max-height: none !important;  /* Full size for vision only */
            object-fit: contain !important;
        }}

        /* GLASS CARDS, BUTTONS, SCROLLBAR, etc. remain the same as before */
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

        button[kind="primary"] {{
            background: {accent_primary} !important;
            color: #000000 !important;
            border-radius: 14px !important;
            font-weight: 700 !important;
            box-shadow: 0 4px 15px {accent_glow} !important;
        }}

        /* ... (keep all other rules like metrics, tabs, scrollbar, HR, etc.) ... */
    </style>
    """, unsafe_allow_html=True)