# utils/helpers.py
"""
Reusable utility functions for KMFX EA Dashboard
- File upload to Supabase Storage (with signed URL option)
- Image resizing (uniform size with padding for journey/timeline/testimonials)
- Action logging to Supabase logs table
- Keep-alive ping to prevent Streamlit Cloud sleep
- QR code generation helpers
"""
import os
import uuid
import requests
import threading
import time
from datetime import datetime
from io import BytesIO
from PIL import Image
import streamlit as st
import qrcode

from utils.supabase_client import supabase

# ────────────────────────────────────────────────
# IMAGE RESIZING – Uniform size with padding (800x700 default)
# ────────────────────────────────────────────────
def make_same_size(image_input, target_width=800, target_height=700, bg_color=(0, 0, 0)):
    """
    Resize image to exact target size with centered padding (black bg for dark theme).
    Accepts:
    - Local file path (str)
    - Uploaded file object (with .getvalue() or .read())
    - BytesIO or raw bytes
    Returns bytes ready for st.image() or None on failure
    """
    try:
        # Handle different input types
        if isinstance(image_input, str):  # local path
            img = Image.open(image_input)
        elif hasattr(image_input, "getvalue"):  # UploadedFile.getvalue()
            img = Image.open(BytesIO(image_input.getvalue()))
        elif hasattr(image_input, "read"):  # file-like object
            img = Image.open(BytesIO(image_input.read()))
        else:  # assume raw bytes
            img = Image.open(BytesIO(image_input))

        # Resize preserving aspect ratio
        img.thumbnail((target_width, target_height), Image.LANCZOS)

        # Create new image with target size + background
        new_img = Image.new("RGB", (target_width, target_height), bg_color)
        offset = ((target_width - img.width) // 2, (target_height - img.height) // 2)
        new_img.paste(img, offset)

        # Convert to bytes
        buf = BytesIO()
        new_img.save(buf, format="PNG")
        buf.seek(0)
        return buf.getvalue()
    except Exception as e:
        st.warning(f"Image resize failed: {str(e)}")
        return None

# ────────────────────────────────────────────────
# UPLOAD TO SUPABASE STORAGE
# ────────────────────────────────────────────────
def upload_to_supabase(file, bucket: str, folder: str = "", use_signed_url: bool = False, signed_expiry: int = 604800):
    """
    Upload file to Supabase Storage
    Returns (url, storage_path) or (None, None) on failure
    - use_signed_url=True → returns 7-day signed URL (private buckets)
    - use_signed_url=False → returns public URL (if bucket is public)
    """
    try:
        file_name = getattr(file, "name", f"file_{uuid.uuid4().hex}")
        safe_name = f"{uuid.uuid4()}_{file_name}"
        storage_path = f"{folder}/{safe_name}" if folder else safe_name

        # Get bytes safely
        if hasattr(file, "getvalue"):
            content = file.getvalue()
        elif hasattr(file, "read"):
            content = file.read()
        else:
            content = file  # assume bytes

        with st.spinner(f"Uploading {file_name}..."):
            supabase.storage.from_(bucket).upload(
                path=storage_path,
                file=content,
                file_options={
                    "content-type": getattr(file, "type", "application/octet-stream"),
                    "upsert": "true"
                }
            )

        if use_signed_url:
            signed = supabase.storage.from_(bucket).create_signed_url(storage_path, signed_expiry)
            url = signed.get("signedURL") if signed else None
        else:
            url = supabase.storage.from_(bucket).get_public_url(storage_path)

        st.success(f"✅ {file_name} uploaded")
        return url, storage_path
    except Exception as e:
        st.error(f"Upload failed: {str(e)}")
        return None, None

# ────────────────────────────────────────────────
# LOG ACTION TO SUPABASE LOGS TABLE
# ────────────────────────────────────────────────
def log_action(action: str, details: str = "", user_name: str = None, user_type: str = None):
    """
    Log important actions to logs table (silent fail if error)
    """
    user_name = user_name or st.session_state.get("full_name", "Unknown")
    user_type = user_type or st.session_state.get("role", "unknown")

    try:
        supabase.table("logs").insert({
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "details": details,
            "user_type": user_type,
            "user_name": user_name
        }).execute()
    except Exception:
        # Silent – logging should never break the app
        pass

# ────────────────────────────────────────────────
# KEEP-ALIVE THREAD – Prevent Streamlit Cloud sleep
# ────────────────────────────────────────────────
def keep_alive():
    """Ping the app every ~25 minutes to keep it awake on Cloud"""
    url = "https://kmfxea.streamlit.app"  # ← CHANGE TO YOUR ACTUAL LIVE URL
    while True:
        try:
            requests.get(url, timeout=10)
        except:
            pass
        time.sleep(1500)  # 25 minutes

def start_keep_alive_if_needed():
    """Start keep-alive only once and only on Cloud"""
    if "keep_alive_started" not in st.session_state:
        if os.getenv("STREAMLIT_SHARING") or os.getenv("STREAMLIT_CLOUD"):
            thread = threading.Thread(target=keep_alive, daemon=True)
            thread.start()
            st.session_state.keep_alive_started = True

# ────────────────────────────────────────────────
# QR CODE GENERATORS (for profile/admin QR display)
# ────────────────────────────────────────────────
def generate_qr_url(app_base_url: str, qr_token: str) -> str:
    """Generate full QR login URL"""
    return f"{app_base_url}/?qr={qr_token}"

def generate_qr_image(url: str, fill_color="#000000", back_color="#ffffff", box_size=10, border=4) -> BytesIO:
    """Generate QR code image as BytesIO for st.image()"""
    try:
        qr = qrcode.QRCode(version=1, box_size=box_size, border=border)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color=fill_color, back_color=back_color)
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf
    except Exception as e:
        st.warning(f"QR generation failed: {str(e)}")
        return BytesIO()