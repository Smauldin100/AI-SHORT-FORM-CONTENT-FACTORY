import os
import sys
import json
import time
import uuid
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_FILE = BASE_DIR / "data" / "videos.json"
AUDIO_DIR = BASE_DIR / "audio"
VIDEOS_DIR = BASE_DIR / "videos"

AUDIO_DIR.mkdir(parents=True, exist_ok=True)
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
HEYGEN_API_KEY = os.getenv("HEYGEN_API_KEY")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME", "Videos")

HEADERS = {"User-Agent": "heygen-agent/1.0"}


def save_record_local(record):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            arr = json.load(f)
    else:
        arr = []
    arr.append(record)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(arr, f, indent=2)


def generate_script_openai(topic):
    if not OPENAI_API_KEY:
        # simple fallback prompt-based script
        title = f"{topic} - Quick Tip"
        script = f"Hook: Want a quick {topic} tip?\nValue: Here's one fast tip you can use today...\nCTA: Follow for more."
        return {"title": title, "script": script}
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    prompt = (
        f"Create a 15-30 second TikTok style script for the topic '{topic}'. Include a hook, value, and CTA. "
        "Return only the script text."
    )
    body = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8,
        "max_tokens": 200,
    }
    r = requests.post(url, headers=headers, json=body)
    r.raise_for_status()
    res = r.json()
    script_text = res["choices"][0]["message"]["content"].strip()
    title = topic
    return {"title": title, "script": script_text}


def generate_tts_elevenlabs(text, voice="alloy"):
    if not ELEVENLABS_API_KEY:
        filename = AUDIO_DIR / f"{uuid.uuid4()}.txt"
        filename.write_text(text, encoding="utf-8")
        return str(filename)
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"
    headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
    body = {"text": text}
    try:
        r = requests.post(url, headers=headers, json=body, timeout=60)
        r.raise_for_status()
        out_path = AUDIO_DIR / f"{uuid.uuid4()}.mp3"
        with open(out_path, "wb") as f:
            f.write(r.content)
        return str(out_path)
    except Exception as e:
        fallback = AUDIO_DIR / f"{uuid.uuid4()}.txt"
        fallback.write_text(text, encoding="utf-8")
        print("ElevenLabs TTS failed, wrote fallback text file:", e)
        return str(fallback)


def generate_video_heygen(script_text, audio_path, avatar_id=None, background_id=None):
    # Attempt to use HeyGen API. If unavailable, create a local placeholder video file.
    if not HEYGEN_API_KEY:
        fake = VIDEOS_DIR / f"{uuid.uuid4()}.mp4"
        fake.write_text("FAKE VIDEO - HEYGEN KEY MISSING", encoding="utf-8")
        return str(fake)
    try:
        url = "https://api.heygen.com/v1/videos"
        headers = {"Authorization": f"Bearer {HEYGEN_API_KEY}"}
        # many HeyGen endpoints accept multipart/form-data with an audio file and JSON params
        files = {}
        data = {"script": script_text}
        if audio_path and Path(audio_path).exists():
            files["audio_file"] = open(audio_path, "rb")
        if avatar_id:
            data["avatar_id"] = avatar_id
        if background_id:
            data["background_id"] = background_id
        r = requests.post(url, headers=headers, data=data, files=files, timeout=120)
        # close any opened file objects
        for v in files.values():
            try:
                v.close()
            except Exception:
                pass
        r.raise_for_status()
        res = r.json()
        # HeyGen may return a job id or a direct video url
        if isinstance(res, dict) and res.get("video_url"):
            return res.get("video_url")
        if isinstance(res, dict) and res.get("job_id"):
            job_id = res.get("job_id")
            poll_url = f"https://api.heygen.com/v1/videos/{job_id}"
            for _ in range(30):
                pj = requests.get(poll_url, headers=headers, timeout=30)
                pj.raise_for_status()
                pjres = pj.json()
                status = pjres.get("status")
                if status == "finished" and pjres.get("video_url"):
                    return pjres.get("video_url")
                if status == "failed":
                    break
                time.sleep(2)
        # fallback: return raw response
        return res
    except Exception as e:
        fake = VIDEOS_DIR / f"{uuid.uuid4()}.mp4"
        fake.write_text(f"FAKE VIDEO - HEYGEN FAILED: {e}", encoding="utf-8")
        print("HeyGen request failed, created placeholder video:", e)
        return str(fake)


def update_airtable_record(title, script, audio_url, video_url):
    if not AIRTABLE_API_KEY or not AIRTABLE_BASE_ID:
        # return local record
        return None
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}", "Content-Type": "application/json"}
    body = {"fields": {"Title": title, "Script": script, "AudioURL": audio_url, "VideoURL": video_url, "Status": "Generated", "Posted": False}}
    r = requests.post(url, headers=headers, json=body)
    r.raise_for_status()
    return r.json()


def run_once(topic):
    print(f"Generating for: {topic}")
    s = generate_script_openai(topic)
    title = s["title"]
    script = s["script"]
    audio_path = generate_tts_elevenlabs(script)
    print(f"Saved audio: {audio_path}")
    video_url = generate_video_heygen(script, audio_path)
    print(f"Got video: {video_url}")
    record = {
        "id": str(uuid.uuid4()),
        "title": title,
        "script": script,
        "audio_path": audio_path,
        "video_url": str(video_url),
        "status": "Generated",
        "posted": False,
        "created_at": int(time.time())
    }
    save_record_local(record)
    airtable_res = update_airtable_record(title, script, audio_path, video_url)
    if airtable_res:
        print("Airtable updated")
    return record


def main():
    if len(sys.argv) > 1:
        topics = sys.argv[1:]
    else:
        raw = input("Enter topics (comma separated, or 'quit' to exit): ")
        topics = [t.strip() for t in raw.split(",") if t.strip()]
    
    if not topics:
        print("No topics provided.")
        return
    
    if topics == ["quit"]:
        print("Exiting.")
        return
    
    results = []
    for i, t in enumerate(topics, 1):
        try:
            print(f"\n[{i}/{len(topics)}] Generating video for: {t}")
            r = run_once(t)
            results.append(r)
            print(f"✓ Success: {r['title']}")
        except Exception as e:
            print(f"✗ Failed: {t} - {e}")
            results.append({"title": t, "error": str(e)})
    
    print(f"\nDone. Saved {len(results)} record(s) to: {DATA_FILE}")
    
    # Prompt to repeat if loop mode
    while True:
        again = input("\nGenerate more videos? (yes/no): ").strip().lower()
        if again in ["yes", "y"]:
            raw = input("Enter topics (comma separated, or 'quit' to exit): ")
            new_topics = [t.strip() for t in raw.split(",") if t.strip()]
            if new_topics == ["quit"]:
                break
            for i, t in enumerate(new_topics, 1):
                try:
                    print(f"\nGenerating video for: {t}")
                    r = run_once(t)
                    results.append(r)
                    print(f"✓ Success: {r['title']}")
                except Exception as e:
                    print(f"✗ Failed: {t} - {e}")
        else:
            break
    
    print("Agent finished.")


if __name__ == "__main__":
    main()
