# Development Quick Reference

## 🚀 Quick Start

### Environment Setup
```bash
# Set feature context
export SPECIFY_FEATURE=001-efl-agent-assistant-prototype-track-trace-vo

# Check prerequisites
.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks

# Install dependencies
cd backend && pip install -r requirements.txt

# Start development server
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```

### Update Progress
```bash
# Save current progress
SPECIFY_FEATURE=001-efl-agent-assistant-prototype-track-trace-vo .specify/scripts/bash/update-agent-context.sh

# Or update all agents
SPECIFY_FEATURE=001-efl-agent-assistant-prototype-track-trace-vo .specify/scripts/bash/update-agent-context.sh
```

## 📝 Commit Strategy

### Format
```bash
type(scope): description (T[task_number])

# Examples
feat: implement TrackService for container/BL tracking logic (T027)
test: add contract tests for health endpoint (T006)
fix: resolve circuit breaker timeout issues (T046)
```

### Types
- `feat:` - New features (T001-T072)
- `test:` - Test implementations
- `fix:` - Bug fixes
- `docs:` - Documentation
- `refactor:` - Code restructuring
- `chore:` - Maintenance

## 🔀 PR Structure

### Single PR Per Feature
- **One PR** for `001-efl-agent-assistant-prototype-track-trace-vo`
- **Multiple commits** (one per task)
- **Follow dependencies** in commit order

### PR Title
```bash
feat: implement EFL Agent Assistant Track & Trace prototype
```

## 🧪 Testing Workflow

### Test-First Development
```bash
# 1. Write failing test
def test_container_tracking():
    # This fails until implemented
    response = track_container("Track EFLU7896543")
    assert response.status_code == 200

# 2. Implement minimum code
def track_container(query: str):
    return {"status": "success"}  # Passes test

# 3. Refactor while maintaining tests
def track_container(query: str):
    # Improved implementation
    return process_tracking_query(query)
```

### Test Commands
```bash
# Run all tests
pytest tests/

# Run specific types
pytest tests/contract/     # API contracts
pytest tests/integration/  # End-to-end
pytest tests/unit/         # Components

# With coverage
pytest --cov=src tests/
```

## 📊 Progress Tracking

### Check Current Status
```bash
# Feature files available
.specify/scripts/bash/check-prerequisites.sh --json

# Current tasks
cat specs/001-efl-agent-assistant-prototype-track-trace-vo/tasks.md

# Session continuity
cat logs/status_line.json
```

### Mark Tasks Complete
- Update `tasks.md` with [x] checkboxes
- Reference task number in commit message
- Follow dependency order

## 🔧 Code Quality

### Formatting & Linting
```bash
# Format code
black src/
isort src/

# Lint code
flake8 src/
ruff check src/
```

### Standards
- Type hints for all functions
- Docstrings for public methods
- Single responsibility principle
- Comprehensive error handling

## 📁 Project Structure

```
src/
├── models/           # Pydantic data models
├── services/         # Business logic (T027-T034)
├── api/             # Endpoints (T035-T041)
├── schemas/         # Request/response models
├── middleware/      # FastAPI middleware
├── lib/             # Utilities (circuit breakers, etc.)
└── mcp/             # External API servers

tests/
├── contract/        # API validation
├── integration/     # End-to-end scenarios
├── unit/           # Component tests
└── performance/    # Load testing
```

## 🚨 Error Handling

### Structured Errors
```python
{
    "error": "CONTAINER_NOT_FOUND",
    "message": "Container with ID EFLU7896543 not found",
    "details": {"containerId": "EFLU7896543"},
    "timestamp": "2025-01-15T10:30:00Z"
}
```

### Circuit Breaker Protection
- All external APIs protected by circuit breakers
- Graceful degradation implemented
- Service health monitoring

## 🎯 Quality Gates

### Pre-Commit
- [ ] Tests pass
- [ ] Code formatted
- [ ] Linting passes
- [ ] Task dependencies satisfied
- [ ] Progress saved

### Pre-PR
- [ ] All feature tasks complete
- [ ] Contract tests validate APIs
- [ ] Integration tests pass
- [ ] Performance requirements met
- [ ] Documentation updated

---

*This quick reference provides essential development guidelines. For detailed information, see [CONTRIBUTING.md](CONTRIBUTING.md).*
