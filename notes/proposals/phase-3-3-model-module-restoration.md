# Phase 3.3 Model Module Restoration Plan

## Context
- T019–T025 are marked complete in `specs/001-efl-agent-assistant-prototype-track-trace-vo/tasks.md`, yet the repository only defines models inside `backend/src/models/container.py` and `backend/src/models/agent.py`.
- Linear EFLP-212 highlights missing standalone modules; EFLP-219 incorrectly claims completion, cascading to the master tracker (EFLP-217) and dependent testing tickets (EFLP-239, EFLP-243).
- Services, schemas, and tests currently import classes from the aggregated modules, so structural changes require coordinated import updates.

## Goals
1. Restore dedicated modules for each Phase 3.3 model task (T019–T025).
2. Realign repository state with Linear tickets and task tracker status.
3. Preserve functional parity and keep existing tests green while refactoring imports.

## Task Breakdown
1. **Revert Task Tracker Status**
   - Update `tasks.md` to set T019–T025 to `[ ]` before any code changes.
   - Run `.specify/scripts/bash/update-agent-context.sh` to broadcast the reverted progress state.

2. **Reconstruct Model Modules**
   - Create `backend/src/models/bill_of_lading.py`, `terminal_location.py`, `vessel_voyage.py`, `container_milestone.py`, `agent_session.py`, and `session_context.py`.
   - Move the corresponding class definitions out of `container.py` and `agent.py`, leaving only their native responsibilities.
   - Maintain existing type hints, validators, and docstrings; ensure each file exports the expected classes.

3. **Refactor Imports**
   - Update services, schemas, middleware, and tests to import from the new modules.
   - Use `rg` to confirm no references remain to the relocated classes in old files.

4. **Stabilise Tests**
   - Run targeted unit suites (`tests/unit/test_track_service.py`, `tests/unit/test_session_service.py`, others touching models).
   - Execute integration and contract tests if they rely on the refactored imports.
   - Address any fallout quickly to keep regression risk low.

5. **Documentation & Tracking**
   - Once tests pass, mark T019–T025 back to `[x]` and rerun the specify update script.
   - Prepare a comment for EFLP-212 summarising the fix and include evidence (file paths, test commands).
   - Reopen EFLP-219 (or update status per workflow) and adjust linked issues (EFLP-217, EFLP-239, EFLP-243) with accurate completion notes.

## Risks & Mitigations
- **Import Drift**: High touch count across services/tests. Mitigate with `rg --files-with-matches` sweeps and CI-equivalent test runs.
- **Parallel Work Collision**: Voice/chat teams may touch the same files; coordinate via Linear comments before merging.
- **Pydantic Refactor Dependency**: EFLP-247 scopes `backend/src/models/*.py`. Note in that ticket that new files exist so the upcoming refactor covers them.

## Testing Strategy
- `PYTEST_ADDOPTS='--no-cov' python -m pytest tests/unit/test_track_service.py tests/unit/test_session_service.py`
- `python -m pytest tests/unit/test_channel_router.py tests/unit/test_redis_session_store.py`
- Contract/integration smoke run if time allows: `python -m pytest tests/contract tests/integration --maxfail=1`

## Communication
- Log progress with `/implement` updates.
- Share refactor summary in EFLP-212 and link the commit.
- Update `logs/status_line.json` automatically via specify scripts to maintain continuity.
