# Contributing Guidelines

## Overview

This project uses the **Spec-Driven Development (SDD)** methodology with the `specify` system. All development follows a structured approach with clear phases, dependencies, and commit strategies.

## 🚀 Development Workflow

### 1. Feature Development Process

#### Phase 0: Specification
```bash
/specify "Natural language feature description"
```
- Creates new branch and spec file
- Defines requirements and constraints
- Establishes feature boundaries

#### Phase 1: Planning
```bash
/plan "Review and plan implementation approach"
```
- Creates `plan.md` with technical decisions
- Defines architecture and dependencies
- Generates data models and API contracts

#### Phase 2: Task Generation
```bash
/tasks "Generate implementation task list"
```
- Creates `tasks.md` with detailed task breakdown
- Organizes tasks into phases with dependencies
- Marks parallel tasks with [P] for concurrent development

#### Phase 3-5: Implementation → Testing → Polish
Follow the task dependencies and commit after each task completion.

### 2. Branch Naming Convention

```bash
# For new features (created by /specify command)
001-feature-name-description

# Current development branch
feature/20250925-efl-agent-assistant-prototype-spec-track--trace-vo
```

## 📝 Commit Strategy

### Commit Guidelines

#### **✅ One Task = One Commit**
- Each task in `tasks.md` gets its own commit
- Reference the task number in the commit message
- Use conventional commit format

#### **✅ Commit Message Format**
```bash
# Standard format
type(scope): description (T[task_number])

# Examples
feat: implement TrackService for container/BL tracking logic (T027)
test: add contract tests for container tracking endpoints (T008-T012)
fix: resolve rate limiting configuration issues (T046)
docs: update API documentation with OpenAPI specifications (T069)
```

#### **✅ Commit Types**
- `feat:` - New feature implementation
- `test:` - Test additions or modifications
- `fix:` - Bug fixes
- `docs:` - Documentation updates
- `refactor:` - Code restructuring without functionality changes
- `chore:` - Maintenance tasks (dependencies, tooling, etc.)

#### **✅ Task Dependencies**
```bash
# Commit order must respect dependencies
- Setup (T001-T005) before all tests and implementation
- Contract tests (T006-T012) before API endpoints (T035-T041)
- Integration tests (T013-T017) before services (T027-T034)
- Models (T018-T025) before services (T027-T034)
- Services (T027-T034) before API endpoints (T035-T041)
```

### Parallel Tasks ([P] Marking)
- Tasks marked with [P] can be developed concurrently
- Different files, no dependencies between them
- Example: Multiple contract tests can be implemented in parallel

## 🔀 Pull Request Structure

### Single PR Per Feature
- **One feature branch** → **One pull request**
- **Multiple commits** within the PR (one per task)
- **Squash merge** when approved

### PR Guidelines

#### **📋 PR Title Format**
```bash
feat: implement EFL Agent Assistant Track & Trace prototype
```

#### **📝 PR Description Structure**
```markdown
## Feature Overview
Implementation of EFL Agent Assistant with Track & Trace capabilities for container and shipment tracking.

## Implementation Summary

### ✅ Completed Tasks
- [x] T001-T005: Project setup and configuration
- [x] T006-T017: Contract and integration tests
- [x] T018-T026: Data models and schemas
- [x] T027-T034: Core services implementation
- [x] T035-T041: API endpoints

### 🔄 Remaining Tasks
- [ ] T048-T052: Voice integration
- [ ] T052.1-T052.5: Chat integration
- [ ] T063-T072: Polish and testing

## Technical Implementation

### Architecture
- **Backend**: FastAPI with Python 3.11
- **Database**: Redis for session management
- **External APIs**: EFL Terminal, CMA CGM, OpenAI, Twilio
- **Testing**: pytest with contract and integration tests

### Key Components
- Multi-channel session management
- Circuit breaker protection for external APIs
- Graceful degradation mechanisms
- Natural language processing for container tracking

## Testing Status
- ✅ Contract tests: All endpoints covered
- ✅ Integration tests: Multi-turn conversations, fallback logic
- 🔄 Performance tests: Pending (T067-T068)

## Breaking Changes
None - this is a new feature implementation.

## Related Issues
None
```

