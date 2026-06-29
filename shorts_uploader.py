import os
import pickle
import base64
import json
import time
import logging
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

log = logging.getLogger(__name__)

def get_youtube():
    creds = None
    token_b64 = os.environ.get("YOUTUBE_TOKEN_B64")
    if token_b64:
        creds = pickle.loads(base64.b64decode(token_b64))
    elif os.path.exists("token.pickle"):
        with open("token.pickle","rb") as f:
            creds = pickle.load(f)
    else:
        raise Exception("No YouTube token found!")
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build("youtube","v3",credentials=creds)

def upload_short(video_path, qdata, number=1):
    youtube  = get_youtube()
    topic    = qdata.get("topic","General Knowledge")
    category = qdata.get("category","GK")
    question = qdata["question"]
    answer   = qdata["answer"]

    icons = {"GK":"🌍","Science":"🔬","Math":"➕"}
    icon  = icons.get(category,"🧠")

    title = f"{icon} {question[:55]}... #Shorts"
    desc  = f"""{icon} {category} Quiz Short #{number}!

❓ {question}

A. {qdata['options']['A']}
B. {qdata['options']['B']}
C. {qdata['options']['C']}
D. {qdata['options']['D']}

💬 Comment A / B / C / D — bot will reply ✅ or ❌!
✅ Answer revealed at the end of the video!

📚 Topic: {topic}

#Shorts #Quiz #{category}Quiz #GKQuiz #MCQ #{topic.replace(' ','')} #YoutubeShorts #ShortsFeed
"""

    body = {
        "snippet": {
            "title": title,
            "description": desc,
            "tags": ["Shorts","Quiz",f"{category}Quiz","GKQuiz",
                    "MCQ",topic,"YoutubeShorts","ShortsFeed"],
            "categoryId": "27",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        }
    }

    media   = MediaFileUpload(video_path, chunksize=-1,
                              resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(
        part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            log.info(f"   {int(status.progress()*100)}% uploaded...")

    video_id = response["id"]
    log.info(f"✅ Uploaded: https://youtu.be/{video_id}")

    # Save to local DB
    _save_video(video_id, qdata)
    return video_id


def _save_video(video_id, qdata):
    db = _load_db()
    db[video_id] = {
        "question": qdata["question"],
        "answer":   qdata["answer"],
        "topic":    qdata.get("topic",""),
        "category": qdata.get("category","GK"),
        "replied":  []
    }
    _save_db(db)

def _load_db():
    if os.path.exists("videos_db.json"):
        with open("videos_db.json") as f:
            return json.load(f)
    return {}

def _save_db(db):
    with open("videos_db.json","w") as f:
        json.dump(db, f, indent=2)


def check_and_reply_comments():
    """Scan all video comments and reply ✅ or ❌."""
    db      = _load_db()
    if not db:
        log.info("No videos yet.")
        return

    youtube = get_youtube()
    replied = 0

    for video_id, meta in db.items():
        correct = meta["answer"].upper()
        done    = set(meta.get("replied", []))

        try:
            resp = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=100,
                order="time"
            ).execute()
        except Exception as e:
            log.error(f"Can't fetch comments for {video_id}: {e}")
            continue

        for item in resp.get("items", []):
            top     = item["snippet"]["topLevelComment"]
            cid     = top["id"]
            author  = top["snippet"]["authorDisplayName"]
            raw     = top["snippet"]["textDisplay"].strip().upper()

            if cid in done:
                continue

            # Extract option letter from comment
            option = None
            for opt in ["A","B","C","D"]:
                if raw == opt or raw.startswith(f"{opt} ") or raw.startswith(f"{opt}."):
                    option = opt
                    break

            if option is None:
                continue  # Not an A/B/C/D comment, skip

            if option == correct:
                reply = (
                    f"✅ Correct {author}! 🎉 Well done!\n"
                    f"You nailed it! Keep playing our quiz! 💪\n"
                    f"👍 Like & Subscribe for 6 quiz videos daily!"
                )
            else:
                reply = (
                    f"❌ Not quite {author}! The correct answer is {correct}. 🧠\n"
                    f"Watch the full video to learn why!\n"
                    f"👍 Like & Subscribe for 6 quiz videos daily!"
                )

            try:
                youtube.comments().insert(
                    part="snippet",
                    body={
                        "snippet": {
                            "parentId": cid,
                            "textOriginal": reply
                        }
                    }
                ).execute()
                done.add(cid)
                replied += 1
                log.info(f"💬 Replied to {author} → {'✅' if option==correct else '❌'}")
                time.sleep(2)  # Avoid quota issues
            except Exception as e:
                log.error(f"Reply failed: {e}")

        meta["replied"] = list(done)

    _save_db(db)
    log.info(f"✅ Done — replied to {replied} new comments!")
