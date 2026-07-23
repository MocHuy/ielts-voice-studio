# IELTS Voice Studio

A private, local-first web app for turning ChatGPT IELTS corrections into focused listening, shadowing, dictation, and pronunciation practice. Lesson text, notes, progress, and difficulty ratings stay in a SQLite database on your computer.

## Features

- Parses Original, Corrected/Better, Explanation, Example, and Question sections into cards.
- Natural British and American downloadable voices through Microsoft Edge's online TTS service.
- Browser Web Speech fallback when Edge TTS or the internet is unavailable.
- Play, pause, resume, stop, previous/next, repeat, auto-repeat, presets, speed, pitch, volume, and configurable pauses.
- Sentence highlighting, progress, keyboard shortcuts, and responsive light/dark UI.
- Original/corrected comparison with changed-word highlighting.
- Shadowing presets, phrase-based slow pronunciation practice, and easy/medium/difficult ratings.
- Dictation answers with word-level feedback and a simple accuracy percentage.
- Local lesson save/open/rename (edit the title and save), search, delete, notes, difficult filter, and resume position.
- Sentence, corrected-only, or full-lesson MP3/WAV export.

The dictation score compares written words; it is not pronunciation assessment. The app does not claim to analyse pronunciation because it does not record or analyse speech.

## Requirements

- Windows 10 or 11
- Python 3.10–3.14 (3.12 or newer recommended)
- Internet access for Edge natural voices. Browser voices can work offline if installed in Windows.
- Optional: [ffmpeg](https://ffmpeg.org/) on `PATH` for exact silence between clips and WAV export. Without it, combined text is generated as one MP3.

FastAPI 0.139.2 and Uvicorn 0.51.0 support Python 3.10+, including 3.14. Edge TTS 7.2.8 supports Python 3.7+ and was current when this project was created in July 2026.

## Easiest Windows installation

Double-click `run.bat`. On the first run it creates `.venv`, installs packages, opens the browser, and starts the server. Leave the terminal window open while using the app. Press `Ctrl+C` to stop it.

## Manual installation

Open PowerShell in this folder and copy/paste:

```powershell
py -3 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000>. The app binds only to your computer (`127.0.0.1`).

## Using the app

1. Paste feedback, or click **Load example**.
2. Click **Process text** and choose a reading mode.
3. Select British/American, voice, speed, and a practice preset.
4. Play a card or the queue. Use Compare, Dictation, or Pronunciation tabs as needed.
5. Add notes and click **Save lesson**. To rename it, change the title and save again.
6. Export a sentence from its card, or use **Export audio** for corrected/full content.

Shortcuts (disabled while typing): Space play/pause, Escape stop, arrows previous/next, R repeat, S save.

## Voice troubleshooting

- `Edge natural voices` means downloadable TTS is ready. Edge TTS is free and account-free but is an unofficial client for Microsoft's online service, so availability can change.
- If the badge says `Browser voice fallback`, check the internet/firewall and restart the app. Playback will use voices installed in the browser/Windows, but browser speech cannot be downloaded by this app.
- On Windows, install additional English speech voices in **Settings → Time & language → Speech**. Restart the browser afterward.
- If downloads fail while browser playback works, Edge TTS is unavailable. Try later or update it with `python -m pip install --upgrade edge-tts`.

## Audio export and ffmpeg

Install ffmpeg with Windows Package Manager if you want WAV and exact inter-sentence silence:

```powershell
winget install Gyan.FFmpeg
```

Restart PowerShell and the app. MP3 output from Edge TTS is supported without ffmpeg.

## Project structure

```text
app.py                      FastAPI routes and validation
services/text_parser.py     Markdown cleanup and section parsing
services/tts_service.py     Swappable TTS provider interface
services/audio_service.py   Audio settings and safe filenames
services/lesson_service.py  SQLite persistence
templates/index.html        App shell
static/css/app.css          Responsive design
static/js/app.js            Player and practice modes
storage/lessons.db          Local data (created on first run)
generated_audio/            Temporary generated audio
tests/                      Parser, storage, filename, and API tests
```

## Switching TTS engines

`services/tts_service.py` defines the small `TTSProvider` protocol. Add a class implementing `voices()` and `generate()`, then replace `tts = EdgeTTSProvider()` in `app.py`. Keep the same English voice metadata shape. The frontend automatically falls back to the Web Speech API after a server TTS error.

## Tests

```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest -q
```

Tests cover sentence splitting, headings, Markdown, empty/long/special input, safe filenames, lesson CRUD, and API parsing.

## Packaging later

The simplest desktop package is PyInstaller plus a small launcher/webview. Start with:

```powershell
python -m pip install pyinstaller
pyinstaller --onedir --name IELTSVoiceStudio --add-data "templates;templates" --add-data "static;static" app.py
```

Because this app expects Uvicorn to launch the ASGI server, a production executable should add a dedicated launcher that starts Uvicorn and opens the browser. Keep SQLite beside the executable in a user-writable data directory. The current local web version is easier to update and debug.

## Privacy

Lesson data is never uploaded by the application. Text sent for Edge speech generation is necessarily transmitted to Microsoft's TTS service. Choose browser fallback and an installed offline system voice when content must never leave the laptop.
# ielts-voice-studio
