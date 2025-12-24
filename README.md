HeyGen AI Video Automation Agent

Overview
- Generates short-form videos using HeyGen, TTS via ElevenLabs, and updates an Airtable dashboard.
- Supports batch processing and interactive loop mode.

Quick start
1. Copy `.env.example` to `.env` and set your API keys.
2. Create a Python venv and install deps:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

3. Run the agent:

```bash
python src\main.py
```

Or pass topics as arguments:
```bash
python src\main.py "Real Estate Tips" "Marketing Hacks" "AI Trends"
```

Files
- `src/main.py`: main automation script
- `data/videos.json`: local dashboard entries
- `.env.example`: env var template

Configuration

### Required API Keys
- **OpenAI**: `OPENAI_API_KEY` — for script generation (ChatGPT)
- **ElevenLabs**: `ELEVENLABS_API_KEY` — for TTS audio
- **HeyGen**: `HEYGEN_API_KEY` — for avatar video generation
- **Airtable**: `AIRTABLE_API_KEY`, `AIRTABLE_BASE_ID`, `AIRTABLE_TABLE_NAME` — for dashboard updates

### Optional
- `ELEVENLABS_VOICE_ID`: Voice preset (default: "alloy")
- `HEYGEN_AVATAR_ID`: Avatar preset
- `HEYGEN_BACKGROUND_ID`: Background preset

### Fallback Behavior
- If an API key is missing or the API request fails, the agent creates a local fallback file and continues.
- All records are saved to `data/videos.json` regardless of success or failure.

API Endpoints

#### OpenAI (Script Generation)
```
POST https://api.openai.com/v1/chat/completions
```
- Prompt: Generate 15–30 second TikTok script with hook, value, CTA.
- Model: `gpt-4o-mini`

#### ElevenLabs (TTS)
```
POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}
```
- Request body: `{ "text": "..." }`
- Response: MP3 audio file (binary)

#### HeyGen (Video Generation)
```
POST https://api.heygen.com/v1/videos
```
- Multipart form data: `script`, `avatar_id`, `background_id`, `audio_file`
- Response: Job ID or video URL
- Job polling: `GET https://api.heygen.com/v1/videos/{job_id}`

#### Airtable (Dashboard)
```
POST https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}
```
- Request body: `{ "fields": { "Title": "...", "Script": "...", "AudioURL": "...", "VideoURL": "...", "Status": "Generated", "Posted": false } }`

Workflow

1. **User Input**: Enter topics (comma-separated or via CLI args).
2. **Script Generation**: ChatGPT creates a short TikTok-style script.
3. **TTS**: ElevenLabs converts script to audio.
4. **Video Generation**: HeyGen overlays avatar on background with audio.
5. **Dashboard Update**: Record is saved locally to `data/videos.json` and optionally to Airtable.
6. **Repeat Mode**: Agent offers to generate more videos or exit.

Local Record Format
```json
{
  "id": "uuid",
  "title": "script title",
  "script": "full script text",
  "audio_path": "/path/to/audio.mp3",
  "video_url": "heygen video url or local path",
  "status": "Generated",
  "posted": false,
  "created_at": 1703369600
}
```

Dashboard

### Option 1: Static HTML Dashboard (No Backend)
Open `dashboard.html` in your browser directly:
- Double-click the file or right-click → Open with Browser
- Shows all videos with search, filter, and stats
- Auto-refreshes every 30 seconds

### Option 2: Flask Web Dashboard (Interactive + API)
```bash
pip install Flask
python app.py
```
Then visit: http://localhost:5000

**Features:**
- 📊 Real-time analytics and charts
- ✏️ Mark videos as posted
- ⬇️ Export data
- 🔄 Auto-refresh
- 📱 Responsive mobile design

### Dashboard API Endpoints
- `GET /api/videos` — List all videos
- `GET /api/stats` — Get dashboard stats
- `PATCH /api/videos/<id>/posted` — Mark as posted
- `DELETE /api/videos/<id>` — Delete video
- `GET /api/export` — Export all data
