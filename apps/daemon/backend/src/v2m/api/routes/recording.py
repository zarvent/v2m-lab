from fastapi import APIRouter
from v2m.api.schemas import ToggleResponse
from v2m.api.app import state

router = APIRouter()


@router.post("/toggle", response_model=ToggleResponse)
async def toggle_recording() -> ToggleResponse:
    return await state.recording.toggle()


@router.post("/start", response_model=ToggleResponse)
async def start_recording() -> ToggleResponse:
    return await state.recording.start()


@router.post("/stop", response_model=ToggleResponse)
async def stop_recording() -> ToggleResponse:
    return await state.recording.stop()
