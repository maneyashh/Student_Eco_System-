import os
import json
import re
import feedparser
import google.generativeai as genai
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from supabase import create_client, Client

# --- 1. ENVIRONMENT & SECURITY KEYS ---
GENAI_API_KEY = os.getenv("GEMINI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize AI Engine
if GENAI_API_KEY:
    genai.configure(api_key=GENAI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')

# Initialize Database Engine
supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 2. THE PERSISTENT MEMORY CACHE ---
LATEST_NEWS_CACHE = [
    {
        "id": "backup_01",
        "title": "Backend Systems Live: AI Summarizer Initializing",
        "category": "System Update",
        "innovation": "The background scheduler is currently fetching live news.",
        "impact": "Ensures zero latency for MIT-WPU students upon loading.",
        "takeaway": "Check back shortly for the first live batch.",
        "read_time": "1 min read",
        "url": "#"
    }
]

# --- 3. THE AI SAFETY NET & BACKGROUND WORKER ---
def clean_json_response(raw_text):
    """Regex cleaner: Strips rogue markdown so the JSON parser never crashes."""
    match = re.search(r'\{.*\}', raw_text, re.DOTALL)
    if match:
        return match.group(0)
    return raw_text

def fetch_and_summarize_news():
    global LATEST_NEWS_CACHE
    try:
        if not GENAI_API_KEY:
            return

        feed = feedparser.parse("https://techcrunch.com/feed/")
        new_summaries = []

        for i, entry in enumerate(feed.entries[:4]):
            prompt = f"""
            Analyze this engineering/tech article:
            Title: {entry.title}
            Summary: {entry.summary}
            
            Return ONLY a raw JSON object with exactly these keys:
            "category", "innovation", "impact", "takeaway", "read_time"
            """
            
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(response_mime_type="application/json")
            )
            
            clean_text = clean_json_response(response.text)
            ai_data = json.loads(clean_text)
            
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
            
    except Exception as e:
        print(f"Background job failed: {e}. Keeping existing cache.")

# --- 4. SYSTEM LIFESPAN CONTROLLER ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    fetch_and_summarize_news()
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_and_summarize_news, 'interval', hours=6)
    scheduler.start()
    yield
    scheduler.shutdown()

# Initialize API Engine
app = FastAPI(title="MIT-WPU B.Tech API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Change to Aditya's Vercel URL later to lock the vault
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 5. ENTERPRISE ENDPOINTS (v1) ---

@app.get("/health")
def system_health_check():
    """Lets the frontend know if the server is awake and connected."""
    return {
        "status": "active", 
        "version": "1.0.0", 
        "database": "connected" if supabase else "disconnected"
    }

@app.get("/api/v1/news")
def get_daily_briefing():
    """Serves the AI-summarized tech news from memory instantly."""
    return LATEST_NEWS_CACHE

@app.get("/api/v1/vault")
def get_dynamic_vault():
    """Pulls live academic resources directly from the Supabase database."""
    if not supabase:
        return {"error": "Database disconnected"}
    response = supabase.table("vault_resources").select("*").execute()
    return response.data

@app.get("/api/v1/radar")
def get_dynamic_radar():
    """Pulls live hackathon and campus events directly from the Supabase database."""
    if not supabase:
        return {"error": "Database disconnected"}
    response = supabase.table("radar_events").select("*").execute()
    return response.data
