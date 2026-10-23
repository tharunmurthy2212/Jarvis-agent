from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.schemas.api import TTSRequest, TTSResponse
from app.llm.tts_adapter import tts_adapter
from app.core.config import settings

router = APIRouter(prefix="/api", tags=["Voice & TTS"])


@router.post("/tts", response_model=TTSResponse, summary="Synthesize speech with JARVIS voice")
async def generate_speech(request: TTSRequest) -> TTSResponse:
    voice_or_model = request.model_id or settings.ELEVENLABS_VOICE_ID or settings.FISH_AUDIO_MODEL_ID
    audio_url = await tts_adapter.synthesize(request.text, voice_id=voice_or_model)

    if not audio_url:
        raise HTTPException(
            status_code=503,
            detail="Voice synthesis is unavailable. Check ELEVENLABS_API_KEY or FISH_AUDIO_API_KEY configuration."
        )

    return TTSResponse(audio_url=audio_url, model_id=voice_or_model)


@router.get("/audio/{filename}", summary="Serve generated voice audio")
async def get_audio_file(filename: str):
    # Sanitize path to prevent traversal
    safe_name = Path(filename).name
    file_path = Path(settings.AUDIO_CACHE_DIR) / safe_name

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found.")

    return FileResponse(file_path, media_type="audio/mpeg")
