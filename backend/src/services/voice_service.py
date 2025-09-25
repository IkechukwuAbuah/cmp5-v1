"""VoiceService for OpenAI Realtime integration."""

import asyncio
import json
from typing import Dict, List, Any, Optional, AsyncGenerator
import websockets
import audioop

from src.core.config import settings
from src.lib.circuit_breaker import CircuitBreakerManager
from src.lib.graceful_degradation import GracefulDegradationService


class VoiceService:
    """Service for voice processing using OpenAI Realtime API."""

    def __init__(self):
        self.degradation_service = None
        self._websocket_connections: Dict[str, websockets.WebSocketServerProtocol] = {}

    async def get_instance(self) -> "VoiceService":
        """Get singleton instance with dependencies initialized."""
        if self.degradation_service is None:
            self.degradation_service = await GracefulDegradationService.get_instance()
        return self

    async def process_voice_input(
        self,
        audio_data: bytes,
        session_id: str,
        agent_id: str
    ) -> str:
        """Process voice input and convert to text."""
        try:
            # Check if OpenAI service is available
            if not self._is_openai_available():
                return "Voice service is currently unavailable. Please try again later."

            # Compress audio if needed
            audio_data = self._compress_audio(audio_data)

            # Convert speech to text using OpenAI Realtime API
            text = await self._speech_to_text(audio_data, session_id)

            # Update service health
            self.degradation_service.update_service_status(
                "openai",
                is_healthy=True,
                response_time_ms=500  # Approximate response time
            )

            return text

        except Exception as e:
            # Update service health
            self.degradation_service.update_service_status(
                "openai",
                is_healthy=False,
                error=str(e)
            )

            # Fallback to text response
            return f"I encountered an issue processing your voice input: {str(e)}. Please try again or use text input."

    async def generate_voice_response(
        self,
        text: str,
        session_id: str,
        agent_id: str
    ) -> bytes:
        """Convert text response to voice audio."""
        try:
            # Check if OpenAI service is available
            if not self._is_openai_available():
                return self._generate_error_audio("Voice service is currently unavailable.")

            # Convert text to speech
            audio_data = await self._text_to_speech(text, session_id)

            # Ensure audio doesn't exceed 20 second limit
            audio_data = self._enforce_time_limit(audio_data, 20)

            # Update service health
            self.degradation_service.update_service_status(
                "openai",
                is_healthy=True,
                response_time_ms=1000  # Approximate response time
            )

            return audio_data

        except Exception as e:
            # Update service health
            self.degradation_service.update_service_status(
                "openai",
                is_healthy=False,
                error=str(e)
            )

            # Fallback to error audio
            return self._generate_error_audio(f"Voice generation failed: {str(e)}")

    async def handle_realtime_conversation(
        self,
        websocket: websockets.WebSocketServerProtocol,
        session_id: str,
        agent_id: str
    ) -> AsyncGenerator[str, None]:
        """Handle real-time voice conversation via WebSocket."""
        try:
            # Store connection
            self._websocket_connections[session_id] = websocket

            # Send session configuration to OpenAI
            await self._configure_openai_session(session_id)

            async for message in websocket:
                if isinstance(message, bytes):
                    # Process audio input
                    text = await self.process_voice_input(message, session_id, agent_id)
                    if text:
                        yield text
                elif isinstance(message, str):
                    # Handle text messages
                    yield message

        except Exception as e:
            print(f"Error in realtime conversation: {e}")
            yield f"Error: {str(e)}"
        finally:
            # Clean up connection
            if session_id in self._websocket_connections:
                del self._websocket_connections[session_id]

    async def _speech_to_text(self, audio_data: bytes, session_id: str) -> str:
        """Convert speech audio to text using OpenAI Realtime API."""
        try:
            # In a real implementation, this would use OpenAI Realtime API
            # For now, simulate with mock response
            return "This is a simulated speech-to-text response for testing purposes."

        except Exception as e:
            raise Exception(f"Speech-to-text failed: {str(e)}")

    async def _text_to_speech(self, text: str, session_id: str) -> bytes:
        """Convert text to speech audio using OpenAI TTS API."""
        try:
            # In a real implementation, this would call OpenAI TTS API
            # For now, return mock audio data
            return b"mock_audio_data_for_testing"

        except Exception as e:
            raise Exception(f"Text-to-speech failed: {str(e)}")

    def _compress_audio(self, audio_data: bytes) -> bytes:
        """Compress audio data if needed."""
        try:
            # In a real implementation, this would compress audio
            # For now, return as-is
            return audio_data
        except Exception:
            return audio_data

    def _enforce_time_limit(self, audio_data: bytes, max_seconds: int) -> bytes:
        """Ensure audio doesn't exceed time limit."""
        try:
            # In a real implementation, this would trim audio to max duration
            # For now, return as-is
            return audio_data
        except Exception:
            return audio_data

    def _generate_error_audio(self, error_message: str) -> bytes:
        """Generate error audio message."""
        # In a real implementation, this would generate TTS for error message
        # For now, return mock data
        return b"error_audio_data"

    def _is_openai_available(self) -> bool:
        """Check if OpenAI service is available."""
        try:
            circuit_breaker = CircuitBreakerManager.get_breaker("openai")
            return circuit_breaker.state.name != "OPEN"
        except Exception:
            return False

    async def _configure_openai_session(self, session_id: str):
        """Configure OpenAI Realtime session."""
        try:
            # In a real implementation, this would configure the OpenAI session
            # For now, just pass
            pass
        except Exception as e:
            print(f"Failed to configure OpenAI session: {e}")

    def get_voice_stats(self) -> Dict[str, Any]:
        """Get voice service statistics."""
        return {
            "active_connections": len(self._websocket_connections),
            "openai_available": self._is_openai_available()
        }

    def validate_audio_format(self, audio_data: bytes) -> bool:
        """Validate audio data format."""
        try:
            # Check if audio data has minimum length
            if len(audio_data) < 100:
                return False

            # In a real implementation, validate audio format (sample rate, channels, etc.)
            return True
        except Exception:
            return False

    def format_voice_response(self, text: str) -> str:
        """Format text response for optimal voice delivery."""
        # Ensure response is concise for voice (under 20 seconds)
        if len(text) > 500:
            text = text[:500] + "..."

        # Add pauses for better voice delivery
        text = text.replace(".", ". <break time='500ms'/>")
        text = text.replace("?", "? <break time='500ms'/>")
        text = text.replace("!", "! <break time='300ms'/>")

        return text
