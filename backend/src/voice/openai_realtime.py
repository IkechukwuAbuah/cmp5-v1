"""OpenAI Realtime integration for speech processing."""

import asyncio
import json
import base64
import io
from typing import Dict, Any, Optional, Callable, AsyncGenerator
from datetime import datetime
import time

import openai
from openai import AsyncOpenAI
from src.core.config import settings
from src.models.agent import Message, SessionContext
from src.services.session_service import SessionService
from src.services.response_service import ResponseService
from src.services.track_service import TrackService
from src.lib.logger import get_logger
from src.lib.log_sanitizer import sanitize
from src.middleware.logging import api_logger


logger = get_logger(__name__)


class OpenAIRealtimeService:
    """Service for OpenAI Realtime API integration."""

    def __init__(self):
        self.client: Optional[AsyncOpenAI] = None
        self.session_service = None
        self.response_service = None
        self.track_service = None
        self.active_sessions: Dict[str, Any] = {}

    async def get_instance(self) -> "OpenAIRealtimeService":
        """Get singleton instance with dependencies initialized."""
        if self.client is None:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        if self.session_service is None:
            self.session_service = await SessionService().get_instance()
        if self.response_service is None:
            self.response_service = await ResponseService().get_instance()
        if self.track_service is None:
            self.track_service = await TrackService().get_instance()
        return self

    async def create_realtime_session(
        self,
        session_id: str,
        agent_id: str,
        system_prompt: str = None
    ) -> str:
        """Create a new OpenAI Realtime session."""
        if system_prompt is None:
            system_prompt = self._get_default_system_prompt()

        try:
            # Create realtime session configuration
            session_config = {
                "model": "gpt-4o-realtime-preview-2024-10-01",
                "modalities": ["text", "audio"],
                "instructions": system_prompt,
                "voice": "alloy",  # Options: alloy, echo, fable, onyx, nova, shimmer
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",  # Server-side voice activity detection
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 800
                },
                "tools": [
                    {
                        "type": "function",
                        "name": "track_containers",
                        "description": "Track container or bill of lading status",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Natural language query for container or BL tracking"
                                }
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "type": "function",
                        "name": "get_container_milestones",
                        "description": "Get detailed milestone history for a container",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "container_id": {
                                    "type": "string",
                                    "description": "Container ID to get milestones for"
                                }
                            },
                            "required": ["container_id"]
                        }
                    }
                ]
            }

            # In a real implementation, this would create an actual OpenAI Realtime session
            # For now, we'll simulate it
            realtime_session_id = f"realtime_{session_id}_{datetime.utcnow().timestamp()}"

            self.active_sessions[realtime_session_id] = {
                "session_id": session_id,
                "agent_id": agent_id,
                "config": session_config,
                "created_at": datetime.utcnow(),
                "last_activity": datetime.utcnow()
            }

            logger.info(f"Created OpenAI Realtime session {realtime_session_id} for session {session_id}")
            return realtime_session_id

        except Exception as e:
            logger.error(f"Error creating OpenAI Realtime session: {e}")
            raise

    async def process_audio_input(
        self,
        session_id: str,
        audio_data: bytes,
        mime_type: str = "audio/wav"
    ) -> AsyncGenerator[str, None]:
        """Process audio input and stream text responses."""
        try:
            # Get the agent session
            session = await self.session_service.get_session(session_id, "voice_user")
            if not session:
                yield "Error: Session not found"
                return

            # Create or get realtime session
            realtime_session_id = await self._get_or_create_realtime_session(session_id, session.agentId)

            # Transcribe audio using Whisper
            transcription = await self._transcribe_audio(audio_data, mime_type)

            if not transcription:
                yield "I didn't catch that. Could you please repeat?"
                return

            yield f"I heard: {transcription}. "

            # Process the transcription
            async for response_chunk in self._process_text_input(session, transcription):
                yield response_chunk

        except Exception as e:
            logger.error(f"Error processing audio input: {e}")
            yield f"I encountered an error processing your audio: {str(e)}"

    async def generate_audio_response(
        self,
        session_id: str,
        text: str
    ) -> bytes:
        """Generate audio from text using OpenAI TTS."""
        try:
            if not self.client:
                raise Exception("OpenAI client not initialized")

            start_time = time.perf_counter()

            # Log API request
            await api_logger.log_api_request(
                api_name="OPENAI_TTS",
                method="POST",
                url="https://api.openai.com/v1/audio/speech",
                body={"model": "tts-1", "voice": "alloy", "input": text[:100] + "..." if len(text) > 100 else text}
            )

            response = await self.client.audio.speech.create(
                model="tts-1",
                voice="alloy",  # Options: alloy, echo, fable, onyx, nova, shimmer
                input=text,
                response_format="wav",
                speed=1.0
            )

            # Convert to bytes
            audio_data = b""
            async for chunk in response.iter_bytes():
                audio_data += chunk

            response_time = (time.perf_counter() - start_time) * 1000

            # Log API response
            await api_logger.log_api_response(
                api_name="OPENAI_TTS",
                status_code=200,
                response_time=response_time,
                body={"audio_size": len(audio_data)}
            )

            logger.info(f"Generated TTS audio: {len(audio_data)} bytes in {response_time:.2f}ms")
            return audio_data

        except Exception as e:
            response_time = (time.perf_counter() - start_time) * 1000 if 'start_time' in locals() else 0
            await api_logger.log_api_response(
                api_name="OPENAI_TTS",
                status_code=500,
                response_time=response_time,
                error=str(e)
            )
            logger.error(f"Error generating audio response: {e}")
            # Return silence or error audio
            return self._generate_silence_audio()

    async def _transcribe_audio(
        self,
        audio_data: bytes,
        mime_type: str
    ) -> Optional[str]:
        """Transcribe audio using OpenAI Whisper."""
        try:
            if not self.client:
                logger.error("OpenAI client not initialized")
                return None

            # Create a file-like object from the audio data
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "audio.wav"

            response = await self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en",  # You can specify language for better accuracy
                response_format="text"
            )

            return response.strip()

        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return None

    async def _process_text_input(
        self,
        session: Any,
        text: str
    ) -> AsyncGenerator[str, None]:
        """Process text input using OpenAI chat completion."""
        try:
            if not self.client:
                yield "Error: OpenAI client not initialized"
                return

            # Add user message to session
            user_message = Message(
                id=f"msg_{session.id}_{len(session.conversationHistory)}",
                type="user",
                content=text,
                timestamp=datetime.utcnow()
            )
            await self.session_service.add_message(session.id, user_message)

            # Get conversation history for context
            conversation_history = session.conversationHistory[-10:]  # Last 10 messages

            # Build messages for OpenAI
            messages = [
                {
                    "role": "system",
                    "content": self._get_system_prompt_for_session(session)
                }
            ]

            # Add conversation history
            for msg in conversation_history:
                messages.append({
                    "role": "user" if msg.type == "user" else "assistant",
                    "content": msg.content
                })

            # Get streaming response
            stream = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                stream=True,
                max_tokens=500,  # Limit for voice responses
                temperature=0.7
            )

            full_response = ""
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content

            # Add assistant response to session
            assistant_message = Message(
                id=f"msg_{session.id}_{len(session.conversationHistory) + 1}",
                type="assistant",
                content=full_response,
                timestamp=datetime.utcnow()
            )
            await self.session_service.add_message(session.id, assistant_message)

        except Exception as e:
            logger.error(f"Error processing text input: {e}")
            yield f"I encountered an error: {str(e)}"

    def _get_default_system_prompt(self) -> str:
        """Get default system prompt for voice interactions."""
        return """You are an EFL Agent Assistant, helping logistics agents track containers and shipments.

Key capabilities:
- Track container status by container number (e.g., "EFLU7896543")
- Track bill of lading status by BL number (e.g., "ABC1234567")
- Provide container locations, status updates, and next steps
- Answer questions about shipping and logistics processes

Guidelines for voice responses:
- Keep responses clear and concise (under 20 seconds when spoken)
- Use simple, natural language
- Provide specific details about containers and shipments
- If something is unclear, ask for clarification
- Always be helpful and professional

Response format:
- Start with the most important information
- Use short sentences
- Include relevant numbers and status updates
- End with next steps or offers for more help"""

    def _get_system_prompt_for_session(self, session: Any) -> str:
        """Get system prompt tailored for the current session."""
        base_prompt = self._get_default_system_prompt()

        # Add context from session
        if session.context.currentIntent:
            base_prompt += f"\n\nCurrent conversation intent: {session.context.currentIntent}"

        if session.context.activeEntities:
            entities_str = ", ".join([f"{e['type']}: {e['id']}" for e in session.context.activeEntities])
            base_prompt += f"\n\nActive entities in conversation: {entities_str}"

        return base_prompt

    async def _get_or_create_realtime_session(
        self,
        session_id: str,
        agent_id: str
    ) -> str:
        """Get existing realtime session or create new one."""
        # Look for existing session
        for realtime_session_id, session_data in self.active_sessions.items():
            if session_data["session_id"] == session_id:
                # Update last activity
                session_data["last_activity"] = datetime.utcnow()
                return realtime_session_id

        # Create new session
        return await self.create_realtime_session(session_id, agent_id)

    def _generate_silence_audio(self, duration_ms: int = 1000) -> bytes:
        """Generate silence audio for error cases."""
        # This would generate actual silence audio
        # For now, return empty bytes
        return b""

    async def cleanup_inactive_sessions(self, max_age_minutes: int = 30):
        """Clean up inactive realtime sessions."""
        current_time = datetime.utcnow()
        expired_sessions = []

        for session_id, session_data in self.active_sessions.items():
            last_activity = session_data.get("last_activity", session_data["created_at"])
            age = (current_time - last_activity).total_seconds() / 60

            if age > max_age_minutes:
                expired_sessions.append(session_id)

        # Remove expired sessions
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
            logger.info(f"Cleaned up inactive OpenAI Realtime session {session_id}")

    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about active sessions."""
        total_sessions = len(self.active_sessions)
        return {
            "total_sessions": total_sessions,
            "sessions": list(self.active_sessions.keys())
        }


# Global instance
_openai_realtime: Optional[OpenAIRealtimeService] = None


async def get_openai_realtime() -> OpenAIRealtimeService:
    """Get or create OpenAI Realtime service instance."""
    global _openai_realtime
    if _openai_realtime is None:
        _openai_realtime = await OpenAIRealtimeService().get_instance()
    return _openai_realtime
