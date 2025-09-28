"""Twilio webhook handler for voice input processing."""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import Request, Response, HTTPException
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client

from src.core.config import settings
from src.models.agent import ChannelType
from src.models.agent_session import AgentSession, Message
from src.services.session_service import SessionService
from src.services.response_service import ResponseService
from src.services.track_service import TrackService
from src.lib.logger import get_logger
from src.lib.log_sanitizer import sanitize, sanitize_headers


logger = get_logger(__name__)


class TwilioVoiceHandler:
    """Handles Twilio voice webhooks for the EFL Agent Assistant."""

    def __init__(self):
        self.twilio_client = None
        self.session_service = None
        self.response_service = None
        self.track_service = None

    async def get_instance(self) -> "TwilioVoiceHandler":
        """Get singleton instance with dependencies initialized."""
        if self.twilio_client is None:
            self.twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        if self.session_service is None:
            self.session_service = await SessionService().get_instance()
        if self.response_service is None:
            self.response_service = await ResponseService().get_instance()
        if self.track_service is None:
            self.track_service = await TrackService().get_instance()
        return self

    async def handle_incoming_call(self, request: Request) -> str:
        """Handle incoming Twilio voice call."""
        try:
            # Get form data from Twilio
            form_data = await request.form()
            call_sid = form_data.get('CallSid')
            from_number = form_data.get('From')
            to_number = form_data.get('To')

            logger.info(f"Incoming call from {from_number} to {to_number}, CallSID: {call_sid}")

            # Create or retrieve session for this caller
            language_pref = getattr(request.state, "language", None)
            cultural_pref = getattr(request.state, "cultural_context", None)

            session = await self._get_or_create_session(
                from_number,
                call_sid,
                language_pref,
                cultural_pref,
            )

            await self.session_service.update_localisation_preferences(
                session.id,
                session.agentId,
                language=language_pref,
                cultural_context=cultural_pref,
            )

            twilio_language = self._twilio_language_for(session.context.preferredLanguage)

            # Generate TwiML response
            response = VoiceResponse()

            # Add gather for speech input
            gather = response.gather(
                input='speech',
                action=f'/api/v1/voice/process-speech?session_id={session.id}',
                method='POST',
                timeout=10,
                speech_timeout='auto',
                language=twilio_language,
                hints='container, tracking, shipment, bill of lading, status'
            )

            # Welcome message
            gather.say(
                "Welcome to EFL Agent Assistant. I'm here to help you track containers and shipments. "
                "Please say the container number or bill of lading number you'd like to track, "
                "or ask for help.",
                voice='alice',
                language=twilio_language
            )

            # If no input received, redirect back
            response.redirect('/api/v1/voice/handle-call', method='POST')

            return str(response)

        except Exception as e:
            logger.error(f"Error handling incoming call: {e}")
            return self._generate_error_response()

    async def process_speech_input(self, request: Request) -> str:
        """Process speech input from Twilio gather."""
        try:
            form_data = await request.form()
            session_id = form_data.get('session_id')
            call_sid = form_data.get('CallSid')
            speech_result = form_data.get('SpeechResult')
            confidence = float(form_data.get('Confidence', 0))

            logger.info(f"Processing speech input for session {session_id}: {speech_result}")

            # Get session
            session = await self.session_service.get_session(session_id, None)
            if not session:
                return self._generate_error_response("Session not found. Please try again.")

            language_pref = getattr(request.state, "language", None)
            cultural_pref = getattr(request.state, "cultural_context", None)
            await self.session_service.update_localisation_preferences(
                session.id,
                session.agentId,
                language=language_pref,
                cultural_context=cultural_pref,
            )

            twilio_language = self._twilio_language_for(
                language_pref or session.context.preferredLanguage
            )

            # Add user message to session
            user_message = Message(
                id=f"msg_{call_sid}_{len(session.conversationHistory)}",
                type="user",
                content=speech_result,
                timestamp=datetime.utcnow()
            )
            await self.session_service.add_message(session.id, user_message)

            # Process the query
            response_text = await self._process_voice_query(speech_result, session)

            # Add assistant response to session
            assistant_message = Message(
                id=f"msg_{call_sid}_{len(session.conversationHistory) + 1}",
                type="assistant",
                content=response_text,
                timestamp=datetime.utcnow()
            )
            await self.session_service.add_message(session.id, assistant_message)

            # Generate TwiML response
            twiml_response = VoiceResponse()

            # Truncate response for voice (20 second limit)
            truncated_response = self.response_service.truncate_for_voice(response_text, 500)

            # Enhance for better voice delivery
            voice_response = self.response_service.enhance_for_voice(truncated_response)

            twiml_response.say(
                voice_response,
                voice='alice',
                language=twilio_language
            )

            # Check if we need follow-up
            if self._needs_followup(speech_result):
                twiml_response.gather(
                    input='speech',
                    action=f'/api/v1/voice/process-speech?session_id={session.id}',
                    method='POST',
                    timeout=10,
                    speech_timeout='auto',
                    language=twilio_language
                ).say("Do you need help with anything else?", voice='alice')

            # Hang up
            twiml_response.hangup()

            return str(twiml_response)

        except Exception as e:
            logger.error(f"Error processing speech input: {e}")
            return self._generate_error_response()

    async def _get_or_create_session(
        self,
        phone_number: str,
        call_sid: str,
        language: Optional[str] = None,
        cultural_context: Optional[str] = None,
    ) -> AgentSession:
        """Get existing session or create new one for phone number."""
        # Try to find existing active session for this phone number
        # This is a simplified implementation - in production, you'd want more sophisticated session management
        session_id = f"voice_{call_sid}"

        existing_session = await self.session_service.get_session(session_id, phone_number)
        if existing_session:
            return existing_session

        session = await self.session_service.create_session(phone_number, ChannelType.VOICE)

        # Override the session ID to match our call_sid for tracking
        original_id = session.id
        session.id = session_id
        # Ensure service cache uses the new identifier
        if original_id in self.session_service._sessions:
            self.session_service._sessions.pop(original_id)
        self.session_service._sessions[session_id] = session

        await self.session_service.update_localisation_preferences(
            session.id,
            session.agentId,
            language=language,
            cultural_context=cultural_context,
        )
        return session

    def _twilio_language_for(self, preference: Optional[str]) -> str:
        """Map ISO language codes to Twilio-supported locales."""
        lookup = {
            "en": "en-US",
            "en-gb": "en-GB",
            "en-ng": "en-NG",
            "fr": "fr-FR",
            "fr-sn": "fr-FR",
            "pt": "pt-PT",
            "pt-pt": "pt-PT",
            "pt-br": "pt-BR",
            "ar": "ar-SA",
        }

        if not preference:
            return "en-US"

        code = preference.lower()
        return lookup.get(code, lookup.get(code.split('-')[0], "en-US"))

    async def _process_voice_query(self, query: str, session: AgentSession) -> str:
        """Process a voice query and return response."""
        try:
            # Use track service to process the query
            containers, bill_of_ladings = await self.track_service.track_containers(query)

            # Format response for voice channel
            response = self.response_service.format_tracking_response(
                query=query,
                containers=containers,
                bill_of_ladings=bill_of_ladings,
                channel=ChannelType.VOICE
            )

            return response

        except Exception as e:
            logger.error(f"Error processing voice query '{query}': {e}")
            return self.response_service.format_error_response(
                f"I encountered an issue processing your request: {str(e)}",
                ChannelType.VOICE
            )

    def _needs_followup(self, query: str) -> bool:
        """Determine if the query requires follow-up interaction."""
        followup_keywords = ['yes', 'sure', 'okay', 'help', 'what', 'how', 'more', 'details']
        query_lower = query.lower()

        return any(keyword in query_lower for keyword in followup_keywords)

    def _generate_error_response(self, message: str = "An error occurred. Please try again.") -> str:
        """Generate error response TwiML."""
        response = VoiceResponse()
        response.say(message, voice='alice', language='en-US')
        response.hangup()
        return str(response)

    async def get_call_status(self, call_sid: str) -> Dict[str, Any]:
        """Get status of a Twilio call."""
        try:
            call = self.twilio_client.calls(call_sid).fetch()
            return {
                "call_sid": call.sid,
                "status": call.status,
                "duration": call.duration,
                "price": call.price
            }
        except Exception as e:
            logger.error(f"Error getting call status for {call_sid}: {e}")
            return {"error": str(e)}


# Global instance
_twilio_handler: Optional[TwilioVoiceHandler] = None


async def get_twilio_handler() -> TwilioVoiceHandler:
    """Get or create Twilio voice handler instance."""
    global _twilio_handler
    if _twilio_handler is None:
        _twilio_handler = await TwilioVoiceHandler().get_instance()
    return _twilio_handler
