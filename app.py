import os
import io
import json
import zipfile
import asyncio
import uuid
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTask, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from downloader import YouTubeChannelDownloader, sanitize_filename

app = FastAPI(title="YouTube Channel Transcript Downloader")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOADS_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)
downloader = YouTubeChannelDownloader(output_base_dir=DOWNLOADS_DIR)

# Active WebSocket connections per job_id
active_connections: Dict[str, List[WebSocket]] = {}
job_statuses: Dict[str, Dict[str, Any]] = {}

class ExtractRequest(BaseModel):
    channel_url: str
    formats: List[str] = ["txt", "json", "srt"]
    languages: List[str] = ["en"]
    limit: Optional[int] = None

async def broadcast_progress(job_id: str, message: dict):
    job_statuses[job_id] = message
    if job_id in active_connections:
        dead_sockets = []
        for ws in active_connections[job_id]:
            try:
                await ws.send_json(message)
            except Exception:
                dead_sockets.append(ws)
        for ws in dead_sockets:
            active_connections[job_id].remove(ws)

def run_extraction_job(job_id: str, request: ExtractRequest, loop: asyncio.AbstractEventLoop):
    def sync_callback(data):
        asyncio.run_coroutine_threadsafe(broadcast_progress(job_id, data), loop)

    try:
        res = downloader.process_channel(
            channel_url=request.channel_url,
            languages=request.languages,
            formats=request.formats,
            limit=request.limit,
            progress_callback=sync_callback
        )
    except Exception as e:
        asyncio.run_coroutine_threadsafe(
            broadcast_progress(job_id, {'type': 'error', 'message': str(e)}), loop
        )

@app.post("/api/extract")
async def start_extraction(request: ExtractRequest):
    if not request.channel_url.strip():
        raise HTTPException(status_code=400, detail="Channel URL is required")

    job_id = str(uuid.uuid4())
    job_statuses[job_id] = {'type': 'status', 'message': 'Initializing extraction job...'}
    
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, run_extraction_job, job_id, request, loop)

    return {"job_id": job_id, "status": "started"}

@app.websocket("/ws/progress/{job_id}")
async def websocket_progress(websocket: WebSocket, job_id: str):
    await websocket.accept()
    if job_id not in active_connections:
        active_connections[job_id] = []
    active_connections[job_id].append(websocket)

    # Send current status if available
    if job_id in job_statuses:
        await websocket.send_json(job_statuses[job_id])

    try:
        while True:
            await websocket.receive_text() # keepalive
    except WebSocketDisconnect:
        if job_id in active_connections and websocket in active_connections[job_id]:
            active_connections[job_id].remove(websocket)

@app.get("/api/downloads")
async def list_downloads():
    channels = []
    if not os.path.exists(DOWNLOADS_DIR):
        return {"channels": []}

    for ch_name in os.listdir(DOWNLOADS_DIR):
        ch_path = os.path.join(DOWNLOADS_DIR, ch_name)
        if os.path.isdir(ch_path):
            transcripts_dir = os.path.join(ch_path, "transcripts")
            metadata_file = os.path.join(ch_path, "metadata", "channel_metadata.json")
            
            transcript_files = []
            if os.path.exists(transcripts_dir):
                transcript_files = sorted(os.listdir(transcripts_dir))

            meta = {}
            if os.path.exists(metadata_file):
                try:
                    with open(metadata_file, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                except Exception:
                    pass

            channels.append({
                "channel_title": meta.get("channel_title", ch_name),
                "folder_name": ch_name,
                "total_transcripts": len([f for f in transcript_files if f.endswith(('.txt', '.srt', '.json'))]),
                "transcript_files": transcript_files,
                "metadata": meta
            })
    return {"channels": channels}

@app.get("/api/download-file")
async def download_file(channel: str, file_type: str, filename: str):
    channel_safe = sanitize_filename(channel)
    subfolder = "transcripts" if file_type == "transcript" else "metadata"
    file_path = os.path.join(DOWNLOADS_DIR, channel_safe, subfolder, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path, filename=filename)

@app.get("/api/export-zip/{channel_name}")
async def export_zip(channel_name: str):
    channel_safe = sanitize_filename(channel_name)
    channel_path = os.path.join(DOWNLOADS_DIR, channel_safe)

    if not os.path.exists(channel_path):
        raise HTTPException(status_code=404, detail="Channel download not found")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for root, _, files in os.walk(channel_path):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, channel_path)
                zip_file.write(abs_path, arcname=rel_path)

    zip_buffer.seek(0)
    headers = {'Content-Disposition': f'attachment; filename="{channel_safe}_transcripts.zip"'}
    return StreamingResponse(zip_buffer, media_type="application/zip", headers=headers)

# Serve Static files for UI
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
