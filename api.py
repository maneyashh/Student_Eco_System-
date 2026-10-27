import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

# Initialize the enterprise-grade FastAPI application
app = FastAPI(title="MIT-WPU B.Tech Ecosystem API", version="2.0.0")

# Security & Access: This allows Aditya's frontend to fetch data without being blocked
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- STRICT DATA MODELS ---
# These models force the frontend to design specific UI components like badges and icons.

class NewsItem(BaseModel):
    id: str
    title: str
    category: str  # Forces UI badges (e.g., "AI", "Hardware")
    innovation: str
    impact: str
    takeaway: str
    read_time: str  # Forces a sleek metadata footer
    url: str

class VaultResource(BaseModel):
    subject: str
    icon: str  # Forces UI to display a clean visual identifier
    primary_playlist: str
    pyq_drive_link: str
    quick_notes: str

class RadarEvent(BaseModel):
    name: str
    date: str
    urgency_level: str  # Forces color-coded UI borders (High = Red, Low = Blue)
    deadline_hours: int
    registration_link: str

# --- ENDPOINTS ---

@app.get("/api/news", response_model=List[NewsItem])
def get_daily_briefing():
    """Delivers the AI-summarized B.Tech news feed."""
    return [
        NewsItem(
            id="news_001",
            title="Solid-State Batteries Hit 1000 Charge Cycles",
            category="Hardware & EV",
            innovation="New lithium-metal anodes completely eliminate battery degradation.",
            impact="Radically changes thermal management architectures in modern EV design.",
            takeaway="Crucial technology to understand for upcoming hardware hackathons.",
            read_time="2 min read",
            url="https://techcrunch.com/"
        ),
        NewsItem(
            id="news_002",
            title="Next-Gen AI Models Slash API Latency by 50%",
            category="Software & AI",
            innovation="Background caching algorithms now operate asynchronously at the server edge.",
            impact="Allows student developers to build real-time AI wrappers for free.",
            takeaway="Update your Python API projects to leverage these new endpoint speeds.",
            read_time="3 min read",
            url="https://wired.com/"
        )
    ]

@app.get("/api/vault", response_model=List[VaultResource])
def get_academic_vault():
    """Delivers the Semester 1 survival resources."""
    return [
        VaultResource(
            subject="Linear Algebra & Differential Calculus",
            icon="🧮",
            primary_playlist="https://youtube.com/playlist?list=...",
            pyq_drive_link="https://drive.google.com/...",
            quick_notes="https://notion.so/..."
        ),
        VaultResource(
            subject="Python Programming",
            icon="🐍",
            primary_playlist="https://youtube.com/playlist?list=...",
            pyq_drive_link="
