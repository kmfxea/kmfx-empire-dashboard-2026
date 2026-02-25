# utils/supabase_client.py
"""
Centralized Supabase client with caching & better error messages
Gamitin 'to sa lahat ng files: from utils.supabase_client import supabase
"""
from supabase import create_client, Client
import streamlit as st
import os
from dotenv import load_dotenv

# Load .env only in local development (Streamlit Cloud uses secrets)
if os.getenv("STREAMLIT_SHARING") is None and os.getenv("STREAMLIT_CLOUD") is None:
    load_dotenv()  # local .env lang, hindi sa production

@st.cache_resource(show_spinner=False)
def get_supabase() -> Client:
    """
    Cached Supabase client – never recreated during reruns.
    Priority order: Streamlit secrets > .env > raise clear error
    """
    url = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY") or os.getenv("SUPABASE_KEY")

    if not url or not key:
        error_msg = (
            "Missing Supabase credentials!\n\n"
            "Please set the following in Streamlit Cloud Secrets (preferred):\n"
            "- SUPABASE_URL\n"
            "- SUPABASE_KEY\n\n"
            "Or in local .env file:\n"
            "SUPABASE_URL=https://your-project.supabase.co\n"
            "SUPABASE_KEY=your-anon-or-service-key"
        )
        st.error(error_msg)
        raise ValueError(error_msg)

    try:
        client = create_client(url, key)
        # Optional: quick health check (can remove if not needed)
        # client.table("users").select("count", count="exact").limit(0).execute()
        return client
    except Exception as e:
        st.error(f"Failed to initialize Supabase client: {str(e)}")
        raise

# Global singleton – import and use directly
supabase: Client = get_supabase()