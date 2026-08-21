"""
Telegram Research Paper Analyser
Listens for commands on Telegram, analyzes papers using Gemini,
and appends summaries to a Google Doc via Google Apps Script.
"""

import sys
import os
import re
import asyncio
import threading
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

# Ensure stdout is unbuffered so print logs appear immediately in Render / Docker logs
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from parsers import ParserFactory

# Load configurations
load_dotenv()

# Telegram API credentials
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
PHONE_NUMBER = os.getenv("PHONE_NUMBER")
TELEGRAM_SESSION_STRING = os.getenv("TELEGRAM_SESSION_STRING", "").strip()

# Gemini API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Google Apps Script Web App URL
APPS_SCRIPT_URL = os.getenv("APPS_SCRIPT_URL")

# Trigger Commands
TRIGGERS = ["/analyze", "/analyse"]

# Validate basic configuration
if not API_ID or not API_HASH:
    print("❌ Missing Telegram credentials (API_ID, API_HASH) in .env!")
    exit(1)

if not GEMINI_API_KEY:
    print("⚠️  GEMINI_API_KEY is not set. Gemini features will fail unless set.")

if not APPS_SCRIPT_URL:
    print(
        "⚠️  APPS_SCRIPT_URL is not set. Exporting to Google Docs will fail unless set."
    )

# Initialize Client: Use StringSession (for Render/Cloud) or local 'session' file
session_handler = (
    StringSession(TELEGRAM_SESSION_STRING)
    if TELEGRAM_SESSION_STRING
    else "session"
)
client = TelegramClient(session_handler, API_ID, API_HASH)

# Initialize Gemini Client if key exists
gemini_client = None
if GEMINI_API_KEY:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)


# 1. Define the Pydantic schema for structured Gemini output
class AnalysisResult(BaseModel):
    title: str = Field(
        description="The formal title of the research paper (extracted or inferred)."
    )
    studentSummary: list[str] = Field(
        description="List of 4 to 5 concise bullet points for students in simple English. Each item in the list is a single bullet point string."
    )
    facultySummary: list[str] = Field(
        description="List of 4 to 5 concise bullet points for PhD-pursuing faculty covering methodology, literature gaps, and thesis directions. Each item in the list is a single bullet point string."
    )
    phdSummary: list[str] = Field(
        description="List of 4 to 5 concise bullet points for PhD holders covering technical novelty, algorithmic/mathematical rigor, and limitations. Each item in the list is a single bullet point string."
    )
    productSummary: list[str] = Field(
        description="List of 4 to 5 concise bullet points for product managers covering commercial applications, target market, MVP, and business value. Each item in the list is a single bullet point string."
    )


def run_gemini_analysis(text: str) -> AnalysisResult:
    """Synchronous helper to run Gemini analysis and return the parsed result."""
    if not gemini_client:
        raise ValueError(
            "Gemini client is not initialized. Please set GEMINI_API_KEY in .env."
        )

    prompt = (
        "Analyze the following research paper and generate structured, concise bullet points for four distinct audiences.\n\n"
        "STRICT REQUIREMENTS:\n"
        "- Return a JSON object where each category is a LIST of 4 to 5 concise bullet point strings.\n"
        "- Each bullet point MUST be a single, punchy sentence (15-25 words max).\n"
        "- Do NOT write long paragraphs.\n"
        "- You may use **bold** keywords for key concepts.\n\n"
        f"Research Paper:\n{text}"
    )

    response = gemini_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=(
                "You are an expert research analyst. You summarize complex research papers into clear, punchy bullet points. "
                "For every category, provide an array/list of 4-5 concise bullet point strings. Never generate paragraphs."
            ),
            response_mime_type="application/json",
            response_schema=AnalysisResult,
            temperature=0.1,
        ),
    )

    # Return the parsed Pydantic object
    return response.parsed


