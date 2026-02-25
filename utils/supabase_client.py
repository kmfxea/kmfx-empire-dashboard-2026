# utils/supabase_client.py
"""
Centralized Supabase client with caching
Gamitin 'to sa lahat ng files para iwas sa paulit-ulit na create_client
"""

from supabase import create_client, Client
import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()  # para sa local dev (.env file)

@st.cache_resource
def get_supabase() -> Client:
    """
    Cached Supabase client — hindi na nagrerecreate sa bawat rerun
    Priority: Streamlit secrets > .env > error
    """
    url = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY") or os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise ValueError(
            "Kailangan ng SUPABASE_URL at SUPABASE_KEY.\n"
            "Ilagay sa Streamlit Cloud Secrets o sa .env file."
        )

    return create_client(url, key)


# Global access — import lang 'to sa ibang files
supabase = get_supabase()