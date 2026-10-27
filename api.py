import os
import json
import feedparser
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager

# --- 1. AI CONFIGURATION ---
GENAI_API_KEY = os.getenv("GEMINI_API_KEY")
if GENAI_API_KEY:
    genai.configure(api_key=GENAI_API_KEY)
    # Using Gemini 1.5 Flash for high-speed JSON generation
    model = genai.GenerativeModel('gemini-1.5-flash-latest')

# --- 2. GLOBAL CACHE (Prevents Server Crashes & API Limits) ---
# This holds the news in memory. If the AI takes too long, it serves this instantly.
LATEST_NEWS_CACHE = [
    {
        "id": "backup_01",
        "title": "Backend Systems Live: AI Summarizer Initializing",
        "category": "System Update",
        "innovation": "The background scheduler is currently fetching the first batch of live news.",
        "impact": "Ensures zero latency when MIT-WPU students open the dashboard.",
        "takeaway": "Check back in a few minutes for live AI-summarized engineering tech briefs.",
        "read_time": "1 min read",
        "url": "#"
    }
]

# --- 3. AUTONOMOUS BACKGROUND JOB ---
def fetch_and_summarize_news():
    """Runs silently every 6 hours to update the news cache."""
    global LATEST_NEWS_CACHE
    try:
        if not GENAI_API_KEY:
            print("No Gemini API Key found. Serving backup cache.")
            return

        # Fetch top articles from a broad tech source
        feed = feedparser.parse("https://techcrunch.com/feed/")
        new_summaries = []

        for i, entry in enumerate(feed.entries[:4]):  # Process top 4 articles
            # The Prompt: Ruthlessly enforces JSON output and 3-bullet structure
            prompt = f"""
            Analyze this engineering/tech article:
            Title: {entry.title}
            Summary: {entry.summary}
            
            Return ONLY a raw JSON object with exactly these string keys and NO markdown formatting:
            "category": (Classify as Hardware, Software, EV, AI, or General Engineering)
            "innovation": (1 sentence on the core breakthrough)
            "impact": (1 sentence on how it affects the industry)
            "takeaway": (1 sentence on why a first-year B.Tech student should care)
            "read_time": (Estimate read time, e.g., '3 min read')
            """
            
            # Force the model to output strict JSON for Aditya's frontend
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(response_mime_type="application/json")
            )
            
            ai_data = json.loads(response.text)
            
            new_summaries.append({
                "id": f"live_news_{i}",
                "title": entry.title,
                "category": ai_data.get("category", "Tech News"),
                "innovation": ai_data.get("innovation", "Innovation details unavailable."),
                "impact": ai_data.get("impact", "Impact details unavailable."),
                "takeaway": ai_data.get("takeaway", "Takeaway unavailable."),
                "read_time": ai_data.get("read_time", "2 min read"),
                "url": entry.link
            })
            
        if new_summaries:
            LATEST_NEWS_CACHE = new_summaries
            print("News cache updated successfully.")
            
    except Exception as e:
        print(f"Background job failed: {e}. Keeping existing cache.")

# --- 4. APP LIFESPAN (Starts the Scheduler) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run once immediately on server startup
    fetch_and_summarize_news()
    # Schedule to run every 6 hours automatically
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_and_summarize_news, 'interval', hours=6)
    scheduler.start()
    yield
    scheduler.shutdown()

# Initialize App
app = FastAPI(title="MIT-WPU B.Tech Ecosystem API", version="3.0", lifespan=lifespan)

# Allow Frontend Connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 5. DATA MODELS ---
class NewsItem(BaseModel):
    id: str
    title: str
    category: str
    innovation: str
    impact: str
    takeaway: str
    read_time: str
    url: str

class VaultResource(BaseModel):
    subject: str
    icon: str
    primary_playlist: str
    pyq_drive_link: str
    quick_notes: str

class RadarEvent(BaseModel):
    name: str
    date: str
    urgency_level: str
    deadline_hours: int
    registration_link: str

# --- 6. ENDPOINTS ---
@app.get("/api/news", response_model=List[NewsItem])
def get_daily_briefing():
    # Instantly serves the cache (0.05s load time for the frontend)
    return LATEST_NEWS_CACHE

@app.get("/api/vault", response_model=List[VaultResource])
def get_academic_vault():
    return [
        VaultResource(
            subject="Applied Mathematics (Calculus & Linear Algebra)",
            icon="📐",
            primary_playlist="https://www.youtube.com/@GajendraPurohitMathematics",
            pyq_drive_link="https://drive.google.com/drive/folders/mit-wpu-math-pyqs-placeholder",
            quick_notes="https://tutorial.math.lamar.edu/"
        ),
        VaultResource(
            subject="Engineering Mechanics",
            icon="⚙️",
            primary_playlist="https://www.youtube.com/@TiklesAcademy",
            pyq_drive_link="https://drive.google.com/drive/folders/mit-wpu-mechanics-pyqs-placeholder",
            quick_notes="https://www.engineeringtoolbox.com/mechanics-t_71.html"
        ),
        VaultResource(
            subject="Python Programming & Logic",
            icon="🐍",
            primary_playlist="https://www.youtube.com/@CodeWithHarry",
            pyq_drive_link="https://drive.google.com/drive/folders/mit-wpu-python-pyqs-placeholder",
            quick_notes="https://www.w3schools.com/python/"
        ),
        VaultResource(
            subject="Basic Electrical & Electronics (BEE)",
            icon="⚡",
            primary_playlist="https://www.youtube.com/@nesoacademy",
            pyq_drive_link="https://drive.google.com/drive/folders/mit-wpu-bee-pyqs-placeholder",
            quick_notes="https://www.allaboutcircuits.com/textbook/"
        )
    ]

@app.get("/api/radar", response_model=List[RadarEvent])
def get_event_radar():
    return [
        RadarEvent(
            name="Smart India Hackathon 2026",
            date="Nov 10, 2026",
            urgency_level="High",
            deadline_hours=48,
            registration_link="https://sih.gov.in"
        ),
        RadarEvent(
            name="MIT-WPU Gen AI Bootcamp",
            date="Oct 30, 2026",
            urgency_level="Medium",
            deadline_hours=120,
            registration_link="https://unstop.com/"
        )
    ]
