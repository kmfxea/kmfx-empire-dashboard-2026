"""
Centralized Supabase client with caching, timeouts, and retry.
Gamitin 'to sa lahat ng files para consistent at stable ang connection.
"""
from supabase import create_client, Client
import streamlit as st
import os
import time
from httpx import Timeout, ConnectError, ReadTimeout

@st.cache_resource(show_spinner="Connecting to Supabase...")
def get_supabase() -> Client:
    """
    Cached Supabase client — hindi na nagrerecreate sa bawat rerun.
    Priority: Streamlit secrets > environment variables > error
    """
    url = (
        st.secrets.get("SUPABASE_URL")
        or os.getenv("SUPABASE_URL")
        or os.getenv("SUPABASE_URL")  # double-check env for local
    )
    key = (
        st.secrets.get("SUPABASE_KEY")
        or os.getenv("SUPABASE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")  # common fallback name
    )

    if not url or not key:
        raise ValueError(
            "Missing Supabase credentials!\n\n"
            "1. Go to Streamlit Cloud → Manage app → Secrets\n"
            "2. Add:\n"
            "   SUPABASE_URL = https://your-project-ref.supabase.co\n"
            "   SUPABASE_KEY = eyJhbGciOiJIUzI1NiIs... (anon key)\n\n"
            "Or for local dev: create .env with the same keys."
        )

    # Long timeouts to survive free-tier sleep/wake-up (30-60s common)
    timeout = Timeout(
        connect=15.0,    # time to establish connection
        read=90.0,       # time to wait for response data
        write=30.0,
        pool=15.0
    )

    # Create client with timeout
    client = create_client(
        supabase_url=url,
        supabase_key=key,
        options={"http": {"timeout": timeout}}
    )

    # Simple retry wrapper for first query (wake-up robustness)
    def retry_first_query(max_retries=2):
        for attempt in range(max_retries):
            try:
                # Test ping
                client.table("users").select("count(*)", count="exact", head=True).execute()
                return client
            except (ConnectError, ReadTimeout) as e:
                if attempt == max_retries - 1:
                    raise Exception(f"Supabase connection failed after {max_retries} retries: {str(e)}")
                time.sleep(2 ** attempt)  # exponential backoff: 1s, 2s, ...

    # Run retry on first use
    retry_first_query()

    return client


# Global singleton access — import lang 'to sa ibang files
supabase = get_supabase()