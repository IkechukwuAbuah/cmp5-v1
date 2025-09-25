# AI Agent Development Guidelines

## Overview

This file provides guidance for AI agents (Claude, Cursor, GitHub Copilot, etc.) working on the EFL Agent Assistant prototype. Follow these guidelines to maintain consistency, quality, and progress tracking.

## 🚀 Development Workflow

### 1. Feature Development Process

#### Always Use the Specify System
```bash
# For new features
/specify "Natural language feature description"

# For existing features (check progress)
/implement "Continue with current implementation"
/tasks "Show current task status"
/plan "Review implementation plan"
```

#### Progress Tracking
```bash
# Update agent context with current progress
SPECIFY_FEATURE=001-efl-agent-assistant-prototype-track-trace-vo .specify/scripts/bash/update-agent-context.sh

# Check prerequisites before starting work
.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
```

### 2. Task Management

#### Follow Task Dependencies
```bash
# From tasks.md - respect these dependencies
- Setup (T001-T005) before all tests and implementation
- Contract tests (T006-T012) before API endpoints (T035-T041)
- Integration tests (T013-T017) before services (T027-T034)
- Models (T018-T025) before services (T027-T034)
- Services (T027-T034) before API endpoints (T035-T041)
```

#### Mark Progress in Tasks
- Update `tasks.md` with [x] checkboxes for completed tasks
- Reference task numbers in all commit messages
- Maintain task order and dependencies

## 📝 Commit Strategy

### Commit Guidelines

#### **✅ One Task = One Commit**
- Each task gets its own commit
- Reference task number: `feat: implement [description] (T[task_number])`
- Atomic commits for easy rollback

#### **✅ Commit Message Format**
```bash
# Standard format
type(scope): description (T[task_number])

# Examples
feat: implement TrackService for container/BL tracking logic (T027)
test: add contract tests for health endpoint (T006)
fix: resolve circuit breaker timeout issues (T046)
docs: update API documentation with OpenAPI specs (T069)
refactor: optimize session management for performance (T028)
```

#### **✅ Commit Types**
- `feat:` - New feature implementation (T001-T072)
- `test:` - Test additions (contract, integration, unit)
- `fix:` - Bug fixes and issue resolution
- `docs:` - Documentation updates
- `refactor:` - Code restructuring without functionality changes
- `chore:` - Maintenance tasks (dependencies, tooling)

#### **✅ Parallel Tasks ([P] Marking)**
- Tasks marked with [P] can be developed concurrently
- Different files, no dependencies between them
- Example: Multiple contract tests can be implemented in parallel

## 🔀 Pull Request Guidelines

### Single PR Per Feature
- **One feature branch** → **One pull request**
- **Multiple commits** (one per task)
- **Logical commit grouping** by phases

### PR Title Format
```bash
feat: implement EFL Agent Assistant Track & Trace prototype
```

### PR Description Structure
```markdown
## Feature Overview
[Brief description of what was implemented]

## Implementation Summary

### ✅ Completed Tasks
- [x] T001-T005: Project setup and configuration
- [x] T006-T017: Contract and integration tests
- [x] T018-T026: Data models and schemas
- [x] T027-T034: Core services implementation

### 🔄 Remaining Tasks
- [ ] T048-T052: Voice integration
- [ ] T052.1-T052.5: Chat integration
- [ ] T063-T072: Polish and testing

## Technical Implementation
[Architecture decisions, key components, technical details]

## Testing Status
[Contract tests, integration tests, performance tests]

## Breaking Changes
[If any, list them clearly]
```

## 🧪 Testing Requirements

### Test-Driven Development (TDD)
1. **Write tests that fail** before implementing functionality
2. **Implement minimum code** to make tests pass
3. **Refactor** while maintaining test coverage

### Test Coverage Requirements
- **Contract Tests**: All API endpoints must have contract tests
- **Integration Tests**: Critical user journeys must be tested end-to-end
- **Unit Tests**: Individual components should have focused unit tests
- **Performance Tests**: Response time and concurrency requirements must be validated

### Test Implementation
```bash
# Write failing tests first
def test_container_tracking_natural_language():
    # This should fail until NLP is implemented
    response = track_container("Track EFLU7896543")
    assert response.status_code == 200

# Then implement the functionality
def track_container(query: str):
    # Implementation here
    return response
```

## 📊 Progress Tracking

### Update Progress
```bash
# Save current progress to agent context
SPECIFY_FEATURE=001-efl-agent-assistant-prototype-track-trace-vo .specify/scripts/bash/update-agent-context.sh

# Update specific agent
SPECIFY_FEATURE=001-efl-agent-assistant-prototype-track-trace-vo .specify/scripts/bash/update-agent-context.sh claude
```