## 📊 Progress Tracking

### Update Progress
```bash
# Update agent context with current progress
SPECIFY_FEATURE=001-efl-agent-assistant-prototype-track-trace-vo .specify/scripts/bash/update-agent-context.sh

# Or update specific agent
SPECIFY_FEATURE=001-efl-agent-assistant-prototype-track-trace-vo .specify/scripts/bash/update-agent-context.sh claude
```

### Mark Tasks Complete
- Update `tasks.md` with [x] checkboxes
- Reference task numbers in commit messages
- Maintain task dependencies

### Session Continuity
- All progress is automatically saved in `logs/status_line.json`
- Agent context files maintain implementation state
- Use `.specify/scripts/bash/check-prerequisites.sh` to validate progress

## 🧪 Testing Guidelines

### Test-First Development (TDD)
1. **Write tests that fail** before implementing functionality
2. **Implement minimum code** to make tests pass
3. **Refactor** while maintaining test coverage

### Test Structure
```bash
tests/
├── contract/          # API contract validation (fail before implementation)
├── integration/       # End-to-end scenarios (fail before services)
├── unit/             # Individual component testing
└── performance/      # Load and performance testing
```

### Test Requirements
- **Minimum 80% coverage** for all new code
- **Contract tests** for all API endpoints
- **Integration tests** for critical user journeys
- **Performance tests** for response time and concurrency requirements

## 🔧 Code Quality

### Linting and Formatting
```bash
# Format code
black src/
isort src/

# Lint code
flake8 src/
ruff check src/

# Type checking (if applicable)
mypy src/
```

### Code Standards
- Follow PEP 8 for Python code
- Use type hints for all function signatures
- Write docstrings for all public methods
- Keep functions focused and single-purpose

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
```

## 🚨 Error Handling

### Structured Error Reporting
```python
# Use structured error responses
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
- All external API calls protected by circuit breakers
- Graceful degradation when services are unavailable
- Service health monitoring and automatic recovery

## 📚 Documentation

### Documentation Requirements
- **API Documentation**: OpenAPI specifications for all endpoints
- **Architecture Documentation**: System design and component interactions
- **Quickstart Guides**: User onboarding and usage examples
- **Development Guides**: Contributing and development setup

### Documentation Updates
- Update README files after major changes
- Maintain API documentation with each endpoint implementation
- Document architectural decisions in plan.md

## 🎯 Quality Gates

### Pre-Commit Checks
- All tests pass
- Code formatting applied
- Linting passes
- Type checking passes (if applicable)

### Pre-PR Checks
- All tasks for the feature are complete
- Contract tests validate API specifications
- Integration tests demonstrate end-to-end functionality
- Performance requirements are met

## 🔄 Review Process

### Reviewer Checklist
- [ ] Code follows project conventions
- [ ] Tests are comprehensive and passing
- [ ] Documentation is updated
- [ ] Performance requirements are met
- [ ] Security considerations addressed
- [ ] Error handling is robust
- [ ] Dependencies are respected

### Self-Review Checklist
- [ ] Task dependencies are satisfied
- [ ] Commit messages follow conventional format
- [ ] Tests fail before implementation (TDD)
- [ ] Progress is saved via specify system
- [ ] No breaking changes introduced

## 🤝 Collaboration

### Communication
- Use clear, descriptive commit messages
- Reference task numbers in all commits
- Update progress regularly via specify system
- Document architectural decisions

### Code Reviews
- Focus on code quality, not just functionality
- Suggest improvements for maintainability
- Ensure adherence to established patterns
- Validate security and performance considerations

## 📈 Metrics and Monitoring

### Success Metrics
- **Response Time**: <5s for chat, <20s for voice
- **Concurrent Users**: Support 100 simultaneous users
- **Container Tracking**: Handle 10K requests per day
- **Uptime**: 99.5% service availability
- **Test Coverage**: Minimum 80% for all components

### Monitoring
- Health checks for all external services
- Circuit breaker status monitoring
- Performance metrics collection
- Error rate and response time tracking

---

*These guidelines ensure consistent, high-quality development while maintaining the structured approach of the Spec-Driven Development methodology.*
