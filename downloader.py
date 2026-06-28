import os
import re
import json
import csv
import logging
from typing import List, Dict, Any, Optional, Callable
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("yt_downloader")

def sanitize_filename(name: str) -> str:
    """Sanitize string to be safe for filenames."""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def format_timestamp(seconds: float) -> str:
    """Format seconds to SRT timestamp format (HH:MM:SS,mmm)."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

def convert_to_srt(transcript: List[Any]) -> str:
    """Convert transcript items to SRT string."""
    srt_lines = []
    for idx, item in enumerate(transcript, 1):
        if isinstance(item, dict):
            start = item.get('start', 0.0)
            duration = item.get('duration', 0.0)
            text = str(item.get('text', '')).replace('\n', ' ')
        else:
            start = getattr(item, 'start', 0.0)
            duration = getattr(item, 'duration', 0.0)
            text = str(getattr(item, 'text', '')).replace('\n', ' ')
            
        end = start + duration
        srt_lines.append(f"{idx}\n{format_timestamp(start)} --> {format_timestamp(end)}\n{text}\n")
    return "\n".join(srt_lines)

def convert_to_txt(transcript: List[Any], include_timestamps: bool = True) -> str:
    """Convert transcript to readable plain text."""
    lines = []
    for item in transcript:
        if isinstance(item, dict):
            start = item.get('start', 0.0)
            text = str(item.get('text', ''))
        else:
            start = getattr(item, 'start', 0.0)
            text = str(getattr(item, 'text', ''))

        if include_timestamps:
            mins = int(start // 60)
            secs = int(start % 60)
            lines.append(f"[{mins:02d}:{secs:02d}] {text}")
        else:
            lines.append(text)
    return "\n".join(lines)

class YouTubeChannelDownloader:
    def __init__(self, output_base_dir: str = "downloads"):
        self.output_base_dir = output_base_dir
        os.makedirs(self.output_base_dir, exist_ok=True)

    def get_channel_videos(self, channel_url: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """Fetch list of video items and channel info without downloading media."""
        # Clean URL format
        url = channel_url.strip()
        if url.startswith("@"):
            url = f"https://www.youtube.com/{url}"
        elif not url.startswith("http"):
            url = f"https://www.youtube.com/@{url}"
            
        if not ("/videos" in url or "/playlists" in url or "watch?v=" in url or "/playlist?" in url):
            url = url.rstrip("/") + "/videos"

        ydl_opts = {
            'extract_flat': 'in_playlist',
            'skip_download': True,
            'quiet': True,
            'ignoreerrors': True,
            'playlistend': limit if limit and limit > 0 else None,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                raise ValueError("Failed to extract channel information. Please verify the URL.")

            channel_title = info.get('channel') or info.get('uploader') or info.get('title') or "Unknown_Channel"
            entries = info.get('entries', [])
            
            # Filter valid entries
            videos = []
            for entry in entries:
                if not entry:
                    continue
                video_id = entry.get('id')
                title = entry.get('title')
                if video_id and title:
                    videos.append({
                        'id': video_id,
                        'title': title,
                        'url': f"https://www.youtube.com/watch?v={video_id}",
                        'duration': entry.get('duration'),
                        'view_count': entry.get('view_count'),
                        'uploader': entry.get('uploader'),
                    })
                    
            return {
                'channel_title': channel_title,
                'channel_id': info.get('channel_id') or info.get('id'),
                'videos': videos
            }

    def fetch_transcript(self, video_id: str, languages: List[str] = None) -> Dict[str, Any]:
        """Fetch transcript for a video, supporting both manual and auto-generated captions."""
        if not languages:
            languages = ['en']

        try:
            api = YouTubeTranscriptApi()
            # Support both instance and class level calls for library compatibility
            if hasattr(api, 'list'):
                transcript_list = api.list(video_id)
            elif hasattr(YouTubeTranscriptApi, 'list_transcripts'):
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            else:
                raise RuntimeError("Unsupported YouTubeTranscriptApi interface")

            transcript = None
            # 1. Try finding manually created transcript in requested languages
            try:
                transcript = transcript_list.find_manually_created_transcript(languages)
            except Exception:
                pass

            # 2. Try finding auto-generated transcript in requested languages
            if not transcript:
                try:
                    transcript = transcript_list.find_generated_transcript(languages)
                except Exception:
                    pass

            # 3. Fallback to general find_transcript
            if not transcript:
                try:
                    transcript = transcript_list.find_transcript(languages)
                except Exception:
                    pass

            # 4. Fallback to any transcript available (and translate to primary language if possible)
            if not transcript:
                available = list(transcript_list)
                if available:
                    transcript = available[0]
                    if languages and hasattr(transcript, 'is_translatable') and transcript.is_translatable:
                        try:
                            transcript = transcript.translate(languages[0])
                        except Exception:
                            pass
                else:
                    raise NoTranscriptFound(video_id, languages, transcript_list)

            raw_data = transcript.fetch()
            fetched_data = []
            for item in raw_data:
                if isinstance(item, dict):
                    fetched_data.append(item)
                else:
                    fetched_data.append({
                        'text': getattr(item, 'text', ''),
                        'start': getattr(item, 'start', 0.0),
                        'duration': getattr(item, 'duration', 0.0)
                    })

            return {
                'status': 'success',
                'language': getattr(transcript, 'language', 'Unknown'),
                'language_code': getattr(transcript, 'language_code', 'en'),
                'is_generated': getattr(transcript, 'is_generated', False),
                'transcript': fetched_data
            }
        except (TranscriptsDisabled, NoTranscriptFound) as e:
            return {'status': 'unavailable', 'error': str(e)}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def process_channel(
        self, 
        channel_url: str, 
        languages: List[str] = None, 
        formats: List[str] = None,
        limit: Optional[int] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """Main pipeline to process channel and save transcripts & metadata."""
        if not formats:
            formats = ['txt', 'json', 'srt']
        if not languages:
            languages = ['en']

        if progress_callback:
            progress_callback({'type': 'status', 'message': 'Extracting channel video list...'})

        channel_data = self.get_channel_videos(channel_url, limit=limit)
        channel_title = sanitize_filename(channel_data['channel_title'])
        videos = channel_data['videos']

        # Setup directory structure
        channel_dir = os.path.join(self.output_base_dir, channel_title)
        transcripts_dir = os.path.join(channel_dir, "transcripts")
        metadata_dir = os.path.join(channel_dir, "metadata")
        os.makedirs(transcripts_dir, exist_ok=True)
        os.makedirs(metadata_dir, exist_ok=True)

        total_videos = len(videos)
        processed_summary = []
        successful_count = 0
        unavailable_count = 0

        for idx, vid in enumerate(videos, 1):
            vid_id = vid['id']
            vid_title = vid['title']
            safe_title = sanitize_filename(vid_title)
            filename_base = f"{idx:03d}_{safe_title}_{vid_id}"

            if progress_callback:
                progress_callback({
                    'type': 'progress',
                    'current': idx,
                    'total': total_videos,
                    'percentage': round((idx / total_videos) * 100, 1),
                    'video_title': vid_title,
                    'video_id': vid_id
                })

            result = self.fetch_transcript(vid_id, languages)
            status = result['status']

            summary_item = {
                'index': idx,
                'video_id': vid_id,
                'title': vid_title,
                'url': vid['url'],
                'duration': vid.get('duration'),
                'view_count': vid.get('view_count'),
                'transcript_status': status,
                'transcript_language': result.get('language_code', ''),
                'is_auto_generated': result.get('is_generated', False)
            }
            processed_summary.append(summary_item)

            if status == 'success':
                successful_count += 1
                raw_transcript = result['transcript']
                
                # Save requested formats
                if 'txt' in formats:
                    txt_content = convert_to_txt(raw_transcript)
                    with open(os.path.join(transcripts_dir, f"{filename_base}.txt"), 'w', encoding='utf-8') as f:
                        f.write(f"Title: {vid_title}\nURL: {vid['url']}\nLanguage: {result.get('language')}\n\n" + txt_content)

                if 'srt' in formats:
                    srt_content = convert_to_srt(raw_transcript)
                    with open(os.path.join(transcripts_dir, f"{filename_base}.srt"), 'w', encoding='utf-8') as f:
                        f.write(srt_content)

                if 'json' in formats:
                    json_data = {
                        'metadata': vid,
                        'transcript_info': {
                            'language': result.get('language'),
                            'language_code': result.get('language_code'),
                            'is_generated': result.get('is_generated')
                        },
                        'transcript': raw_transcript
                    }
                    with open(os.path.join(transcripts_dir, f"{filename_base}.json"), 'w', encoding='utf-8') as f:
                        json.dump(json_data, f, indent=2, ensure_ascii=False)
            else:
                unavailable_count += 1

        # Save Metadata Files
        # CSV Summary
        csv_path = os.path.join(metadata_dir, "videos_summary.csv")
        fieldnames = ['index', 'video_id', 'title', 'url', 'duration', 'view_count', 'transcript_status', 'transcript_language', 'is_auto_generated']
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(processed_summary)

        # JSON Summary
        json_summary_path = os.path.join(metadata_dir, "channel_metadata.json")
        with open(json_summary_path, 'w', encoding='utf-8') as f:
            json.dump({
                'channel_title': channel_data['channel_title'],
                'channel_id': channel_data['channel_id'],
                'total_videos': total_videos,
                'transcripts_retrieved': successful_count,
                'transcripts_unavailable': unavailable_count,
                'videos': processed_summary
            }, f, indent=2, ensure_ascii=False)

        completion_info = {
            'channel_title': channel_data['channel_title'],
            'folder_path': channel_dir,
            'total': total_videos,
            'success': successful_count,
            'unavailable': unavailable_count
        }

        if progress_callback:
            progress_callback({'type': 'complete', 'result': completion_info})

        return completion_info
