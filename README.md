#  ScriptVault: YouTube Channel Transcript & Metadata Extractor (make an issue if the name is trash)

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)

**ScriptVault** is a high-performance, lightweight Python web and CLI application engineered to extract **ONLY transcripts (captions/subtitles) and metadata** from any YouTube channel, playlist, or batch of videos. 

By eliminating audio and video media downloads entirely, ScriptVault processes entire channels with thousands of videos in minutes, consuming minimal network bandwidth and disk storage.

The primary purpose was a tool to aid the training of AI models off a YouTuber's catalogue.

---

##  Features

-  **Zero Media Streaming**: Downloads strictly captions and structured metadata. No heavy MP4/MP3 downloads.
-  **Manual & Auto-Generated Captions**: Automatically fetches manually created subtitles, seamlessly falling back to YouTube's auto-generated speech recognition captions.
-  **Multi-Language & Translation Support**: Configurable language preferences (e.g., `en, es, fr, de`) with automatic translation fallbacks.
-  **Modern Glassmorphism Web UI**: Features a dark-mode web dashboard built with vanilla CSS, live real-time progress bars, metric counters, and logging via WebSockets. (pls don't use this)
-  **Multiple Output Formats**: Export transcripts as Plain Text (`.txt`), Subtitles (`.srt`), or Structured Data (`.json`).
-  **Aggregated Channel Metadata**: Automatically compiles video titles, durations, view counts, upload dates, and caption availability into `channel_metadata.json` and `videos_summary.csv`.
-  **One-Click ZIP Export**: Package entire channel transcript libraries directly from the browser into downloadable `.zip` archives.
-  **CLI Automation**: Includes a powerful command-line script for background jobs, servers, or automated scripting.

---

##  Installation & Setup

### Prerequisites
- Python 3.10 or higher
- Git

### Quickstart

1. **Clone the Repository**
   ```bash
   git clone https://github.com/LordAlex-2-me/yt-channel-transcript-downloader.git
   cd yt-channel-transcript-downloader
   ```

2. **Create a Virtual Environment (tbh you really don't need to do this)**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

---

##  Usage

###  Method 1: (NOT Recommended) Web Dashboard 

Start the local web application server:
```bash
python app.py
```
Open **`http://localhost:8000`** in your web browser.

1. Paste any YouTube Channel URL (e.g., `https://www.youtube.com/@Veritasium`) or handle (`@Veritasium`).
2. Select your export formats (`.txt`, `.srt`, `.json`) and preferred languages.
3. Click **Extract Transcripts & Metadata** to watch real-time extraction metrics.
4. Navigate to the **Downloads Vault** tab to preview transcripts in-browser or download full ZIP packages.

---

###  Method 2: much better ---> Command-Line Interface (CLI) 

Run batch downloads directly from your terminal:

```bash
# Basic extraction for a channel handle
python cli.py --channel "@mkbhd"

# Extract with video limits, specific formats, and custom output path
python cli.py --channel "https://www.youtube.com/@odysseas_" --limit 20 --formats txt srt json --lang en es --output my_downloads
```

#### CLI Arguments:
| Argument | Short | Description | Default |
| :--- | :--- | :--- | :--- |
| `--channel` | `-c` | YouTube channel URL, handle (`@name`), or playlist URL (**Required**) | *None* |
| `--limit` | `-l` | Maximum number of videos to process | *All videos* |
| `--formats` | `-f` | Formats to save (`txt`, `srt`, `json`) | `txt json srt` |
| `--lang` | | Preferred language code hierarchy | `en` |
| `--output` | `-o` | Target base output directory | `downloads` |

---

##  Output Folder Structure

Extracted data is automatically organized into clean channel-specific subfolders:

```
downloads/
└── Odysseas/
    ├── transcripts/
    │   ├── something_something_rennaisance_man.txt
    │   ├── something_something_rennaisance_man.srt
    │   └── something_something_rennaisance_man.json
    └── metadata/
        ├── channel_metadata.json
        └── videos_summary.csv
```

---

##  Architecture & Technology Stack

- **Core Engine**: Python (`yt-dlp` flat-playlist extraction + `youtube-transcript-api` caption retrieval).
- **Backend Server**: FastAPI, Uvicorn, WebSockets.
- **Frontend UI**: Vanilla HTML5, CSS3 Glassmorphism design system, JavaScript (ES6+).

---

##  License
son...
Distributed under the MIT License. See `LICENSE` for more information.
lmao
#
