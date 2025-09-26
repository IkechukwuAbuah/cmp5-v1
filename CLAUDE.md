# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
cd backend
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### Testing
```bash
# Run all tests
cd backend && pytest tests/ -v

# Run specific test types
pytest tests/contract/ -v      # API contract validation
pytest tests/integration/ -v   # End-to-end scenarios
pytest tests/unit/ -v          # Individual component tests

# Run with coverage (minimum 80% required)
pytest --cov=src tests/

# Run single test file
pytest tests/contract/test_health.py -v
```

### Code Quality
```bash
cd backend

# Format code
black src/
isort src/

# Lint code
flake8 src/
ruff check src/

# Type checking (if applicable)
mypy src/
```

### Spec-Driven Development Commands
```bash
# Check current feature context
export SPECIFY_FEATURE=001-efl-agent-assistant-prototype-track-trace-vo

# Update progress tracking
SPECIFY_FEATURE=001-efl-agent-assistant-prototype-track-trace-vo .specify/scripts/bash/update-agent-context.sh

# Check prerequisites
.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
```

## Architecture Overview

### High-Level Structure
This is an **EFL Agent Assistant** - an AI-powered container tracking system for logistics professionals. It features:

- **Multi-channel Interface**: Both voice (Twilio + OpenAI Realtime) and chat support
- **Natural Language Processing**: Users can query containers using everyday language
- **External API Integration**: Real-time data from EFL Terminal and CMA CGM APIs
- **Graceful Degradation**: Circuit breakers protect against external API failures
- **Session Management**: Multi-turn conversations with context preservation

### Technology Stack
- **Backend**: FastAPI (Python 3.11) with async/await patterns
- **Database**: Redis for session management and caching
- **External APIs**: EFL Terminal, CMA CGM, OpenAI Realtime, Twilio
- **Testing**: pytest with comprehensive contract and integration tests
- **Authentication**: JWT-based role-based access control

### Core System Components

#### 1. API Layer (`backend/src/api/`)
RESTful endpoints following this pattern:
- `/api/v1/health` - System health and service monitoring
- `/api/v1/track` - Natural language container tracking
- `/api/v1/containers/{id}` - Container details and milestones
- `/api/v1/bl/{number}` - Bill of lading information
- `/api/v1/sessions/{id}` - Session management and message history
- `/api/v1/voice/` - Voice interaction endpoints

#### 2. Services Layer (`backend/src/services/`)
Business logic components:
- **TrackService**: Container/BL tracking with NLP processing
- **SessionService**: Multi-turn conversation management
- **AgentService**: Role-based authentication and authorization
- **ExternalAPIService**: EFL Terminal and CMA CGM integration
- **VoiceService**: OpenAI Realtime API integration
- **ResponseService**: Multi-channel response formatting
- **ChannelRouter**: Routes requests between voice and chat channels

#### 3. Data Models (`backend/src/models/`)
Pydantic models for type safety:
- **Container**: Container information, status, milestones
- **Agent**: User authentication and role management
- **Session**: Multi-turn conversation context
- **BillOfLading**: Shipping document information

#### 4. Circuit Breaker Architecture (`backend/src/lib/`)
- **CircuitBreaker**: Protection against external API failures
- **GracefulDegradation**: Fallback mechanisms when services unavailable
- Configurable timeouts and retry policies

#### 5. Voice Integration (`backend/src/voice/`)
Complete voice interaction system:
- **OpenAIRealtime**: Real-time voice processing with OpenAI
- **TwilioHandler**: Phone call management and audio streaming
- **SessionContinuity**: Maintains context across voice interactions
- **AudioUtils**: Audio format conversion and processing

#### 6. Chat Integration (`backend/src/chat/`)
Text-based interaction system:
- **ChatInterface**: Text message processing
- **ChatContinuity**: Context preservation for chat sessions
- **ChatResponse**: Response formatting for different channels

### Key Architectural Patterns

#### Multi-Channel Session Management
The system maintains session continuity across voice and chat channels. Sessions are stored in Redis with:
- Session ID linking voice calls and chat messages
- Context preservation for multi-turn conversations
- Channel-specific state management

#### Circuit Breaker Protection
All external API calls are protected by circuit breakers:
- EFL Terminal API integration with fallback mechanisms
- CMA CGM API with graceful degradation
- OpenAI API with rate limiting and error handling

#### Test-Driven Development Structure
- **Contract Tests**: Validate API specifications before implementation
- **Integration Tests**: End-to-end user journey validation
- **Unit Tests**: Individual component testing
- Minimum 80% code coverage requirement

## Development Workflow

### Spec-Driven Development (SDD)
This project follows the Spec-Driven Development methodology:
1. All features start with `/specify` command to create specifications
2. Use `/plan` to generate technical implementation plans
3. Use `/tasks` to break down work into actionable tasks
4. Tasks are executed following dependencies (setup ’ tests ’ implementation)
5. Progress tracked in `specs/001-efl-agent-assistant-prototype-track-trace-vo/tasks.md`

### Commit Strategy
**One Task = One Commit**
```bash
# Format: type(scope): description (T[task_number])
feat: implement TrackService for container/BL tracking logic (T027)
test: add contract tests for health endpoint (T006)
fix: resolve circuit breaker timeout issues (T046)
```

### Task Dependencies
Respect these implementation dependencies:
1. Setup (T001-T005) ’ All other phases
2. Contract tests (T006-T012) ’ API endpoints (T035-T041)
3. Integration tests (T013-T017) ’ Services (T027-T034)
4. Models (T018-T025) ’ Services (T027-T034)
5. Services (T027-T034) ’ API endpoints (T035-T041)

### Feature Context
Current development focus: **Voice Integration** (Phase 3.5)
- Set `SPECIFY_FEATURE=001-efl-agent-assistant-prototype-track-trace-vo` when working
- Check progress in `specs/001-efl-agent-assistant-prototype-track-trace-vo/tasks.md`
- Update context with progress tracking scripts

## Performance and Quality Requirements

- **Response Time**: <5 seconds for chat, <20 seconds for voice
- **Concurrent Users**: Support 100 simultaneous users
- **Container Volume**: Handle 10K tracking requests per day
- **Availability**: 99.5% uptime with comprehensive health monitoring
- **Security**: TLS 1.3+, GDPR compliance, audit logging
- **Test Coverage**: Minimum 80% coverage for all new code

## Key Files to Understand

- `backend/src/main.py` - FastAPI application entry point
- `backend/src/services/track_service.py` - Core tracking business logic
- `backend/src/services/session_service.py` - Multi-turn conversation management
- `backend/src/lib/circuit_breaker.py` - External API protection
- `specs/001-efl-agent-assistant-prototype-track-trace-vo/plan.md` - Technical architecture decisions
- `AGENTS.md` - AI development guidelines and workflow
- `CONTRIBUTING.md` - Detailed development process and PR guidelines
