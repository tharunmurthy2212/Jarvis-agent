import hashlib
from pathlib import Path
from typing import Optional
import httpx
from app.core.config import settings
from app.core.logger import logger


class UnifiedTTSAdapter:
    """Multi-provider Text-to-Speech client supporting ElevenLabs and Fish Audio."""

    ELEVEN_BASE_URL = "https://api.elevenlabs.io/v1/text-to-speech"
    FISH_API_URL = "https://api.fish.audio/v1/tts"

    def __init__(self, audio_dir: Optional[str] = None):
        self.audio_dir = Path(audio_dir or settings.AUDIO_CACHE_DIR)
        self.audio_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_filename(self, provider: str, voice_or_model: str, text: str) -> str:
        key = f"{provider}_{voice_or_model}_{text.strip()}"
        h = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
        return f"jarvis_{provider}_{h}.mp3"

    async def synthesize(self, text: str, voice_id: Optional[str] = None) -> Optional[str]:
        """
        Synthesize text into speech using configured provider (ElevenLabs by default).
        Returns relative audio URL (e.g. /api/audio/jarvis_elevenlabs_abc123.mp3) or None.
        """
        if not text or not text.strip():
            return None

        clean_text = text.strip()
        provider = settings.TTS_PROVIDER.lower()

        if provider == "elevenlabs":
            return await self._synthesize_elevenlabs(clean_text, voice_id)
        elif provider == "fish_audio":
            return await self._synthesize_fish_audio(clean_text, voice_id)
        else:
            # Try ElevenLabs first if key is available, else Fish Audio
            if settings.ELEVENLABS_API_KEY and settings.ELEVENLABS_API_KEY != "enter your api key":
                return await self._synthesize_elevenlabs(clean_text, voice_id)
            elif settings.FISH_AUDIO_API_KEY and settings.FISH_AUDIO_API_KEY != "enter your api key":
                return await self._synthesize_fish_audio(clean_text, voice_id)
            return None

    async def _synthesize_elevenlabs(self, text: str, voice_id: Optional[str] = None) -> Optional[str]:
        api_key = settings.ELEVENLABS_API_KEY
        if not api_key or api_key == "enter your api key":
            logger.info("ElevenLabs API key not configured. Skipping ElevenLabs synthesis.")
            return None

        voice = voice_id or settings.ELEVENLABS_VOICE_ID or "JBFqnCBsd6RMkjVDRZzb"
        filename = self._get_cache_filename("elevenlabs", voice, text)
        filepath = self.audio_dir / filename

        # Return cached audio if already generated
        if filepath.exists() and filepath.stat().st_size > 100:
            return f"/api/audio/{filename}"

        url = f"{self.ELEVEN_BASE_URL}/{voice}"
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        }
        payload = {
            "text": text[:1500],
            "model_id": settings.ELEVENLABS_MODEL_ID or "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.8
            }
        }

        try:
            logger.info(f"Synthesizing voice with ElevenLabs (voice: {voice})...")
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(url, headers=headers, json=payload)
                if res.status_code == 200 and len(res.content) > 100:
                    filepath.write_bytes(res.content)
                    logger.info(f"ElevenLabs audio cached to {filename}")
                    return f"/api/audio/{filename}"
                else:
                    logger.warning(f"ElevenLabs returned status {res.status_code}: {res.text[:200]}")
                    return None
        except Exception as e:
            logger.error(f"ElevenLabs TTS request failed: {e}")
            return None

    async def _synthesize_fish_audio(self, text: str, model_id: Optional[str] = None) -> Optional[str]:
        api_key = settings.FISH_AUDIO_API_KEY
        if not api_key or api_key == "enter your api key":
            logger.info("Fish Audio API key not configured. Skipping voice synthesis.")
            return None

        active_model = model_id or settings.FISH_AUDIO_MODEL_ID
        filename = self._get_cache_filename("fishaudio", active_model, text)
        filepath = self.audio_dir / filename

        if filepath.exists() and filepath.stat().st_size > 100:
            return f"/api/audio/{filename}"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "text": text[:1000],
            "reference_id": active_model,
            "format": "mp3",
            "normalize": True
        }

        try:
            logger.info(f"Synthesizing voice with Fish Audio (model: {active_model})...")
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(self.FISH_API_URL, headers=headers, json=payload)
                if res.status_code == 200 and len(res.content) > 100:
                    filepath.write_bytes(res.content)
                    return f"/api/audio/{filename}"
                else:
                    logger.warning(f"Fish Audio returned status {res.status_code}: {res.text[:200]}")
                    return None
        except Exception as e:
            logger.error(f"Fish Audio TTS request failed: {e}")
            return None


tts_adapter = UnifiedTTSAdapter()
