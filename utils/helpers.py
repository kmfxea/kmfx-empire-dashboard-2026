# utils/helpers.py
"""
Reusable utility functions for the KMFX EA app
- File upload to Supabase Storage
- Image resizing (for testimonials, timeline photos, etc.)
- Action logging to Supabase logs table
- Keep-alive ping for Streamlit Cloud
- Other small helpers used across pages
"""

import uuid
import requests
import threading
import time
from io import BytesIO
from PIL import Image
import streamlit as st
from datetime import datetime

from utils.supabase_client import supabase


def upload_to_supabase(
    file,
    bucket: str,
    folder: str = "",
    use_signed_url: bool = False,
    signed_expiry: int = 3600
) -> tuple[str | None, str | None]:
    """
    Upload file to Supabase Storage
    Returns (public_url or signed_url, storage_path) or (None, None) on failure
    """
    try:
        safe_name = f"{uuid.uuid4()}_{file.name}"
        file_path = f"{folder}/{safe_name}" if folder else safe_name

        # Get bytes safely
        if hasattr(file, "getvalue"):
            content = file.getvalue()
        elif hasattr(file, "read"):
            content = file.read()
        else:
            content = file  # assume already bytes

        with st.spinner(f"Uploading {file.name}..."):
            supabase.storage.from_(bucket).upload(
                path=file_path,
                file=content,
                file_options={
                    "content-type": file.type or "application/octet-stream",
                    "upsert": "true"
                }
            )

        if use_signed_url:
            signed = supabase.storage.from_(bucket).create_signed_url(file_path, signed_expiry)
            url = signed.get("signedURL")
        else:
            url = supabase.storage.from_(bucket).get_public_url(file_path)

        st.success(f"✅ {file.name} uploaded")
        return url, file_path

    except Exception as e:
        st.error(f"Upload failed for {file.name}: {str(e)}")
        return None, None


def make_same_size(
    image_path,
    target_width: int = 800,
    target_height: int = 500
) -> Image.Image:
    """
    Center-crop and resize image to exact dimensions without distortion
    Used for timeline photos, testimonials, etc.
    """
    try:
        img = Image.open(image_path)
        target_ratio = target_width / target_height
        img_ratio = img.width / img.height

        if img_ratio > target_ratio:  # too wide → crop sides
            new_width = int(img.height * target_ratio)
            left = (img.width - new_width) // 2
            img = img.crop((left, 0, left + new_width, img.height))
        elif img_ratio < target_ratio:  # too tall → crop top/bottom
            new_height = int(img.width / target_ratio)
            top = (img.height - new_height) // 2
            img = img.crop((0, top, img.width, top + new_height))

        img = img.resize((target_width, target_height), Image.LANCZOS)
        return img
    except Exception as e:
        st.warning(f"Image resize failed: {e}")
        return Image.new("RGB", (target_width, target_height), color=(200, 200, 200))


def log_action(
    action: str,
    details: str = "",
    user_name: str = None
):
    """
    Log important user/admin actions to Supabase logs table
    """
    user_name = user_name or st.session_state.get("full_name", "Unknown")
    user_type = st.session_state.get("role", "unknown")

    try:
        supabase.table("logs").insert({
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "details": details,
            "user_type": user_type,
            "user_name": user_name
        }).execute()
    except Exception:
        # Silent fail — logging should not break the app
        pass


def keep_alive():
    """
    Simple keep-alive ping to prevent Streamlit Cloud from sleeping
    Runs in background thread
    """
    url = "https://kmfxeaftmo.streamlit.app"  # ← palitan kung iba ang app URL mo
    while True:
        try:
            requests.get(url, timeout=10)
        except:
            pass
        time.sleep(1500)  # ~25 minutes


def start_keep_alive_if_needed():
    """
    Start the keep-alive thread only once (call in main.py)
    """
    if "keep_alive_started" not in st.session_state:
        if os.getenv("STREAMLIT_SHARING") or os.getenv("STREAMLIT_CLOUD"):
            thread = threading.Thread(target=keep_alive, daemon=True)
            thread.start()
            st.session_state.keep_alive_started = True


# Optional: small helper for generating QR URLs (used in Admin Management & Profile)
def generate_qr_url(app_base_url: str, qr_token: str) -> str:
    """Generate full QR login URL"""
    return f"{app_base_url}/?qr={qr_token}"


# Optional: QR code image generator (used when displaying QR)
def generate_qr_image(url: str, fill_color="#000000", back_color="#ffffff") -> BytesIO:
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color=fill_color, back_color=back_color)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf