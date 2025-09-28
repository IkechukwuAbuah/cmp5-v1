"""Unit tests for CulturalContextDetector."""

import json
import pytest
from starlette.requests import Request

from src.localisation.context_detection import CulturalContextDetector, CulturalContextResult


class StubSessionService:
    """In-memory stub for session preference persistence."""

    def __init__(self) -> None:
        self.session_preferences = {}
        self.agent_preferences = {}

    async def get_cultural_preference(self, session_id, agent_id):
        if session_id and agent_id:
            key = (session_id, agent_id)
            if key in self.session_preferences:
                return self.session_preferences[key]
        if agent_id and agent_id in self.agent_preferences:
            return self.agent_preferences[agent_id]
        return None

    async def update_cultural_preference(self, session_id, agent_id, preference):
        persisted = False
        if session_id and agent_id:
            self.session_preferences[(session_id, agent_id)] = preference
            persisted = True
        if agent_id:
            self.agent_preferences[agent_id] = preference
            persisted = True
        return persisted


def build_request(headers=None, query_string="", body=b"") -> Request:
    headers = headers or {}
    raw_headers = [(key.lower().encode(), value.encode()) for key, value in headers.items()]
    scope = {
        "type": "http",
        "method": "POST" if body else "GET",
        "path": "/track",
        "query_string": query_string.encode() if isinstance(query_string, str) else query_string,
        "headers": raw_headers,
    }

    chunks = [body] if body else [b""]

    async def receive():
        if chunks:
            return {"type": "http.request", "body": chunks.pop(0), "more_body": False}
        return {"type": "http.request", "body": b"", "more_body": False}

    request = Request(scope, receive)
    return request


@pytest.mark.asyncio
async def test_explicit_query_preference_persists_to_session():
    stub_service = StubSessionService()

    async def provider():
        return stub_service

    detector = CulturalContextDetector(session_provider=provider)
    request = build_request(query_string="culture=formal_business")

    result = await detector.resolve(
        request,
        session_id="sess-123",
        agent_id="agent-1",
        baseline_context="formal_business",
        baseline_source="query_param",
        explicit_source=True,
    )

    assert isinstance(result, CulturalContextResult)
    assert result.context == "formal_business"
    assert result.source == "query_param"
    assert result.persisted is True
    assert stub_service.session_preferences[("sess-123", "agent-1")] == "formal_business"


@pytest.mark.asyncio
async def test_session_preference_overrides_baseline():
    stub_service = StubSessionService()
    stub_service.session_preferences[("sess-55", "agent-9")] = "west_african"

    async def provider():
        return stub_service

    detector = CulturalContextDetector(session_provider=provider)
    request = build_request(headers={"User-Agent": "Mozilla/5.0"})

    result = await detector.resolve(
        request,
        session_id="sess-55",
        agent_id="agent-9",
        baseline_context="nigerian",
        baseline_source="user_agent",
        explicit_source=False,
    )

    assert result.context == "west_african"
    assert result.source == "session"
    assert result.persisted is False


@pytest.mark.asyncio
async def test_accept_language_inference_without_session():
    stub_service = StubSessionService()

    async def provider():
        return stub_service

    detector = CulturalContextDetector(session_provider=provider)
    request = build_request(headers={"Accept-Language": "en-GH,en;q=0.8"})

    result = await detector.resolve(
        request,
        session_id=None,
        agent_id=None,
        baseline_context=None,
        baseline_source=None,
        explicit_source=False,
    )

    assert result.context == "west_african"
    assert result.source == "accept_language"
    assert result.persisted is False


@pytest.mark.asyncio
async def test_extract_session_identifier_from_json_body():
    detector = CulturalContextDetector()
    body = json.dumps({"sessionId": "sess-body-42"}).encode()
    request = build_request(
        headers={"Content-Type": "application/json"},
        body=body,
    )

    session_id = await detector.extract_session_identifier(request)
    assert session_id == "sess-body-42"

    # Body should be consumable after extraction
    parsed = await request.json()
    assert parsed["sessionId"] == "sess-body-42"
