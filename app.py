import os
import json
import uuid
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_FILE = BASE_DIR / "data" / "videos.json"


def load_videos():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_videos(videos):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(videos, f, indent=2)


@app.route("/")
def index():
    return render_template("dashboard.html")


@app.route("/api/videos", methods=["GET"])
def get_videos():
    videos = load_videos()
    return jsonify(videos)


@app.route("/api/videos/<video_id>/posted", methods=["PATCH"])
def mark_posted(video_id):
    videos = load_videos()
    for video in videos:
        if video.get("id") == video_id:
            video["posted"] = request.json.get("posted", True)
            save_videos(videos)
            return jsonify({"success": True, "video": video})
    return jsonify({"error": "Video not found"}), 404


@app.route("/api/videos/<video_id>", methods=["DELETE"])
def delete_video(video_id):
    videos = load_videos()
    videos = [v for v in videos if v.get("id") != video_id]
    save_videos(videos)
    return jsonify({"success": True})


@app.route("/api/stats", methods=["GET"])
def get_stats():
    videos = load_videos()
    total = len(videos)
    posted = sum(1 for v in videos if v.get("posted"))
    drafts = sum(1 for v in videos if not v.get("posted") and v.get("status") == "Generated")
    failed = sum(1 for v in videos if v.get("status") == "Failed")
    
    return jsonify({
        "total": total,
        "posted": posted,
        "drafts": drafts,
        "failed": failed,
        "success_rate": round((total - failed) / total * 100, 1) if total > 0 else 0,
    })


@app.route("/api/export", methods=["GET"])
def export_data():
    videos = load_videos()
    return jsonify(videos)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
