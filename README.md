HeyGen AI Video Automation Agent

Overview
- Generates short-form videos using HeyGen, TTS via ElevenLabs, and updates an Airtable dashboard.

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

Files
- `src/main.py`: main automation script
- `data/videos.json`: local dashboard entries
- `.env.example`: env var template

Next steps
- Add real HeyGen/ElevenLabs/Airtable API credentials
- Optionally enable looping for multiple topics
