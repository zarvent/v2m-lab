from fastapi import APIRouter
from v2m.api.schemas import StatusResponse, HealthResponse
from v2m.api.app import state

router = APIRouter()


@router.get("/status", response_model=StatusResponse)
async def get_status() -> StatusResponse:
    return state.recording.get_status()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse()
