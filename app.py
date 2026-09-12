"""
app.py
Dedicated FastAPI REST API backend for Mahdi's AI Digital Twin.
Designed for direct external calls from the React Portfolio chat widget.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import ask_agent

# Initialize FastAPI app directly as 'app' (standard for FastAPI / Uvicorn deployments)
app = FastAPI(
    title="Mahdi AI Digital Twin API",
    description="REST API for Mahdi Al Sabeh's AI Digital Twin",
    version="1.0.0",
)

# Enable CORS for local React development & production portfolio domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    history: list = []


class ChatResponse(BaseModel):
    response: str


@app.get("/")
async def root():
    """Root endpoint verifying API is active."""
    return {
        "status": "online",
        "service": "Mahdi AI Digital Twin API",
        "chat_endpoint": "/api/chat",
        "health_check": "/api/health",
        "cv_status": "/api/cv-status",
        "refresh_cv": "/api/refresh-cv",
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "Mahdi AI Digital Twin API"}


@app.get("/api/cv-status")
async def cv_status():
    """Returns the currently active CV source and cache timestamp."""
    from cv_loader import get_cv_summary, _CV_CACHE
    get_cv_summary()
    return {
        "status": "ok",
        "active_source": _CV_CACHE.get("source", "unknown"),
        "cached_at": _CV_CACHE.get("last_fetched", 0),
    }


@app.post("/api/refresh-cv")
async def refresh_cv():
    """Forces an immediate reload of the CV from remote URL or local source."""
    from cv_loader import get_cv_summary, _CV_CACHE
    get_cv_summary(force_refresh=True)
    return {
        "status": "refreshed",
        "active_source": _CV_CACHE.get("source", "unknown"),
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    """REST API endpoint consumed by the React Portfolio chat widget."""
    reply = await ask_agent(payload.message, payload.history)
    return ChatResponse(response=reply)


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 7860))
    print(f"\n🚀 Starting FastAPI server on http://0.0.0.0:{port}")
    print(f"📡 Chat API Endpoint: http://localhost:{port}/api/chat\n")
    uvicorn.run(app, host="0.0.0.0", port=port)