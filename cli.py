import argparse
import sys
from downloader import YouTubeChannelDownloader

def main():
    parser = argparse.ArgumentParser(description="Download YouTube channel transcripts and metadata without media downloading.")
    parser.add_argument("--channel", "-c", required=True, help="YouTube Channel URL, handle (e.g. @channel), or playlist URL")
    parser.add_argument("--limit", "-l", type=int, default=None, help="Limit number of videos to process")
    parser.add_argument("--formats", "-f", nargs="+", default=["txt", "json", "srt"], choices=["txt", "json", "srt"], help="Formats to save transcripts")
    parser.add_argument("--lang", nargs="+", default=["en"], help="Preferred language codes (e.g., en es fr)")
    parser.add_argument("--output", "-o", default="downloads", help="Output directory path")

    args = parser.parse_args()

    downloader = YouTubeChannelDownloader(output_base_dir=args.output)
    
    print(f"\n🚀 Starting transcript extraction for: {args.channel}")
    print(f"📁 Saving to directory: {args.output}")
    print(f"📝 Formats requested: {', '.join(args.formats)}\n")

    def progress(data):
        t_type = data.get('type')
        if t_type == 'status':
            print(f"ℹ️  {data.get('message')}")
        elif t_type == 'progress':
            curr = data.get('current')
            tot = data.get('total')
            pct = data.get('percentage')
            title = data.get('video_title')
            print(f"[{curr}/{tot} - {pct}%] Processing: {title[:60]}...")
        elif t_type == 'complete':
            res = data.get('result')
            print("\n✅ Extraction Finished!")
            print(f"Channel: {res.get('channel_title')}")
            print(f"Transcripts Downloaded: {res.get('success')}/{res.get('total')}")
            print(f"Unavailable/No Captions: {res.get('unavailable')}")
            print(f"Saved in: {res.get('folder_path')}\n")

    try:
        downloader.process_channel(
            channel_url=args.channel,
            languages=args.lang,
            formats=args.formats,
            limit=args.limit,
            progress_callback=progress
        )
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
