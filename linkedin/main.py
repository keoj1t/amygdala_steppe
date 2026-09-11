import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.database.db import init_db
from backend.routers import projects, linkedin, export

app = FastAPI(
    title="AI Content Factory — LinkedIn Intelligence API",
    description="Production-ready LinkedIn Intelligence module & media generation engine for AI Steppe Tech Hack",
    version="1.0.0"
)

# CORS setup for Vite frontend (http://localhost:5173 / all origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure media directory exists
os.makedirs("media/generated", exist_ok=True)
app.mount("/media", StaticFiles(directory="media"), name="media")

@app.on_event("startup")
def startup_event():
    init_db()

# Include API routers
app.include_router(projects.router)
app.include_router(linkedin.router)
app.include_router(export.router)

@app.get("/")
def root():
    return {
        "status": "online",
        "app": "AI Content Factory — LinkedIn Intelligence Layer",
        "hackathon": "AI Steppe Tech Hack — Astana 2026",
        "docs": "/docs"
    }
