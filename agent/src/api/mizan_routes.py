"""Read-only API endpoints exposing Mizan safety status inside Vibe."""
from fastapi import APIRouter

from src.mizan_safety import status_payload

router = APIRouter(prefix="/api/mizan", tags=["Mizan paper safety"])


@router.get("/status")
def mizan_safety_status() -> dict:
    """Return the active paper-only safety policy; does not execute trades."""
    return status_payload()