def post_to_google_doc(payload: dict) -> dict:
    """Synchronous helper to post the analysis to the Google Apps Script Web App."""
    if not APPS_SCRIPT_URL:
        raise ValueError(
            "Apps Script Web App URL is not configured. Please set APPS_SCRIPT_URL in .env."
        )
    
    response = requests.post(APPS_SCRIPT_URL, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def extract_pdf_url(text: str) -> str:
    """Extract a PDF URL from text, supporting various patterns including • PDF: <url>."""
    if not text:
        return ""

    # Check specifically for "PDF:" or "• PDF:" prefix followed by URL
    match_bullet = re.search(
        r"(?:PDF:\s*|• PDF:\s*)(https?://\S+)", text, re.IGNORECASE
    )
    if match_bullet:
        return match_bullet.group(1).strip()

    # General fallback: search for any URL that ends with .pdf or contains /pdf/
    urls = re.findall(r"(https?://\S+)", text)
    for url in urls:
        # Strip trailing chars like commas, brackets, etc.
        clean_url = url.rstrip(").,;*#")
        if ".pdf" in clean_url.lower() or "/pdf/" in clean_url.lower():
            return clean_url

    return ""


def download_pdf_from_url(url: str, dest_path: str):
    """Download a file from a URL to a local destination."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers, stream=True, timeout=30)
    response.raise_for_status()
    with open(dest_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)


def check_if_research_paper(text: str) -> bool:
    """Check if the text is a research paper or academic text using length and a fast LLM check."""
    # Length heuristic: Research papers or abstracts are rarely shorter than 500 characters
    if len(text) < 500:
        return False

    if not gemini_client:
        return False

    try:
        prompt = (
            "Analyze the following text. Is this a research paper, an academic abstract, or scientific manuscript content? "
            "Reply with exactly one word: 'YES' or 'NO'. Do not include other text.\n\n"
            f"Text:\n{text[:2000]}"  # Check first 2000 chars for efficiency
        )
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.0, max_output_tokens=5),
        )
        answer = response.text.strip().upper()
        return "YES" in answer
    except Exception as e:
        print(f"⚠️ Error classifying message: {e}")
        # Fallback to length heuristic if API fails
        return len(text) > 1000


@client.on(events.NewMessage)
async def handle_new_message(event):
    """Listen for incoming Telegram messages, classify, print to console, and analyze if research paper."""
    message_text = event.text or ""

    # 1. Check for PDF file attachment
    is_pdf = False
    pdf_file_name = ""
    if event.message.media and event.message.file:
        mime_type = event.message.file.mime_type or ""
        file_name = event.message.file.name or ""
        if mime_type == "application/pdf" or file_name.lower().endswith(".pdf"):
            is_pdf = True
            pdf_file_name = file_name or "document.pdf"

    # 2. Check for PDF URL link inside the message text
    is_pdf_url = False
    pdf_url = ""
    if not is_pdf and message_text:
        pdf_url = extract_pdf_url(message_text)
        if pdf_url:
            is_pdf_url = True

    # If it's neither text, nor PDF attachment, nor PDF URL, skip
    if not message_text and not is_pdf and not is_pdf_url:
        return

    sender = await event.get_sender()
    sender_name = "Unknown"
    sender_username = "unknown"
    sender_id = "unknown"
    if sender:
        sender_name = (
            f"{sender.first_name or ''} {sender.last_name or ''}".strip() or "Unknown"
        )
        sender_username = sender.username or "No Username"
        sender_id = sender.id

    triggered = False
    paper_text = ""
    temp_path = None

    # Extract exact Telegram message sent timestamp
    msg_date = event.message.date if (event and event.message) else None
    if msg_date:
        sent_timestamp = msg_date.strftime("%Y-%m-%d %H:%M:%S UTC")
    else:
        sent_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        # Handle PDF attachment or PDF URL
        if is_pdf or is_pdf_url:
            if is_pdf:
                # Download from Telegram attachment
                temp_path = await event.message.download_media(file="temp_paper.pdf")
            else:
                # Download from PDF link in message text
                temp_path = "temp_paper.pdf"
                print(f"[{datetime.now()}] Downloading PDF from link: {pdf_url}...")
                await asyncio.to_thread(download_pdf_from_url, pdf_url, temp_path)

            # Extract text using our Open-Closed parser component
            try:
                parser = ParserFactory.get_parser("pdf")
                extracted_text = await asyncio.to_thread(parser.extract_text, temp_path)
            except Exception as e:
                print(f"❌ Error parsing PDF file: {e}")
                extracted_text = ""

            # Classify the extracted text to see if it is a research paper
            if extracted_text:
                is_paper = await asyncio.to_thread(
                    check_if_research_paper, extracted_text
                )
                if is_paper:
                    triggered = True
                    paper_text = extracted_text

        # Handle Text-only messages
        else:
            # Check if message starts with a manual command trigger
            for trigger in TRIGGERS:
                if message_text.lower().startswith(trigger):
                    triggered = True
                    paper_text = message_text[len(trigger) :].strip()
                    break

            # Check if it's a trigger reply
            if not triggered and message_text.lower().strip() in TRIGGERS:
                replied_msg = await event.get_reply_message()
                if replied_msg and replied_msg.text:
                    triggered = True
                    paper_text = replied_msg.text.strip()
                    if replied_msg.date:
                        sent_timestamp = replied_msg.date.strftime("%Y-%m-%d %H:%M:%S UTC")

            # If not command-triggered, check if it is dynamically a research paper
            if not triggered:
                # Run classification check in a thread pool to avoid blocking the event loop
                is_paper = await asyncio.to_thread(
                    check_if_research_paper, message_text
                )
                if is_paper:
                    triggered = True
                    paper_text = message_text.strip()

        # Print to console in a nice format (differentiating normal text, normal PDF, and research)
        print(f"\n{'='*70}")
        print(f"📨 NEW MESSAGE RECEIVED!")
        print(f"{'='*70}")
        print(f"⏰ Sent Time: {sent_timestamp}")
        print(f"👤 From: {sender_name} (@{sender_username})")
        print(f"🆔 User ID: {sender_id}")
        if triggered:
            if is_pdf:
                print(f"💬 Message: Research (PDF: {pdf_file_name})")
            elif is_pdf_url:
                print(f"💬 Message: Research Link (PDF Link: {pdf_url})")
            else:
                print(f"💬 Message: Research")
        else:
            if is_pdf:
                print(f"💬 Message: PDF Attachment ({pdf_file_name})")
            elif is_pdf_url:
                print(f"💬 Message: PDF Link ({pdf_url})")
            else:
                print(f"💬 Message: {message_text}")
        print(f"{'='*70}\n")

        # If not triggered/classified, return early
        if not triggered:
            return

        if not paper_text:
            print(f"⚠️ Triggered analysis, but paper text was empty.")
            return

        # Run Gemini analysis (in thread pool to avoid blocking Telethon)
        print(
            f"[{datetime.now()}] Analyzing paper from {sender_name} (@{sender_username})..."
        )
        analysis: AnalysisResult = await asyncio.to_thread(
            run_gemini_analysis, paper_text
        )

        # Prepare the Apps Script payload (compatible with both array and string handlers in Apps Script)
        student_summary = (
            "\n".join(f"- {item.lstrip('-•* ')}" for item in analysis.studentSummary)
            if isinstance(analysis.studentSummary, list)
            else str(analysis.studentSummary)
        )
        faculty_summary = (
            "\n".join(f"- {item.lstrip('-•* ')}" for item in analysis.facultySummary)
            if isinstance(analysis.facultySummary, list)
            else str(analysis.facultySummary)
        )
        phd_summary = (
            "\n".join(f"- {item.lstrip('-•* ')}" for item in analysis.phdSummary)
            if isinstance(analysis.phdSummary, list)
            else str(analysis.phdSummary)
        )
        product_summary = (
            "\n".join(f"- {item.lstrip('-•* ')}" for item in analysis.productSummary)
            if isinstance(analysis.productSummary, list)
            else str(analysis.productSummary)
        )

        payload = {
            "title": analysis.title,
            "timestamp": sent_timestamp,
            "sender": f"{sender_name} (@{sender_username})",
            "studentSummary": student_summary,
            "facultySummary": faculty_summary,
            "phdSummary": phd_summary,
            "productSummary": product_summary,
        }

        # Call Apps Script Web App (in thread pool)
        print(f"[{datetime.now()}] Appending analysis to Google Doc via Apps Script...")
        script_res = await asyncio.to_thread(post_to_google_doc, payload)

        # Console Logs
        if script_res.get("status") == "success":
            print(
                f"[{datetime.now()}] ✅ Successfully saved analysis of '{analysis.title}' to Google Docs."
            )
        else:
            error_msg = script_res.get("message", "Unknown error from Apps Script")
            print(f"[{datetime.now()}] ❌ Failed to write to Google Docs: {error_msg}")

    except Exception as e:
        print(f"[{datetime.now()}] ❌ Error during analysis process: {e}")

    finally:
        # Cleanup temporary PDF files
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                print(f"⚠️ Error cleaning up temporary file: {e}")


class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK - Telegram Chat Analyser is running")

    def log_message(self, format, *args):
        # Silence HTTP server logs to keep console clean
        pass


def start_health_check_server():
    """Start a lightweight HTTP server on $PORT for Web Service health checks (Render / Railway)."""
    port = int(os.getenv("PORT", "8080"))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        print(f"🌐 Health check HTTP server listening on port {port}")
        server.serve_forever()
    except Exception as e:
        print(f"⚠️ Health check server error: {e}")


async def main():
    """Start the Telethon listener."""
    # Start HTTP health check server in background thread for Web Service hosting
    threading.Thread(target=start_health_check_server, daemon=True).start()

    print(f"\n{'='*70}", flush=True)
    print(f"🚀 TELEGRAM RESEARCH PAPER ANALYSER RUNNING", flush=True)
    print(f"{'='*70}", flush=True)
    print(f"📱 API_ID: {API_ID[:10]}..." if API_ID else "❌ API_ID not set", flush=True)
    print(f"🔐 API_HASH: {API_HASH[:10]}..." if API_HASH else "❌ API_HASH not set", flush=True)
    print(
        f"🧵 Session Mode: {'StringSession (Cloud)' if TELEGRAM_SESSION_STRING else f'Local File (Phone: {PHONE_NUMBER})'}",
        flush=True
    )
    print(f"🔑 Gemini Key: {'✅ Set' if GEMINI_API_KEY else '❌ Missing'}", flush=True)
    print(f"🔗 Apps Script: {'✅ Set' if APPS_SCRIPT_URL else '❌ Missing'}", flush=True)
    print(f"{'='*70}\n", flush=True)

    # Check if running in headless environment without session string
    is_interactive = sys.stdin and sys.stdin.isatty()
    if not TELEGRAM_SESSION_STRING and not is_interactive:
        print("❌ FATAL ERROR: TELEGRAM_SESSION_STRING environment variable is missing!", flush=True)
        print("Render runs in a headless environment and cannot prompt for interactive phone OTP codes.", flush=True)
        print("Please generate TELEGRAM_SESSION_STRING locally (`python generate_session.py`) and add it to Render's Environment Variables.", flush=True)
        sys.exit(1)

    try:
        print("🔄 Connecting to Telegram...", flush=True)
        if TELEGRAM_SESSION_STRING:
            await client.start()
        else:
            await client.start(phone=PHONE_NUMBER)
        print("✅ Connected successfully!", flush=True)
        print("👂 Listening for messages & research papers...", flush=True)
        print("⏹️  Press CTRL+C to stop\n", flush=True)
        await client.run_until_disconnected()
    except Exception as e:
        print(f"❌ Connection Error: {e}", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Analyser stopped by user.")
