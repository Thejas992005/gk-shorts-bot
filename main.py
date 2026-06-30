import os
import json
import time
import schedule
import logging
from question_generator import generate_question
from shorts_creator import create_short
from shorts_uploader import upload_short, check_and_reply_comments
from telegram_notify import notify_upload_success, notify_upload_failed, notify_bot_started

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()]
)
log = logging.getLogger(__name__)

SHORTS_PER_DAY          = 6
UPLOAD_EVERY_HOURS      = 24 // SHORTS_PER_DAY  # 4 hours
COMMENT_CHECK_EVERY_MIN = 15
VIDEOS_DIR              = "videos"
COUNTER_FILE            = "counter.json"

os.makedirs(VIDEOS_DIR, exist_ok=True)

def get_count():
    if os.path.exists(COUNTER_FILE):
        return json.load(open(COUNTER_FILE)).get("n", 1)
    return 1

def save_count(n):
    json.dump({"n": n}, open(COUNTER_FILE,"w"))

def run_upload():
    n = get_count()
    log.info(f"🚀 Pipeline starting for Short #{n}")

    # 1 — Generate question
    try:
        log.info("🧠 Generating question...")
        qdata = generate_question()
        log.info(f"✅ [{qdata['category']}] {qdata['question'][:60]}...")
    except Exception as e:
        log.error(f"❌ Question failed: {e}")
        notify_upload_failed(f"Question generation failed: {e}")
        return

    # 2 — Create Short
    path = os.path.join(VIDEOS_DIR, f"short_{n}.mp4")
    try:
        log.info("🎬 Creating Short (1080×1920)...")
        create_short(qdata, path)
    except Exception as e:
        log.error(f"❌ Video failed: {e}")
        notify_upload_failed(f"Video creation failed: {e}")
        return

    # 3 — Upload
    try:
        log.info("📤 Uploading to YouTube...")
        vid = upload_short(path, qdata, n)
        log.info(f"🎉 Live at https://youtu.be/{vid}")
        notify_upload_success(vid, qdata, n)
    except Exception as e:
        log.error(f"❌ Upload failed: {e}")
        notify_upload_failed(f"Upload failed: {e}")
        return

    # 4 — Cleanup
    try: os.remove(path)
    except: pass

    save_count(n + 1)
    log.info(f"✅ Short #{n} done! Next in {UPLOAD_EVERY_HOURS}h\n")

def run_comment_check():
    log.info("💬 Checking comments...")
    try:
        check_and_reply_comments()
    except Exception as e:
        log.error(f"❌ Comment check failed: {e}")

def main():
    log.info("="*55)
    log.info("🤖 GK SHORTS BOT STARTED!")
    log.info(f"📅 {SHORTS_PER_DAY} Shorts/day | every {UPLOAD_EVERY_HOURS} hours")
    log.info(f"💬 Comment check every {COMMENT_CHECK_EVERY_MIN} mins")
    log.info("="*55)

    notify_bot_started()

    # Run immediately
    run_upload()

    # Schedule uploads every 4 hours
    schedule.every(UPLOAD_EVERY_HOURS).hours.do(run_upload)

    # Check comments every 15 minutes
    schedule.every(COMMENT_CHECK_EVERY_MIN).minutes.do(run_comment_check)

    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
