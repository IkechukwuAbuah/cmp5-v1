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
4. Tasks are executed following dependencies (setup � tests � implementation)
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
1. Setup (T001-T005) � All other phases
2. Contract tests (T006-T012) � API endpoints (T035-T041)
3. Integration tests (T013-T017) � Services (T027-T034)
4. Models (T018-T025) � Services (T027-T034)
5. Services (T027-T034) � API endpoints (T035-T041)

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
- **Linear**: when asked to check an issue in linear, always use the mcp. Not the api as that is not configured.


## Key Files to Understand

- `backend/src/main.py` - FastAPI application entry point
- `backend/src/services/track_service.py` - Core tracking business logic
- `backend/src/services/session_service.py` - Multi-turn conversation management
- `backend/src/lib/circuit_breaker.py` - External API protection
- `specs/001-efl-agent-assistant-prototype-track-trace-vo/plan.md` - Technical architecture decisions
- `AGENTS.md` - AI development guidelines and workflow
- `CONTRIBUTING.md` - Detailed development process and PR guidelines

## Linear Workflow
First, verify that Linear MCP tools are available by checking if any `mcp__linear__` tools exist. If not, respond:
```
I need access to Linear tools to help with ticket management. Please run the `/mcp` command to enable the Linear MCP server, then try again.
```

If tools are available, respond based on the user's request:

### For general requests:
```
I can help you with Linear tickets. What would you like to do?
1. Create a new ticket from a thoughts document
2. Add a comment to a ticket (I'll use our conversation context)
3. Search for tickets
4. Update ticket status or details
```

### For specific create requests:
```
I'll help you create a Linear ticket from your thoughts document. Please provide:
1. The path to the thoughts document (or topic to search for)
2. Any specific focus or angle for the ticket (optional)
```

### Automatic Label Assignment
Automatically apply labels based on the ticket content

## Action-Specific Instructions

### 1. Creating Tickets from Thoughts

#### Steps to follow after receiving the request:

1. **Locate and read the thoughts document:**
   - If given a path, read the document directly
   - If given a topic/keyword, search thoughts/ directory using Grep to find relevant documents
   - If multiple matches found, show list and ask user to select
   - Create a TodoWrite list to track: Read document → Analyze content → Draft ticket → Get user input → Create ticket

2. **Analyze the document content:**
   - Identify the core problem or feature being discussed
   - Extract key implementation details or technical decisions
   - Note any specific code files or areas mentioned
   - Look for action items or next steps
   - Identify what stage the idea is at (early ideation vs ready to implement)
   - Take time to ultrathink about distilling the essence of this document into a clear problem statement and solution approach

3. **Check for related context (if mentioned in doc):**
   - If the document references specific code files, read relevant sections
   - If it mentions other thoughts documents, quickly check them
   - Look for any existing Linear tickets mentioned

4. **Get Linear workspace context:**
   - List teams: `mcp__linear__list_teams`
   - If multiple teams, ask user to select one
   - List projects for selected team: `mcp__linear__list_projects`

5. **Draft the ticket summary:**
   Present a draft to the user:
   ```
   ## Draft Linear Ticket

   **Title**: [Clear, action-oriented title]

   **Description**:
   [2-3 sentence summary of the problem/goal]

   ## Key Details
   - [Bullet points of important details from thoughts]
   - [Technical decisions or constraints]
   - [Any specific requirements]

   ## Implementation Notes (if applicable)
   [Any specific technical approach or steps outlined]

**Interactive refinement:**
   Ask the user:
   - Does this summary capture the ticket accurately?
   - Which project should this go in? [show list]
   - What priority? (Default: Medium/3)
   - Any additional context to add?
   - Should we include more/less implementation detail?
   - Do you want to assign it to yourself?

   Note: Ticket will be created in "Triage" status by default.

7. **Create the Linear ticket:**
   ```
   mcp__linear__create_issue with:
   - title: [refined title]
   - description: [final description in markdown]
   - teamId: [selected team]
   - projectId: [use default project from above unless user specifies]
   - priority: [selected priority number, default 3]
   - stateId: [Triage status ID]
   - assigneeId: [if requested]
   - labelIds: [apply automatic label assignment from above]
   - links: [{url: "GitHub URL", title: "Document Title"}]
   ```

8. **Post-creation actions:**
   - Show the created ticket URL
   - Ask if user wants to:
     - Add a comment with additional implementation details
     - Create sub-tasks for specific action items
     - Update the original thoughts document with the ticket reference
   - If yes to updating thoughts doc:
     ```
     Add at the top of the document:
     ---
     linear_ticket: [URL]
     created: [date]
     ---
     ```

## Example transformations:

### From verbose thoughts:
```
"I've been thinking about how our resumed sessions don't inherit permissions properly.
This is causing issues where users have to re-specify everything. We should probably
store all the config in the database and then pull it when resuming. Maybe we need
new columns for permission_prompt_tool and allowed_tools..."
```

### To concise ticket:
```
Title: Fix resumed sessions to inherit all configuration from parent

Description:

## Problem to solve
Currently, resumed sessions only inherit Model and WorkingDir from parent sessions,
causing all other configuration to be lost. Users must re-specify permissions and
settings when resuming.

## Solution
Store all session configuration in the database and automatically inherit it when
resuming sessions, with support for explicit overrides.
```

### Close-Out Checklist
- Reference concrete repo evidence (paths, tests) that support the reported status.
- Update `tasks.md` to reflect verified progress.
- Post a Linear comment summarising findings and transition the issue to `Done` when warranted.

