"""
Centralized Supabase clients (anon + service_role)
Gamitin:
- from utils.supabase_client import supabase, service_supabase
"""
from supabase import create_client, Client
import streamlit as st
import os
from dotenv import load_dotenv

# Load .env only in local dev (Streamlit Cloud uses secrets)
if os.getenv("STREAMLIT_SHARING") is None and os.getenv("STREAMLIT_CLOUD") is None:
    load_dotenv()

@st.cache_resource(show_spinner=False)
def _create_anon_client() -> Client:
    """Anon/public client – for normal queries (follows RLS)"""
    url = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY") or os.getenv("SUPABASE_KEY")

    if not url or not key:
        error_msg = (
            "Missing Supabase anon credentials!\n\n"
            "Set in Streamlit Secrets:\n"
            "- SUPABASE_URL\n"
            "- SUPABASE_KEY (anon/public key)"
        )
        st.error(error_msg)
        raise ValueError(error_msg)

    try:
        client = create_client(url, key)
        # Quick health check (optional – remove if annoying)
        # client.table("users").select("count", count="exact").limit(0).execute()
        return client
    except Exception as e:
        st.error(f"Failed to init anon Supabase client: {str(e)}")
        raise

@st.cache_resource(show_spinner=False)
def _create_service_client() -> Client:
    """Service role client – bypasses RLS (for admin/QR verification)"""
    url = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        error_msg = (
            "Missing Supabase service_role credentials!\n\n"
            "Add to Streamlit Secrets:\n"
            "- SUPABASE_SERVICE_ROLE_KEY (from Supabase API settings)"
        )
        st.error(error_msg)
        raise ValueError(error_msg)

    try:
        client = create_client(url, key)
        return client
    except Exception as e:
        st.error(f"Failed to init service Supabase client: {str(e)}")
        raise

# Global singletons – import and use these
supabase: Client = _create_anon_client()          # normal use (follows RLS)
service_supabase: Client = _create_service_client()  # for QR/login bypass