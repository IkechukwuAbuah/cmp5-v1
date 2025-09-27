"""Voice API endpoints for EFL Agent Assistant."""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks

from src.core.config import settings
from src.voice.twilio_handler import get_twilio_handler
from src.voice.openai_realtime import get_openai_realtime
from src.voice.session_continuity import get_voice_continuity
from src.voice.audio_utils import get_audio_processor


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["voice"])


@router.post("/handle-call")
async def handle_incoming_call(request: Request) -> Dict[str, str]:
    """Handle incoming Twilio voice call."""
    try:
        twilio_handler = await get_twilio_handler()
        twiml_response = await twilio_handler.handle_incoming_call(request)

        return {"twiml": twiml_response}

    except Exception as e:
        logger.error(f"Error handling incoming call: {e}")
        raise HTTPException(status_code=500, detail="Error handling call")


@router.post("/process-speech")
async def process_speech_input(request: Request) -> Dict[str, str]:
    """Process speech input from Twilio gather."""
    try:
        twilio_handler = await get_twilio_handler()
        twiml_response = await twilio_handler.process_speech_input(request)

        return {"twiml": twiml_response}

    except Exception as e:
        logger.error(f"Error processing speech input: {e}")
        raise HTTPException(status_code=500, detail="Error processing speech")


@router.post("/interact")
async def voice_interaction(
    request: Request,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Handle voice interaction with continuity."""
    try:
        # Get audio data from request
        form_data = await request.form()
        session_id = form_data.get("session_id")
        phone_number = form_data.get("phone_number", "unknown")

        # Get audio file
        audio_file = form_data.get("audio")
        if not audio_file:
            raise HTTPException(status_code=400, detail="No audio file provided")

        # Read audio data
        audio_data = await audio_file.read()

        # Process voice interaction
        voice_continuity = await get_voice_continuity()
        result = await voice_continuity.handle_voice_interaction(
            phone_number=phone_number,
            audio_input=audio_data,
            session_id=session_id
        )

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])

        # Clean up expired sessions in background
        background_tasks.add_task(voice_continuity.cleanup_expired_sessions)

        return {
            "session_id": result["session_id"],
            "response_text": result["response_text"],
            "context": result["context"],
            "metadata": result["metadata"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in voice interaction: {e}")
        raise HTTPException(status_code=500, detail="Error processing voice interaction")


@router.post("/continue")
async def continue_voice_conversation(
    session_id: str,
    request: Request,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Continue an existing voice conversation."""
    try:
        # Get audio data
        form_data = await request.form()
        audio_file = form_data.get("audio")
        if not audio_file:
            raise HTTPException(status_code=400, detail="No audio file provided")

        audio_data = await audio_file.read()

        # Get context override if provided
        context_override = form_data.get("context")
        context_dict = None
        if context_override:
            try:
                import json
                context_dict = json.loads(context_override)
            except json.JSONDecodeError:
                pass  # Ignore invalid JSON

        # Continue conversation
        voice_continuity = await get_voice_continuity()
        result = await voice_continuity.continue_conversation(
            session_id=session_id,
            audio_input=audio_data,
            context_override=context_dict
        )

        if not result["success"]:
            raise HTTPException(status_code=404 if "not found" in result["error"].lower() else 500,
                              detail=result["error"])

        # Clean up expired sessions in background
        background_tasks.add_task(voice_continuity.cleanup_expired_sessions)

        return {
            "session_id": result["session_id"],
            "response_text": result["response_text"],
            "context": result["context"],
            "metadata": result["metadata"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error continuing voice conversation: {e}")
        raise HTTPException(status_code=500, detail="Error continuing conversation")


@router.get("/session/{session_id}")
async def get_voice_session(session_id: str) -> Dict[str, Any]:
    """Get voice session information."""
    try:
        voice_continuity = await get_voice_continuity()
        session_summary = await voice_continuity.get_session_summary(session_id)

        if not session_summary:
            raise HTTPException(status_code=404, detail="Session not found")

        return session_summary

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting voice session: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving session")


@router.delete("/session/{session_id}")
async def end_voice_session(session_id: str) -> Dict[str, Any]:
    """End a voice session."""
    try:
        voice_continuity = await get_voice_continuity()
        success = await voice_continuity.end_voice_session(session_id)

        if not success:
            raise HTTPException(status_code=404, detail="Session not found")

        return {"message": "Session ended successfully", "session_id": session_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ending voice session: {e}")
        raise HTTPException(status_code=500, detail="Error ending session")


@router.get("/sessions")
async def get_active_voice_sessions() -> Dict[str, Any]:
    """Get all active voice sessions."""
    try:
        voice_continuity = await get_voice_continuity()
        return {
            "active_sessions": voice_continuity.get_active_session_count(),
            "sessions": []  # Could include session summaries if needed
        }

    except Exception as e:
        logger.error(f"Error getting active sessions: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving sessions")


@router.post("/test-audio")
async def test_audio_processing(request: Request) -> Dict[str, Any]:
    """Test endpoint for audio processing."""
    try:
        form_data = await request.form()
        audio_file = form_data.get("audio")

        if not audio_file:
            raise HTTPException(status_code=400, detail="No audio file provided")

        audio_data = await audio_file.read()
        audio_processor = get_audio_processor()

        # Validate audio
        mime_type = form_data.get("mime_type", "audio/wav")
        is_valid = audio_processor.validate_audio_format(audio_data, mime_type)

        if not is_valid:
            return {
                "valid": False,
                "error": "Unsupported audio format"
            }

        # Get audio info
        info = audio_processor.get_audio_info(audio_data)

        # Get quality score
        quality = audio_processor.get_audio_quality_score(audio_data)

        return {
            "valid": True,
            "info": info,
            "quality_score": quality,
            "optimized": len(audio_processor.optimize_for_voice_processing(audio_data)) > 0
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing audio processing: {e}")
        raise HTTPException(status_code=500, detail="Error testing audio")


@router.get("/health")
async def voice_health_check() -> Dict[str, Any]:
    """Health check for voice services."""
    try:
        # Test basic functionality of voice services
        voice_continuity = await get_voice_continuity()
        audio_processor = get_audio_processor()

        return {
            "status": "healthy",
            "services": {
                "voice_continuity": voice_continuity.get_active_session_count() >= 0,
                "audio_processor": audio_processor is not None
            },
            "configuration": {
                "twilio_enabled": bool(settings.TWILIO_ACCOUNT_SID),
                "openai_enabled": bool(settings.OPENAI_API_KEY),
                "voice_enabled": settings.ENABLE_VOICE
            }
        }

    except Exception as e:
        logger.error(f"Voice health check failed: {e}")
        raise HTTPException(status_code=500, detail="Voice services unhealthy")
