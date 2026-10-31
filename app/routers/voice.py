from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile
from pydantic import BaseModel

from app.services import auth, voice

router = APIRouter(prefix="/api/voice", tags=["voice"], dependencies=[Depends(auth.paid_voice)])


class TtsRequest(BaseModel):
    text: str


@router.post("/stt")
async def stt(audio: UploadFile) -> dict[str, str]:
    try:
        text = await voice.transcribe(
            await audio.read(), audio.filename or "audio.webm", audio.content_type or "audio/webm"
        )
    except voice.VoiceUnavailable as e:
        raise HTTPException(503, str(e)) from e
    return {"text": text}


@router.post("/tts")
async def tts(body: TtsRequest) -> Response:
    try:
        audio = await voice.synthesize(voice.with_disclosure(body.text))
    except voice.VoiceUnavailable as e:
        raise HTTPException(503, str(e)) from e
    return Response(audio, media_type="audio/mpeg")


@router.get("/session")
async def session() -> dict[str, str]:
    try:
        return {"signed_url": await voice.signed_url(), "disclosure": voice.AI_DISCLOSURE}
    except voice.VoiceUnavailable as e:
        raise HTTPException(503, str(e)) from e
