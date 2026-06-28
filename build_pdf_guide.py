import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

def build_pdf(filename="Python_Beginners_Guide_ScriptVault.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette
    PRIMARY_COLOR = colors.HexColor("#4F46E5") # Indigo
    SECONDARY_COLOR = colors.HexColor("#06B6D4") # Cyan
    TEXT_DARK = colors.HexColor("#1F2937") # Charcoal
    BG_LIGHT = colors.HexColor("#F9FAFB")
    BORDER_COLOR = colors.HexColor("#E5E7EB")

    # Custom Typography Styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=26,
        leading=32,
        textColor=PRIMARY_COLOR,
        alignment=TA_CENTER,
        spaceAfter=15
    )

    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=14,
        leading=18,
        textColor=TEXT_DARK,
        alignment=TA_CENTER,
        spaceAfter=30
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=PRIMARY_COLOR,
        spaceBefore=20,
        spaceAfter=10,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=SECONDARY_COLOR,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=TEXT_DARK,
        spaceAfter=8,
        alignment=TA_JUSTIFY
    )

    code_style = ParagraphStyle(
        'Code_Custom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#111827"),
        backColor=colors.HexColor("#F3F4F6"),
        borderColor=colors.HexColor("#E5E7EB"),
        borderWidth=1,
        borderPadding=6,
        spaceBefore=6,
        spaceAfter=8,
        keepWithNext=True
    )

    callout_style = ParagraphStyle(
        'Callout_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#374151"),
        backColor=colors.HexColor("#EEF2FF"),
        borderColor=PRIMARY_COLOR,
        borderWidth=1,
        borderPadding=8,
        spaceBefore=8,
        spaceAfter=10
    )

    story = []

    # --- COVER / HEADER SECTION ---
    story.append(Spacer(1, 40))
    story.append(Paragraph("Zero to Hero: Python Architecture Guide", title_style))
    story.append(Paragraph("Building a High-Performance YouTube Transcript & Metadata Extractor<br/><font size=10 color='#6B7280'>A Complete Technical Deep-Dive for Python Beginners</font>", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY_COLOR, spaceAfter=20))
    
    # Author & Overview Metadata Table
    meta_data = [
        [Paragraph("<b>Target Audience:</b> Python Beginners & Intermediates", body_style), Paragraph("<b>Prerequisites:</b> Basic Python Syntax", body_style)],
        [Paragraph("<b>Goal:</b> Replicate this project independently without AI tools", body_style), Paragraph("<b>Tech Stack:</b> Python, FastAPI, WebSockets", body_style)]
    ]
    t = Table(meta_data, colWidths=[3.5*inch, 3.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
        ('PADDING', (0,0), (-1,-1), 8),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
    ]))
    story.append(t)
    story.append(Spacer(1, 25))

    # --- SECTION 1 ---
    story.append(Paragraph("1. Deconstructing the Problem: The Mindset of a Developer", h1_style))
    story.append(Paragraph(
        "When beginners see a complete web application with real-time updates and multiple export formats, they often feel overwhelmed. The key to building complex software independently without relying on AI assistance is <b>Decomposition</b>—breaking a large problem down into small, isolated, solvable components.",
        body_style
    ))
    story.append(Paragraph(
        "For this project, we break the requirements down into four clear layers:",
        body_style
    ))
    story.append(Paragraph("<b>1. Data Fetching Layer:</b> Interacting with YouTube to get video IDs and captions without downloading video files.", body_style))
    story.append(Paragraph("<b>2. Data Transformation & File I/O:</b> Converting raw caption timestamps into human-readable text (.txt), SRT subtitle files (.srt), and structured data (.json).", body_style))
    story.append(Paragraph("<b>3. API & Async Server Layer (FastAPI):</b> Exposing endpoints and WebSocket channels so a browser can talk to Python.", body_style))
    story.append(Paragraph("<b>4. Frontend UI Layer:</b> Creating an intuitive dashboard with HTML, CSS, and JavaScript.", body_style))

    story.append(Paragraph("💡 Key Takeaway: Never write UI code until your underlying Python logic runs perfectly in isolation inside a script.", callout_style))

    # --- SECTION 2 ---
    story.append(Paragraph("2. Core Python Concepts Demystified", h1_style))
    story.append(Paragraph(
        "Before diving into the code, you must master the fundamental Python building blocks used throughout this application:",
        body_style
    ))
    
    story.append(Paragraph("A. Dictionary & Object Defensive Access", h2_style))
    story.append(Paragraph(
        "External libraries like <code>youtube_transcript_api</code> update frequently. In version 1.2+, caption snippets are returned as objects (<code>FetchedTranscriptSnippet</code>) rather than dictionaries. Using direct dictionary indexing <code>item['text']</code> causes a runtime <code>TypeError: 'FetchedTranscriptSnippet' object is not subscriptable</code>.",
        body_style
    ))
    story.append(Paragraph("<b>Defensive Coding Pattern:</b> Always verify data types or use built-in functions like <code>getattr()</code> and <code>isinstance()</code>:", body_style))
    story.append(Paragraph(
"if isinstance(item, dict):\n"
"    text = item.get('text', '')\n"
"else:\n"
"    text = getattr(item, 'text', '')", code_style))

    story.append(Paragraph("B. Object-Oriented Programming (OOP) Encapsulation", h2_style))
    story.append(Paragraph(
        "We wrap our core downloading logic inside a class <code>YouTubeChannelDownloader</code>. Classes allow us to store persistent state (such as the <code>output_base_dir</code>) and reuse utility helper methods cleanly across both command-line and web API environments.",
        body_style
    ))

    # --- SECTION 3 ---
    story.append(Paragraph("3. Deep Dive: The Extraction Engine (downloader.py)", h1_style))
    story.append(Paragraph(
        "Let's examine how <code>yt-dlp</code> and <code>youtube-transcript-api</code> work together to achieve ultra-fast downloads without media streaming:",
        body_style
    ))
    story.append(Paragraph(
"ydl_opts = {\n"
"    'extract_flat': 'in_playlist',\n"
"    'skip_download': True,\n"
"    'quiet': True\n"
"}\n"
"with yt_dlp.YoutubeDL(ydl_opts) as ydl:\n"
"    info = ydl.extract_info(channel_url, download=False)", code_style))
    story.append(Paragraph(
        "Setting <code>extract_flat: 'in_playlist'</code> tells YouTube's server to only return video metadata headers (ID, title, view count) without resolving video media streams. This makes extraction nearly instantaneous.",
        body_style
    ))

    story.append(Paragraph("Caption Fallback Hierarchy Strategy", h2_style))
    story.append(Paragraph(
        "When fetching transcripts, videos might have manually uploaded captions, auto-generated captions, or captions in foreign languages. Our engine implements a 4-tier fallback strategy:",
        body_style
    ))
    story.append(Paragraph("1. Attempt to fetch <b>manually created transcripts</b> in requested languages (e.g., <code>en</code>).", body_style))
    story.append(Paragraph("2. If manual captions do not exist, attempt to fetch <b>auto-generated transcripts</b>.", body_style))
    story.append(Paragraph("3. If still not found, fetch <i>any</i> available transcript language and attempt to <b>auto-translate</b> it into your primary language.", body_style))
    story.append(Paragraph("4. If all fail, catch the exception cleanly and record the video as unavailable without crashing the batch process.", body_style))

    # --- SECTION 4 ---
    story.append(Paragraph("4. Real-Time Web Communications (FastAPI & WebSockets)", h1_style))
    story.append(Paragraph(
        "Standard HTTP requests follow a Request-Response model: the browser asks, and the server answers. But long-running jobs (like processing 100 YouTube videos) need continuous progress updates. That is where <b>WebSockets</b> come in.",
        body_style
    ))
    story.append(Paragraph(
        "WebSockets open a persistent, two-way communication channel. In <code>app.py</code>, we run the extraction job in a background thread and broadcast progress JSON events directly to the browser:",
        body_style
    ))
    story.append(Paragraph(
"@app.websocket('/ws/progress/{job_id}')\n"
"async def websocket_progress(websocket: WebSocket, job_id: str):\n"
"    await websocket.accept()\n"
"    # Active connection streams real-time logs to UI", code_style))

    # --- SECTION 5 ---
    story.append(Paragraph("5. Step-by-Step Exercises to Build This Without AI", h1_style))
    story.append(Paragraph(
        "To ensure you can replicate this project independently, complete these structured exercises in order on your local machine:",
        body_style
    ))
    story.append(Paragraph("<b>Exercise 1 (Basic Scripting):</b> Write a 20-line script that takes a single YouTube video ID, fetches its transcript using <code>youtube_transcript_api</code>, and prints it formatted with minutes and seconds.", body_style))
    story.append(Paragraph("<b>Exercise 2 (File Management):</b> Extend your script to save the transcript into a folder named after the video ID, generating both a <code>.txt</code> file and a formatted <code>.srt</code> subtitle file.", body_style))
    story.append(Paragraph("<b>Exercise 3 (Channel Handling):</b> Integrate <code>yt-dlp</code> flat extraction to loop through a list of 5 videos from a channel handle, printing a live progress counter `[1/5]`.", body_style))
    story.append(Paragraph("<b>Exercise 4 (Web API):</b> Wrap your script inside a FastAPI endpoint using Uvicorn so entering `http://localhost:8000/api/extract` triggers the download.", body_style))

    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=1, color=BORDER_COLOR, spaceAfter=15))
    story.append(Paragraph("<font color='#9CA3AF' size=8>ScriptVault Architecture Guide • Created for Python Learners • Built with Python & ReportLab</font>", ParagraphStyle('Footer', parent=styles['Normal'], alignment=TA_CENTER)))

    doc.build(story)
    print(f"PDF guide created successfully: {filename}")

if __name__ == "__main__":
    build_pdf()
