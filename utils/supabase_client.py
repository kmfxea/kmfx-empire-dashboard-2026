"""
Centralized Supabase clients + auth object
Usage:
from utils.supabase_client import supabase, service_supabase, auth

- supabase: normal queries (follows RLS rules)
- service_supabase: admin/QR verification (bypasses RLS – use carefully!)
- auth: Supabase auth object (sign_in_with_otp, get_session, etc.)
"""
from supabase import create_client, Client
import streamlit as st
import os
from datetime import timedelta

# Load .env only in local development (Streamlit Cloud uses secrets)
if os.getenv("STREAMLIT_SHARING") is None and os.getenv("STREAMLIT_CLOUD") is None:
    from dotenv import load_dotenv
    load_dotenv()

@st.cache_resource(ttl=timedelta(hours=1), show_spinner=False)
def get_anon_supabase() -> Client:
    """
    Anon/public client – for normal queries (follows RLS)
    Uses SUPABASE_KEY (public/anon key)
    """
    url = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY") or os.getenv("SUPABASE_KEY")

    if not url or not key:
        st.error("""
Missing Supabase anon credentials!

Please add to Streamlit Cloud Secrets:
SUPABASE_URL = https://your-project-ref.supabase.co
SUPABASE_KEY = eyJhbGciOiJIUzI1NiIs... (anon/public key)
        """)
        raise ValueError("Anon credentials missing")

    try:
        client = create_client(url, key)
        # Optional health check (uncomment to test connection on init)
        # client.table("users").select("count", count="exact").limit(0).execute()
        return client
    except Exception as e:
        st.error(f"Failed to init anon client: {str(e)}\nCheck URL and anon key.")
        raise

@st.cache_resource(ttl=timedelta(hours=1), show_spinner=False)
def get_service_supabase() -> Client:
    """
    Service role client – bypasses RLS (admin/QR tasks)
    Uses SUPABASE_SERVICE_ROLE_KEY
    """
    url = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        st.error("""
Missing service_role key!

Add to Streamlit Cloud Secrets:
SUPABASE_SERVICE_ROLE_KEY = eyJhbGciOiJIUzI1NiIs... (copy from Supabase → Settings → API → service_role)
        """)
        raise ValueError("Service role key missing")

    try:
        client = create_client(url, key)
        return client
    except Exception as e:
        st.error(f"Failed to init service client: {str(e)}\nCheck service_role key.")
        raise

# ────────────────────────────────────────────────
# Global exports – import these directly
# ────────────────────────────────────────────────
supabase: Client = get_anon_supabase()           # normal queries (follows RLS)
service_supabase: Client = get_service_supabase()  # for QR/login bypass & admin
auth = supabase.auth                             # Supabase auth object (magic link, sessions, etc.)