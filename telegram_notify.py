import os
import requests
import logging

log = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram_message(text):
    """Send a message to Telegram if credentials are set."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return  # Skip silently if not configured

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        response = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }, timeout=10)
        if response.status_code == 200:
            log.info("📱 Telegram notification sent")
        else:
            log.warning(f"Telegram send failed: {response.text}")
    except Exception as e:
        log.warning(f"Telegram notification error: {e}")


def notify_upload_success(video_id, qdata, video_number):
    text = (
        f"🎬 <b>New Short Uploaded!</b>\n\n"
        f"📊 Short #{video_number}\n"
        f"📚 Category: {qdata.get('category','GK')}\n"
        f"❓ {qdata['question'][:100]}\n\n"
        f"▶️ https://youtu.be/{video_id}\n\n"
        f"✅ Bot running smoothly on Azure!"
    )
    send_telegram_message(text)

def notify_upload_failed(error_msg):
    text = (
        f"❌ <b>Upload Failed!</b>\n\n"
        f"Error: {error_msg}\n\n"
        f"⚠️ Please check the bot logs."
    )
    send_telegram_message(text)

def notify_bot_started():
    text = (
        f"🤖 <b>GK Shorts Bot Started!</b>\n\n"
        f"📅 6 Shorts/day\n"
        f"💬 Comment checking active\n"
        f"☁️ Running on Azure 24/7"
    )
    send_telegram_message(text)
