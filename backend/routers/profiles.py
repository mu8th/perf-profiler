"""Profile management endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/profiles")
def create_profile(name: str) -> dict:
    """Create a new profiling session. Returns profile ID and metadata."""
    return {"id": 1, "name": name}


@router.get("/profiles/{profile_id}")
def get_profile(profile_id: int) -> dict:
    """Retrieve a profiling session. Returns metadata and collected metrics."""
    return {"id": profile_id, "metrics": []}