### Check Current Status
```bash
# Check what files are available
.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks

# Review current tasks
cat specs/001-efl-agent-assistant-prototype-track-trace-vo/tasks.md

# Check session continuity
cat logs/status_line.json
```

### Session Continuity
- **Automatic Logging**: All progress saved in `logs/status_line.json`
- **Agent Context**: Updated via specify system
- **Task Tracking**: Maintained in `tasks.md` with checkboxes
- **Error Recovery**: Can resume from any point if interrupted

## 🔧 Code Quality Standards

### Linting and Formatting
```bash
# Apply formatting
black src/
isort src/

# Check for issues
flake8 src/
ruff check src/

# Type checking (if applicable)
mypy src/
```

### Code Standards
- **Type Hints**: Use for all function signatures
- **Docstrings**: Document all public methods
- **Single Responsibility**: Keep functions focused
- **Error Handling**: Comprehensive error handling with structured responses
- **Logging**: Use appropriate log levels for debugging and monitoring

### File Organization
```bash
src/
├── models/           # Pydantic data models
├── services/         # Business logic services
├── api/             # API endpoint handlers
├── schemas/         # Request/response schemas
├── middleware/      # FastAPI middleware
├── lib/             # Utility libraries
└── mcp/             # Model Context Protocol servers

tests/
├── contract/        # API contract validation
├── integration/     # End-to-end scenarios
├── unit/           # Individual component testing
└── performance/    # Load and performance testing
```

## 🚨 Error Handling Guidelines

### Structured Error Responses
```python
# Use consistent error format
{
    "error": "CONTAINER_NOT_FOUND",
    "message": "Container with ID EFLU7896543 not found",
    "details": {
        "containerId": "EFLU7896543",
        "agentId": "agent_123"
    },
    "timestamp": "2025-01-15T10:30:00Z"
}
```

### Circuit Breaker Protection
- All external API calls must be protected by circuit breakers
- Implement graceful degradation when services are unavailable
- Monitor service health and implement automatic recovery

## 📚 Documentation Standards

### Documentation Updates
- **README Files**: Update after major changes
- **API Documentation**: Maintain OpenAPI specifications
- **Architecture Documentation**: Document design decisions in plan.md
- **Quickstart Guides**: Provide user onboarding examples

### Documentation Format
- Use Markdown for all documentation
- Include code examples for API usage
- Document architectural decisions and trade-offs
- Maintain consistent formatting and structure

## 🎯 Quality Gates

### Pre-Commit Checks
- [ ] All tests pass
- [ ] Code formatting applied (black, isort)
- [ ] Linting passes (flake8)
- [ ] Type checking passes (if applicable)
- [ ] Task dependencies satisfied
- [ ] Progress saved via specify system

### Pre-PR Checks
- [ ] All tasks for the feature are complete
- [ ] Contract tests validate API specifications
- [ ] Integration tests demonstrate end-to-end functionality
- [ ] Performance requirements are met
- [ ] Documentation is updated

## 🔄 Session Management

### When Starting Work
1. **Check Session Data**: Review `logs/status_line.json` for previous context
2. **Update Agent Context**: Run the specify update script
3. **Review Current Tasks**: Check `tasks.md` for pending work
4. **Validate Prerequisites**: Use check-prerequisites script

### When Ending Work
1. **Update Task Progress**: Mark completed tasks in `tasks.md`
2. **Commit Changes**: Follow commit guidelines
3. **Update Agent Context**: Save progress via specify system
4. **Document Changes**: Update relevant documentation

### Error Recovery
- **Session Interruption**: Can resume from any point
- **Context Loss**: Agent context files maintain implementation state
- **Progress Tracking**: Tasks.md and git history provide recovery points

## 🤝 Collaboration Guidelines

### Communication
- **Clear Commit Messages**: Reference task numbers and describe changes
- **Progress Updates**: Regular updates via specify system
- **Issue Tracking**: Use conventional commits for tracking
- **Code Reviews**: Focus on quality, security, and maintainability

### Best Practices
- **Atomic Commits**: One task per commit
- **Test Coverage**: Maintain minimum 80% coverage
- **Error Handling**: Comprehensive error handling
- **Performance**: Meet response time requirements
- **Security**: Follow security best practices

---

*These guidelines ensure consistent, high-quality development while maintaining the structured approach of the Spec-Driven Development methodology. Always prioritize following the established workflow and maintaining progress tracking through the specify system.*
