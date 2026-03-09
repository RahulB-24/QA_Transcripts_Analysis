"""
FastAPI Server
===============
Exposes the Trust-Weighted QA pipeline over HTTP.

Endpoints
---------
GET  /meetings   — list available meeting IDs
POST /ask        — ask a question about a meeting
"""

import sys
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Ensure backend root is importable
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from pipeline.pipeline import QAPipeline

# ── Pydantic request / response models ──────────────────────────────────


class AskRequest(BaseModel):
    """Request body for the ``/ask`` endpoint."""
    meeting_id: str = Field(..., description="Meeting identifier")
    question: str = Field(..., description="Natural-language question")


class EvidenceItem(BaseModel):
    """Single piece of evidence returned with an answer."""
    speaker: str
    text: str
    timestamp: float
    trust_score: float


class AskResponse(BaseModel):
    """Response body for the ``/ask`` endpoint."""
    answer: str
    evidence: list[EvidenceItem]


# ── Application lifespan (initialise pipeline once) ────────────────────

_pipeline: QAPipeline | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialise the QA pipeline at startup."""
    global _pipeline
    print("[Server] Initialising QA pipeline …")
    _pipeline = QAPipeline()
    print("[Server] Pipeline ready — accepting requests.")
    yield
    # Cleanup (if needed) on shutdown
    _pipeline = None


# ── FastAPI app ─────────────────────────────────────────────────────────

app = FastAPI(
    title="Trust-Weighted Meeting QA",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Endpoints ───────────────────────────────────────────────────────────


@app.get("/meetings", response_model=list[str])
async def list_meetings() -> list[str]:
    """Return all available meeting IDs."""
    if _pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not ready")
    return _pipeline.get_meeting_ids()


@app.post("/ask", response_model=AskResponse)
async def ask_question(body: AskRequest) -> AskResponse:
    """Answer a question about a specific meeting.

    Parameters
    ----------
    body : AskRequest
        JSON body with ``meeting_id`` and ``question``.

    Returns
    -------
    AskResponse
        Generated answer and supporting evidence.
    """
    if _pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not ready")

    meeting_ids = _pipeline.get_meeting_ids()
    if body.meeting_id not in meeting_ids:
        raise HTTPException(
            status_code=404,
            detail=f"Meeting '{body.meeting_id}' not found. "
            f"Available: {meeting_ids[:10]}{'…' if len(meeting_ids) > 10 else ''}",
        )

    try:
        result: dict[str, Any] = _pipeline.ask(
            meeting_id=body.meeting_id,
            question=body.question,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return AskResponse(
        answer=result["answer"],
        evidence=[EvidenceItem(**e) for e in result["evidence"]],
    )
