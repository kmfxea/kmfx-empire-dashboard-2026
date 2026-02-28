# utils/styles.py
# =====================================================================
# KMFX EA - FULL CONSOLIDATED STYLES (v3.4 – Mobile Optimized – Feb 2026)
# Centralized, theme-aware CSS – golden login/registration fields
# Enhanced mobile friendliness: clamp() fonts, compact padding, cute scaling
# =====================================================================
import streamlit as st

def apply_global_styles(public: bool = True):
    """
    Apply global app styles.
    - public=True → forced dark theme + public/landing look
    - public=False → respect st.session_state.theme (dashboard/admin)
    """
    # Theme logic
    theme = "dark" if public else st.session_state.get("theme", "dark")

    # Color palette
    accent_primary = "#00ffaa"
    accent_gold   = "#ffd700"
    accent_glow   = "#00ffaa40"
    accent_hover  = "#00ffcc"
    gold_border   = "#d4a017"
    gold_focus    = "#ffd700"
    gold_bg_normal = "rgba(255, 215, 0, 0.10)"
    gold_bg_focus  = "rgba(255, 215, 0, 0.22)"
    bg_color    = "#0a0d14" if theme == "dark" else "#f8fbff"
    card_bg     = "rgba(15,20,30,0.78)" if theme == "dark" else "rgba(255,255,255,0.82)"
    border_color= "rgba(100,100,100,0.18)" if theme == "dark" else "rgba(0,0,0,0.09)"
    text_primary= "#ffffff" if theme == "dark" else "#0f172a"
    text_muted  = "#bbbbbb" if theme == "dark" else "#64748b"
    card_shadow = "0 10px 35px rgba(0,0,0,0.58)" if theme == "dark" else "0 8px 25px rgba(0,0,0,0.13)"
    sidebar_bg  = "rgba(10,13,20,0.97)" if theme == "dark" else "rgba(248,251,255,0.97)"

    # ── Inject fonts + main CSS ────────────────────────────────────────
    st.markdown(f"""
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --accent-primary: {accent_primary};
            --accent-gold: {accent_gold};
            --accent-glow: {accent_glow};
            --gold-gradient: linear-gradient(135deg, #FFD700 0%, #B8860B 100%);
            --metric-white: #FFFFFF;
            --max-app-width: 1320px;
        }}

        /* ── GLOBAL BASE ── */
        html, body, .stApp {{
            font-family: 'Poppins', sans-serif !important;
            background: {bg_color} !important;
            color: {text_primary} !important;
            scroll-behavior: smooth;
            font-size: clamp(14px, 3.4vw, 16px) !important;   /* ← mobile friendly base */
        }}

        p, div, span, li {{
            font-size: clamp(0.92rem, 2.9vw, 1.05rem) !important;
            line-height: 1.58 !important;
        }}

        h1 {{
            font-size: clamp(1.9rem, 6.2vw, 2.8rem) !important;
            margin: 0.8rem 0 !important;
        }}
        h2 {{
            font-size: clamp(1.55rem, 5.2vw, 2.2rem) !important;
        }}
        h3, .stSubheader {{
            font-size: clamp(1.28rem, 4.4vw, 1.65rem) !important;
        }}

        .main .block-container {{
            max-width: var(--max-app-width) !important;
            margin: 0 auto !important;
            padding: 2rem 1.5rem !important;
        }}

        /* ── METRIC CARDS ── */
        [data-testid="stMetricLabel"] {{
            color: var(--metric-white) !important;
            font-size: clamp(0.85rem, 2.8vw, 1rem) !important;
            font-weight: 500 !important;
            letter-spacing: 0.5px;
            opacity: 0.9;
        }}
        [data-testid="stMetricValue"] {{
            color: var(--metric-white) !important;
            font-size: clamp(1.7rem, 5.8vw, 2.5rem) !important;
            font-weight: 700 !important;
            text-shadow: 0 0 15px rgba(255,255,255,0.25);
        }}
        [data-testid="stMetric"] {{
            background: rgba(255,255,255,0.05) !important;
            border-radius: 20px !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
            padding: 1.4rem !important;
            transition: all 0.3s ease;
        }}
        [data-testid="stMetric"]:hover {{
            transform: translateY(-6px);
            border-color: var(--accent-gold) !important;
            background: rgba(255,255,255,0.08) !important;
        }}

        /* ── GLASS CARDS ── */
        .glass-card {{
            background: {card_bg} !important;
            backdrop-filter: blur(24px);
            -webkit-backdrop-filter: blur(24px);
            border: 1px solid {border_color} !important;
            border-radius: 22px !important;
            padding: clamp(1.4rem, 4.5vw, 2.4rem) !important;
            box-shadow: {card_shadow} !important;
            transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
            margin: 1.6rem auto;
        }}
        .glass-card:hover {{
            transform: translateY(-8px);
            box-shadow: 0 22px 55px var(--accent-glow) !important;
            border-color: rgba(0,255,170,0.9) !important;
        }}

        /* ── GOLD TEXT ── */
        .gold-text {{
            background: var(--gold-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 700;
            letter-spacing: 0.6px;
            filter: drop-shadow(0 1px 3px rgba(0,0,0,0.4));
        }}

        /* ── PRIMARY BUTTONS ── */
        button[kind="primary"] {{
            background: var(--accent-primary) !important;
            color: #000000 !important;
            border: none !important;
            border-radius: 14px !important;
            padding: 0.85rem 2.4rem !important;
            font-weight: 700 !important;
            font-size: clamp(0.98rem, 3.4vw, 1.08rem) !important;
            text-transform: uppercase;
            letter-spacing: 1px;
            box-shadow: 0 5px 16px var(--accent-glow) !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }}
        button[kind="primary"]:hover {{
            transform: translateY(-2px) scale(1.02);
            box-shadow: 0 10px 25px {accent_glow}cc !important;
        }}
        button[key="lang_toggle_public"],
        div[data-testid="stFormSubmitButton"] button {{
            background: #00ffa2 !important;
            color: #000000 !important;
        }}

        /* ── FORM INPUTS (base style for non-golden fields) ── */
        .stTextInput input:not([aria-label*="username" i]):not([aria-label*="Username" i]):not([aria-label*="name" i]):not([aria-label*="Name" i]):not([aria-label*="email" i]):not([aria-label*="Email" i]),
        .stTextArea textarea:not([data-testid="stTextArea"]) {{
            background: rgba(255,255,255,0.09) !important;
            color: white !important;
            border: 1px solid rgba(255,215,0,0.18) !important;
            border-radius: 12px !important;
            padding: 12px 16px !important;
            font-size: clamp(0.95rem, 3.2vw, 1.05rem) !important;
            transition: all 0.25s ease;
        }}

        /* ── GOLDEN THEME FOR LOGIN / REGISTRATION FIELDS ── */
        input[aria-label*="username" i],
        input[aria-label*="Username" i],
        input[type="password"],
        input[aria-label*="password" i],
        input[aria-label*="name" i],
        input[aria-label*="Name" i],
        input[type="email"],
        input[aria-label*="email" i],
        input[aria-label*="Email" i],
        textarea[data-testid="stTextArea"] {{
            background: {gold_bg_normal} !important;
            color: #000000 !important;
            border: 1px solid {gold_border} !important;
            caret-color: #000000 !important;
            font-size: clamp(0.95rem, 3.2vw, 1.05rem) !important;
        }}

        /* Focused state - golden glow */
        input[aria-label*="username" i]:focus,
        input[aria-label*="Username" i]:focus,
        input[type="password"]:focus,
        input[aria-label*="name" i]:focus,
        input[aria-label*="Name" i]:focus,
        input[type="email"]:focus,
        textarea[data-testid="stTextArea"]:focus {{
            background: {gold_bg_focus} !important;
            border-color: {gold_focus} !important;
            box-shadow: 0 0 16px rgba(255,215,0,0.50) !important;
            color: #000000 !important;
        }}

        /* Dark gray placeholders */
        input[aria-label*="username" i]::placeholder,
        input[aria-label*="Username" i]::placeholder,
        input[type="password"]::placeholder,
        input[aria-label*="name" i]::placeholder,
        input[aria-label*="Name" i]::placeholder,
        input[type="email"]::placeholder,
        textarea[data-testid="stTextArea"]::placeholder {{
            color: #333333 !important;
            opacity: 0.70 !important;
            font-weight: 400;
        }}

        /* ── GOLD GRADIENT LABELS ── */
        .stTextInput > label,
        .stTextInput > div > label,
        .stTextArea > label,
        .stTextArea > div > label {{
            background: var(--gold-gradient) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            font-weight: 700 !important;
            letter-spacing: 0.4px !important;
            filter: drop-shadow(0 1px 4px rgba(0,0,0,0.6)) !important;
            padding-bottom: 4px !important;
            font-size: clamp(0.9rem, 3vw, 1.05rem) !important;
        }}

        /* Helper text / caption / error messages */
        p[data-testid="stCaption"],
        small,
        .stTextInput div[role="alert"],
        .stTextArea div[role="alert"] {{
            color: #111111 !important;
            font-size: clamp(0.82rem, 2.6vw, 0.92rem) !important;
        }}

        textarea[data-testid="stTextArea"] {{
            min-height: 110px !important;
            resize: vertical !important;
        }}

        /* ── SUCCESS BOX ── */
        .success-box {{
            background: linear-gradient(135deg, rgba(0,255,162,0.16) 0%, rgba(0,255,162,0.09) 100%) !important;
            border: 1px solid #00ffa2 !important;
            padding: 22px !important;
            border-radius: 16px !important;
            text-align: center;
            color: white !important;
        }}

        /* ── LOGIN CARD & TABS ── */
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
            gap: 8px !important;
            display: flex !important;
            justify-content: stretch !important;
        }}
        [data-baseweb="tab"] {{
            flex: 1 !important;
            color: #FFD700 !important;
            font-weight: 700 !important;
            border-radius: 10px !important;
            transition: all 0.3s ease;
            font-size: clamp(0.9rem, 3.2vw, 1rem) !important;
        }}
        [aria-selected="true"] {{
            background: var(--gold-gradient) !important;
            color: #000000 !important;
            box-shadow: 0 4px 16px rgba(255,215,0,0.4) !important;
        }}

        /* ── HEADER & SIDEBAR ── */
        header[data-testid="stHeader"] {{
            background-color: transparent !important;
            backdrop-filter: blur(12px) !important;
        }}
        section[data-testid="stSidebar"] {{
            background: {sidebar_bg} !important;
            border-right: 1px solid {border_color} !important;
        }}

        /* ── MOBILE OPTIMIZATIONS (enhanced) ── */
        @media (max-width: 768px) {{
            .main .block-container {{
                max-width: 100% !important;
                padding: 0.9rem 1rem !important;
            }}
            .glass-card {{
                padding: 1.2rem !important;
                margin: 1rem 0.4rem !important;
                border-radius: 16px !important;
            }}
            .login-box {{
                padding: 1.8rem 1.4rem !important;
                max-width: 96% !important;
                margin: 1.2rem auto !important;
            }}
            button[kind="primary"] {{
                width: 100% !important;
                padding: 1rem !important;
                font-size: 1.02rem !important;
            }}
            section[data-testid="stSidebar"] {{
                min-width: 240px !important;
            }}
            .glass-card:hover, .glass-card:active {{
                transform: scale(1.015);
                box-shadow: 0 14px 35px var(--accent-glow) !important;
            }}
        }}

        /* ── SCROLLBAR ── */
        ::-webkit-scrollbar {{ width: 8px; }}
        ::-webkit-scrollbar-track {{ background: {bg_color}; }}
        ::-webkit-scrollbar-thumb {{ background: {border_color}; border-radius: 10px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: var(--accent-gold); }}

        /* ── HR SEPARATOR ── */
        hr {{
            border: 0;
            height: 1px;
            background: rgba(255,255,255,0.06);
            border-bottom: 1px solid rgba(0,0,0,0.45);
            margin: 2.4rem 0 !important;
            box-shadow: 0 1px 3px rgba(255,215,0,0.08);
        }}
    </style>
    """, unsafe_allow_html=True)