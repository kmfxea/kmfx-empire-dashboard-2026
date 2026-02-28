# utils/styles.py
# =====================================================================
# KMFX EA - FULL CONSOLIDATED STYLES (v3.15 – Final Professional & Golden Feb 28, 2026)
# Titles: pure golden gradient text (like $5,247.9), no box • Top black font • White labels + golden values • Responsive
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
    accent_glow    = "#00ffaa30"
    accent_hover   = "#00ffcc"

    bg_color       = "#0a0d14" if theme == "dark" else "#f8fbff"
    card_bg        = "rgba(15,20,30,0.78)" if theme == "dark" else "rgba(255,255,255,0.82)"
    border_color   = "rgba(100,100,100,0.18)" if theme == "dark" else "rgba(0,0,0,0.09)"
    text_primary   = "#ffffff" if theme == "dark" else "#0f172a"
    text_muted     = "#bbbbbb" if theme == "dark" else "#64748b"
    card_shadow    = "0 10px 35px rgba(0,0,0,0.58)" if theme == "dark" else "0 8px 25px rgba(0,0,0,0.13)"
    sidebar_bg     = "rgba(10,13,20,0.97)" if theme == "dark" else "rgba(248,251,255,0.97)"

    st.markdown(f"""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">

    <style>
        :root {{
            --accent-primary: {accent_primary};
            --accent-gold:    {accent_gold};
            --accent-glow:    {accent_glow};
            --gold-gradient:  linear-gradient(135deg, #FFD700 0%, #FFEA00 50%, #FFCC00 100%);  /* Bright gold like $5,247.9 */
            --metric-white:   #FFFFFF;
            --max-app-width:  1320px;
            --base-font-size: 16px;
        }}

        html, body, .stApp {{
            font-family: 'Inter', 'Poppins', system-ui, -apple-system, sans-serif !important;
            font-size: var(--base-font-size) !important;
            background: {bg_color} !important;
            color: {text_primary} !important;
            scroll-behavior: smooth;
            line-height: 1.65 !important;
        }}

        .main .block-container {{
            max-width: var(--max-app-width) !important;
            margin: 0 auto !important;
            padding: clamp(0.8rem, 3vw, 1.6rem) 1.2rem !important;
        }}

        /* ALL TITLES - PURE GOLDEN GRADIENT TEXT (no box, like $5,247.9) */
        h1, h2, h3, h4, .gold-text, .title-gold {{
            background: var(--gold-gradient) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            font-weight: 700 !important;
            letter-spacing: 0.8px !important;
            text-shadow: 0 1px 4px rgba(0,0,0,0.35) !important;
            filter: drop-shadow(0 1px 3px rgba(255,215,0,0.25)) !important;
        }}

        h1 {{ font-size: clamp(2.4rem, 6.5vw, 4.2rem) !important; margin: 0.5rem 0 0.7rem !important; }}
        h2 {{ font-size: clamp(1.8rem, 5vw, 3rem) !important; margin: 1.4rem 0 0.8rem !important; }}
        h3 {{ font-size: clamp(1.4rem, 4vw, 2.2rem) !important; margin: 1.6rem 0 1rem !important; }}

        /* TOP HERO - BLACK FONT + IMPROVED EMOJI */
        .hero-title {{
            color: #000000 !important;
            font-weight: 900 !important;
            letter-spacing: 2px !important;
            text-shadow: 0 2px 8px rgba(0,0,0,0.7) !important;
            display: inline-block !important;
            margin: 0.5rem auto !important;
            font-size: clamp(2.6rem, 7vw, 4.2rem) !important;
        }}

        .hero-subtitle {{
            color: #000000 !important;
            font-weight: 700 !important;
            letter-spacing: 2.5px !important;
            font-size: clamp(1.1rem, 3.5vw, 1.4rem) !important;
            margin-top: 0.5rem !important;
            display: inline-block !important;
        }}

        /* METRICS BOX - WHITE LABELS + GOLD VALUES */
        .metrics-box {{
            background: rgba(255,255,255,0.05) !important;
            backdrop-filter: blur(14px) !important;
            border: 1px solid rgba(255,255,255,0.18) !important;
            border-radius: 18px !important;
            padding: clamp(1.5rem, 3vw, 2.5rem) 1.5rem !important;
            margin: 1.8rem auto !important;
            max-width: 1100px !important;
            box-shadow: 0 8px 25px rgba(0,0,0,0.4) !important;
            text-align: center !important;
        }}

        .metrics-box [data-testid="stMetricLabel"] {{
            color: #ffffff !important;
            font-size: clamp(1rem, 2.5vw, 1.15rem) !important;
            font-weight: 600 !important;
            margin-bottom: 0.8rem !important;
        }}

        .metrics-box [data-testid="stMetricValue"] {{
            color: #FFD700 !important;  /* Exact bright gold like $5,247.9 */
            font-size: clamp(2rem, 5vw, 2.8rem) !important;
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
            border-radius: 12px !important;
            font-weight: 700 !important;
            box-shadow: 0 4px 12px rgba(255,215,0,0.4) !important;
            transition: all 0.3s ease !important;
        }}

        button[kind="primary"]:hover {{
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 20px rgba(255,215,0,0.6) !important;
        }}

        /* INPUT LABELS - GOLDEN */
        .stTextInput label,
        .stTextArea label {{
            color: #FFD700 !important;
            font-weight: 600 !important;
        }}

        /* GLASS CARDS */
        .glass-card {{
            background: {card_bg} !important;
            backdrop-filter: blur(25px);
            border: 1px solid {border_color} !important;
            border-radius: 20px !important;
            padding: clamp(1.2rem, 4vw, 2.2rem) !important;
            box-shadow: {card_shadow} !important;
            transition: all 0.4s ease;
        }}

        .glass-card:hover {{
            transform: translateY(-6px);
            box-shadow: 0 15px 40px var(--accent-glow) !important;
        }}

        /* RESPONSIVE - Especially mobile */
        @media (max-width: 1024px) {{
            .main .block-container {{ padding: 1rem 1.2rem !important; }}
            h1 {{ font-size: clamp(2rem, 7vw, 3.5rem) !important; }}
            h2 {{ font-size: clamp(1.5rem, 5vw, 2.5rem) !important; }}
        }}

        @media (max-width: 768px) {{
            :root {{ --base-font-size: 15px; }}
            .main .block-container {{ padding: 0.8rem 1rem !important; }}
            h1 {{ font-size: clamp(1.8rem, 8vw, 3rem) !important; margin: 0.5rem 0 !important; }}
            h2 {{ font-size: clamp(1.4rem, 6vw, 2.2rem) !important; }}
            h3 {{ font-size: clamp(1.2rem, 5vw, 1.8rem) !important; }}
            .metrics-box {{ padding: 1.5rem 1rem !important; margin: 1.5rem 0.5rem !important; }}
            button[kind="primary"] {{ padding: 0.9rem !important; font-size: 1rem !important; min-height: 48px !important; }}
            .glass-card {{ padding: 1.2rem !important; border-radius: 16px !important; }}
        }}

        /* SCROLLBAR */
        ::-webkit-scrollbar {{ width: 8px; }}
        ::-webkit-scrollbar-track {{ background: {bg_color}; }}
        ::-webkit-scrollbar-thumb {{ background: {border_color}; border-radius: 10px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: {accent_gold}; }}
    </style>
    """, unsafe_allow_html=True)