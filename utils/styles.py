# utils/styles.py
# =====================================================================
# KMFX EA - FULL CONSOLIDATED STYLES (v3.16 – Refined Feb 28, 2026)
# - Hero title & subtitle: pure BLACK
# - Metric labels: WHITE
# - Metric values & main titles: golden gradient (like $5,247.9)
# - Login cards / sections: full-width friendly
# - Professional dark theme + responsive
# =====================================================================
import streamlit as st

def apply_global_styles(public: bool = True):
    """
    Apply global styles across the app.
    - public=True  → dark theme (landing/login pages)
    - public=False → respect session_state['theme'] (dashboard)
    """
    theme = "dark" if public else st.session_state.get("theme", "dark")

    # ────────────────────────────────────────────────
    # Color & Gradient Definitions
    # ────────────────────────────────────────────────
    accent_gold_start   = "#FFD700"
    accent_gold_mid     = "#FFEA00"
    accent_gold_end     = "#FFCC00"
    gold_gradient       = f"linear-gradient(135deg, {accent_gold_start} 0%, {accent_gold_mid} 50%, {accent_gold_end} 100%)"

    bg_color            = "#0a0d14" if theme == "dark" else "#f8fbff"
    card_bg             = "rgba(18, 23, 35, 0.82)" if theme == "dark" else "rgba(255,255,255,0.88)"
    border_color        = "rgba(120,120,140,0.22)" if theme == "dark" else "rgba(0,0,0,0.11)"
    text_primary        = "#ffffff" if theme == "dark" else "#0f172a"
    text_muted          = "#c0c8d4" if theme == "dark" else "#64748b"

    card_shadow         = "0 12px 38px rgba(0,0,0,0.62)" if theme == "dark" else "0 10px 30px rgba(0,0,0,0.16)"
    glow_shadow         = "0 0 28px rgba(255,215,0,0.28)"

    st.markdown(f"""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">

    <style>
        :root {{
            --gold-gradient: {gold_gradient};
            --text-gold: #FFD700;
            --text-white: #ffffff;
            --bg-dark: {bg_color};
            --card-bg: {card_bg};
            --border: {border_color};
            --shadow-card: {card_shadow};
            --glow-gold: {glow_shadow};
            --max-width: 1380px;
        }}

        html, body, .stApp {{
            font-family: 'Inter', 'Poppins', system-ui, sans-serif !important;
            background: var(--bg-dark) !important;
            color: {text_primary} !important;
            font-size: 16px;
            line-height: 1.6;
        }}

        .main .block-container {{
            max-width: var(--max-width) !important;
            margin: 0 auto !important;
            padding: clamp(1rem, 3.5vw, 2rem) 1.4rem !important;
        }}

        /* ── ALL MAIN TITLES ── golden gradient (no box) ── */
        h1, h2, h3, h4, .gold-title, [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3 {{
            background: var(--gold-gradient) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            font-weight: 700 !important;
            letter-spacing: -0.2px;
            text-shadow: 0 1.5px 6px rgba(0,0,0,0.4);
        }}

        h1 {{ font-size: clamp(2.6rem, 7vw, 4.4rem) !important; margin: 0.4rem 0 0.8rem !important; }}
        h2 {{ font-size: clamp(2rem, 5.5vw, 3.2rem) !important; margin: 1.6rem 0 1rem !important; }}
        h3 {{ font-size: clamp(1.5rem, 4.2vw, 2.4rem) !important; margin: 1.8rem 0 1.1rem !important; }}

        /* ── HERO TITLE & SUBTITLE ── pure BLACK ── */
        .hero-title {{
            color: #000000 !important;
            font-weight: 900 !important;
            letter-spacing: 1.8px;
            text-shadow: 0 3px 12px rgba(0,0,0,0.75);
            font-size: clamp(2.8rem, 8vw, 4.8rem) !important;
            line-height: 1.05;
            margin: 0.6rem auto !important;
        }}

        .hero-subtitle {{
            color: #000000 !important;
            font-weight: 700 !important;
            letter-spacing: 2px;
            font-size: clamp(1.15rem, 3.8vw, 1.55rem) !important;
            margin-top: 0.4rem;
            opacity: 0.95;
        }}

        /* ── METRICS / STATS ── white labels + gold values ── */
        .metrics-container {{
            background: rgba(255,255,255,0.06) !important;
            backdrop-filter: blur(16px) !important;
            border: 1px solid rgba(255,255,255,0.16) !important;
            border-radius: 20px !important;
            padding: clamp(1.8rem, 4vw, 2.8rem) 1.6rem !important;
            margin: 2rem auto !important;
            max-width: 1140px !important;
            box-shadow: 0 10px 40px rgba(0,0,0,0.55) !important;
        }}

        .metrics-container [data-testid="stMetricLabel"] {{
            color: var(--text-white) !important;
            font-size: clamp(1.05rem, 2.4vw, 1.25rem) !important;
            font-weight: 600 !important;
            margin-bottom: 0.7rem !important;
            letter-spacing: 0.4px;
        }}

        .metrics-container [data-testid="stMetricValue"] {{
            background: var(--gold-gradient) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            font-size: clamp(2.4rem, 6vw, 3.4rem) !important;
            font-weight: 900 !important;
            line-height: 1.05 !important;
            text-shadow: 0 2px 8px rgba(255,215,0,0.35) !important;
        }}

        /* Make columns in metrics stretch nicely */
        .metrics-container .stColumn {{
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
        }}

        /* ── FULL-WIDTH LOGIN CARDS (Owner/Admin/Client) ── */
        .login-card {{
            background: var(--card-bg) !important;
            backdrop-filter: blur(22px) !important;
            border: 1px solid var(--border) !important;
            border-radius: 20px !important;
            padding: 2.2rem 2rem !important;
            margin: 1.4rem 0 !important;
            box-shadow: var(--shadow-card) !important;
            width: 100% !important;
            transition: all 0.35s ease;
        }}

        .login-card:hover {{
            transform: translateY(-8px);
            box-shadow: var(--glow-gold) !important;
        }}

        /* Buttons, inputs, etc. */
        button[kind="primary"], .stFormSubmitButton > button {{
            background: var(--gold-gradient) !important;
            color: #000000 !important;
            font-weight: 700 !important;
            border: none !important;
            border-radius: 14px !important;
            box-shadow: 0 5px 15px rgba(255,215,0,0.45) !important;
            transition: all 0.3s ease;
            min-height: 52px !important;
        }}

        button[kind="primary"]:hover {{
            transform: translateY(-3px);
            box-shadow: 0 12px 30px rgba(255,215,0,0.65) !important;
        }}

        .stTextInput label, .stTextArea label {{
            color: #FFD700 !important;
            font-weight: 600 !important;
        }}

        /* Scrollbar polish */
        ::-webkit-scrollbar {{ width: 9px; }}
        ::-webkit-scrollbar-track {{ background: var(--bg-dark); }}
        ::-webkit-scrollbar-thumb {{ background: rgba(120,120,140,0.5); border-radius: 10px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: #FFD700; }}

        /* Mobile adjustments */
        @media (max-width: 768px) {{
            .main .block-container {{ padding: 1rem 1.1rem !important; }}
            h1 {{ font-size: clamp(2.2rem, 9vw, 3.6rem) !important; }}
            .hero-title {{ font-size: clamp(2.4rem, 10vw, 4rem) !important; }}
            .metrics-container {{ padding: 1.6rem 1.2rem !important; margin: 1.6rem 0.6rem !important; }}
            .login-card {{ padding: 1.8rem 1.4rem !important; }}
        }}
    </style>
    """, unsafe_allow_html=True)