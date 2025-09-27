# Tasks: EFL Agent Assistant Prototype: Track & Trace (Voice + Chat)

**Input**: Design documents from `/specs/001-efl-agent-assistant-prototype-track-trace-vo/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → If not found: ERROR "No implementation plan found"
   → Extract: tech stack, libraries, structure
2. Load optional design documents:
   → data-model.md: Extract entities → model tasks
   → contracts/: Each file → contract test task
   → research.md: Extract decisions → setup tasks
3. Generate tasks by category:
   → Setup: project init, dependencies, linting
   → Tests: contract tests, integration tests
   → Core: models, services, CLI commands
   → Integration: DB, middleware, logging
   → Polish: unit tests, performance, docs
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   → All contracts have tests?
   → All entities have models?
   → All endpoints implemented?
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 3.1: Setup
- [x] T001 Create project structure per implementation plan ✅
- [x] T002 Initialize Python/FastAPI project with dependencies ✅
- [x] T003 [P] Configure linting and formatting tools (black, isort, flake8) ✅
- [x] T004 [P] Set up Redis for session management and caching ✅
- [x] T005 [P] Configure environment variables and settings ✅

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [x] T006 [P] Contract test GET /health in tests/contract/test_health.py ✅
- [x] T007 [P] Contract test POST /track in tests/contract/test_track_post.py ✅
- [x] T008 [P] Contract test GET /containers/{id} in tests/contract/test_containers_get.py ✅
- [x] T009 [P] Contract test GET /containers/{id}/milestones in tests/contract/test_milestones_get.py ✅
- [x] T010 [P] Contract test GET /bl/{bl} in tests/contract/test_bl_get.py ✅
- [x] T011 [P] Contract test GET /sessions/{id} in tests/contract/test_sessions_get.py ✅
- [x] T012 [P] Contract test GET /sessions/{id}/messages in tests/contract/test_session_messages_get.py ✅
- [x] T013 [P] Integration test basic container tracking in tests/integration/test_container_tracking.py ✅
- [x] T014 [P] Integration test BL tracking scenario in tests/integration/test_bl_tracking.py ✅
- [x] T015 [P] Integration test voice interaction flow in tests/integration/test_voice_flow.py ✅
- [x] T016 [P] Integration test fallback logic in tests/integration/test_fallback_logic.py ✅
- [x] T017 [P] Integration test multi-turn conversation in tests/integration/test_multi_turn.py ✅

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [x] T018 [P] Container model in backend/src/models/container.py ✅
- [x] T019 [P] BillOfLading model in backend/src/models/bill_of_lading.py ✅
- [x] T020 [P] Agent model in backend/src/models/agent.py ✅
- [x] T021 [P] TerminalLocation model in backend/src/models/terminal_location.py ✅
- [x] T022 [P] VesselVoyage model in backend/src/models/vessel_voyage.py ✅
- [x] T023 [P] ContainerMilestone model in backend/src/models/container_milestone.py ✅
- [x] T024 [P] AgentSession model in backend/src/models/agent_session.py ✅
- [x] T025 [P] SessionContext model in backend/src/models/session_context.py ✅
- [x] T026 [P] Create Pydantic schemas for API contracts in backend/src/schemas/ ✅
- [x] T027 TrackService for container/BL tracking logic in backend/src/services/track_service.py ✅
- [x] T028 SessionService for multi-channel session management in backend/src/services/session_service.py ✅
- [x] T029 AgentService for agent validation and permissions in backend/src/services/agent_service.py ✅
- [x] T030 ExternalAPIService for EFL Terminal and CMA CGM integration in backend/src/services/external_api_service.py ✅
- [x] T031 MCP server for EFL Terminal API integration in backend/src/mcp/efl_terminal_server.py ✅
- [x] T032 MCP server for CMA CGM API integration in backend/src/mcp/cma_cgm_server.py ✅
- [x] T033 VoiceService for OpenAI Realtime integration in backend/src/services/voice_service.py ✅
- [x] T034 ResponseService for natural language response formatting in backend/src/services/response_service.py ✅

## Phase 3.4: API Endpoints
- [x] T035 GET /health endpoint in backend/src/api/health.py ✅
- [x] T036 POST /track endpoint with natural language processing in backend/src/api/track.py ✅
- [x] T037 GET /containers/{containerId} endpoint in backend/src/api/containers.py ✅
- [x] T038 GET /containers/{containerId}/milestones endpoint in backend/src/api/containers.py ✅
- [x] T039 GET /bl/{blNumber} endpoint in backend/src/api/bl.py ✅
- [x] T040 GET /sessions/{sessionId} endpoint in backend/src/api/sessions.py ✅
- [x] T041 GET /sessions/{sessionId}/messages endpoint in backend/src/api/session_messages.py ✅

## Phase 3.5: Integration & Middleware
- [x] T042 Authentication middleware with JWT validation in backend/src/middleware/auth.py ✅ IMPLEMENTED
- [x] T043 Redis session store implementation in backend/src/storage/redis_session_store.py ✅ IMPLEMENTED
- [x] T044 Error handling and logging middleware in backend/src/middleware/error_handler.py ✅
- [x] T045 CORS and security headers configuration in backend/src/middleware/security.py ✅
- [x] T046 Circuit breaker for external API calls in backend/src/lib/circuit_breaker.py ✅
- [x] T047 Graceful degradation service in backend/src/lib/graceful_degradation.py ✅

## Phase 3.6: Voice Integration
- [x] T048 Twilio webhook handler for voice input in backend/src/voice/twilio_handler.py ✅
- [x] T049 OpenAI Realtime integration for speech processing in backend/src/voice/openai_realtime.py ✅
- [x] T050 Voice response formatting service in backend/src/voice/voice_response.py ✅
- [x] T051 Audio processing utilities in backend/src/voice/audio_utils.py ✅
- [x] T052 Voice channel session continuity in backend/src/voice/session_continuity.py ✅

## Phase 3.6.1: Chat Integration (Multi-Channel Parity - Principle IV)
- [x] T052.1 [P] Chat interface service for natural language input in backend/src/chat/chat_interface.py ✅
- [x] T052.2 [P] Chat response formatting service matching voice quality in backend/src/chat/chat_response.py ✅
- [x] T052.3 [P] Chat session continuity and context preservation in backend/src/chat/chat_continuity.py ✅
- [x] T052.4 [P] Multi-channel routing service for seamless voice/chat handoffs in backend/src/services/channel_router.py ✅
- [x] T052.5 [P] Chat-specific error handling and user feedback in backend/src/chat/chat_errors.py ✅

## Phase 3.6.2: Localisation & Multi-Language Support (Integration Standard C6)
- [x] T052.6 [P] English language pack with logistics terminology in backend/src/localisation/en.py ✅ IMPLEMENTED
- [x] T052.7 [P] West African English accent handling for voice recognition in backend/src/localisation/accent_handler.py ✅ IMPLEMENTED
- [x] T052.8 [P] Culturally appropriate error messages for logistics domain in backend/src/localisation/cultural_messages.py ✅ IMPLEMENTED
- [x] T052.9 [P] Localisation middleware for dynamic language switching in backend/src/middleware/localisation.py ✅ IMPLEMENTED
- [x] T052.10 [P] Voice command grammar documentation with logistics examples in docs/voice-grammar.md ✅ IMPLEMENTED
- Verification: EFLP-215 marked Done on 2025-09-26 after validating localisation artefacts across code and docs.

## Phase 3.7: Polish
- [ ] T063 [P] Unit tests for container model validation in tests/unit/test_container_model.py ⚠️ NOT IMPLEMENTED
- [x] T064 [P] Unit tests for tracking service logic in tests/unit/test_track_service.py ✅
- [ ] T065 [P] Unit tests for session management in tests/unit/test_session_service.py ⚠️ NOT IMPLEMENTED
- [x] T066 [P] Unit tests for external API integration in tests/unit/test_external_api.py ✅
- [ ] T067 Performance tests for <5s response time in tests/performance/test_response_time.py ⚠️ NOT IMPLEMENTED
- [ ] T068 Load tests for 100 concurrent users in tests/performance/test_load.py ⚠️ NOT IMPLEMENTED
- [ ] T069 [P] Update API documentation with OpenAPI spec and multi-channel quickstart guides ⚠️ NOT IMPLEMENTED
- [✅] T070 [P] Add request/response logging for debugging ✅ COMPLETED
- [ ] T071 Remove code duplication and optimize imports (automated via pre-commit hooks) ⚠️ NOT IMPLEMENTED
- [ ] T072 Run manual testing scenarios from quickstart.md ⚠️ NOT IMPLEMENTEDi've editted

## Dependencies
- Setup (T001-T005) before all tests and implementation
- Contract tests (T006-T012) before API endpoints (T035-T041)
- Integration tests (T013-T017) before services (T027-T034)
- Models (T018-T025) before services (T027-T034)
- Services (T027-T034) before API endpoints (T035-T041)
- Core API (T035-T041) before voice integration (T048-T052)
- Core API (T035-T041) before chat integration (T052.1-T052.5)
- Voice integration (T048-T052) and chat integration (T052.1-T052.5) before multi-channel routing (T052.4)
- All implementation before localisation tasks (T052.6-T052.10)
- All implementation before polish (T063-T072)

## Parallel Example
```
# Launch contract tests together:
Task: "Contract test GET /health in tests/contract/test_health.py"
Task: "Contract test POST /track in tests/contract/test_track_post.py"
Task: "Contract test GET /containers/{id} in tests/contract/test_containers_get.py"
Task: "Contract test GET /containers/{id}/milestones in tests/contract/test_milestones_get.py"
Task: "Contract test GET /bl/{bl} in tests/contract/test_bl_get.py"
Task: "Contract test GET /sessions/{id} in tests/contract/test_sessions_get.py"
Task: "Contract test GET /sessions/{id}/messages in tests/contract/test_session_messages_get.py"
```

## Notes
- [P] tasks = different files, no dependencies
- Verify tests fail before implementing
- Commit after each task
- Avoid: vague tasks, same file conflicts
- Voice responses must be limited to 20 seconds maximum
- API response time <200ms target, <5s maximum
- Support 100 concurrent users, 10K containers/day
- Implement graceful degradation for external API failures
- **Constitutional Compliance**: Multi-channel architecture (voice + chat) required per Principle IV
- **Localisation Support**: English language pack with West African accent handling per Integration Standard C6
- **Health Monitoring**: T035 implements system health checks for reliability requirements (99.5% uptime)
- **Documentation**: T069 includes voice command grammar and multi-channel quickstart guides

## Task Generation Rules
*Applied during main() execution*

1. **From Contracts**:
   - Each contract file → contract test task [P]
   - Each endpoint → implementation task

2. **From Data Model**:
   - Each entity → model creation task [P]
   - Relationships → service layer tasks

3. **From User Stories**:
   - Each story → integration test [P]
   - Quickstart scenarios → validation tasks

4. **Ordering**:
   - Setup → Tests → Models → Services → Endpoints → Voice Integration → Chat Integration → Localisation → Polish
   - Dependencies block parallel execution
   - Multi-channel parity (voice + chat) required per Principle IV
   - Localisation support required per Integration Standard C6

## Validation Checklist
*GATE: Checked by main() before returning*

- [x] All contracts have corresponding tests ✅ IMPLEMENTED AND WORKING
- [x] JWT authentication middleware implemented ✅ IMPLEMENTED AND WORKING
- [x] All entities have model tasks ✅
- [x] All tests come before implementation ✅ IMPLEMENTED AND WORKING
- [x] Parallel tasks truly independent ✅
- [x] Each task specifies exact file path ✅
- [x] No task modifies same file as another [P] task ✅
- [x] Multi-channel parity: Voice + Chat integration tasks present (Principle IV compliance) ✅
- [ ] Localisation support tasks present (Integration Standard C6 compliance) ❌ NOT IMPLEMENTED
- [x] Health endpoint mapped to reliability requirements ✅
- [ ] Documentation tasks include voice grammar and multi-channel quickstarts ❌ NOT IMPLEMENTED
