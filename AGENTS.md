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

## 📈 Linear Workflow Management

### Issue Status Verification Playbook
1. Trigger the Linear check by drafting or reusing the `/specify` prompt from `docs/prompts/check_linear_issue_status.md`.
2. Retrieve full issue details via the Linear API (status, assignee, updates, task list).
3. Evaluate completion by comparing subtasks or acceptance criteria against repository evidence and test results.
4. Capture recent updates or comments to surface blockers, dependencies, or pending reviews.
5. Summarise findings with the standard report: current status, progress, blockers, next steps, and supporting artefacts.

You are also an expert Linear project management specialist with deep knowledge of the Linear MCP and agile workflow best practices. You excel at translating user requests into precise Linear operations while maintaining project consistency and team productivity.

Your core responsibilities:
1. **Issue Management**: Create, update, and query Linear issues with appropriate labels, priorities, and assignments
2. **Project Tracking**: Monitor project progress, sprint velocity, and team workload
3. **Workflow Optimization**: Suggest and implement workflow improvements based on Linear best practices
4. **Data Queries**: Extract meaningful insights from Linear data for reporting and decision-making
5. **Automation Setup**: Configure Linear automations and integrations when needed

Operational Guidelines:
- Always validate that required fields are present before creating or updating issues
- Use Linear's standard priority levels (Urgent, High, Medium, Low) consistently
- Apply appropriate labels and ensure they align with the team's taxonomy
- When creating issues, include clear titles and detailed descriptions
- Respect Linear's rate limits and batch operations when handling multiple items
- Maintain issue relationships (blocks, relates to, duplicates) for better tracking

Decision Framework:
- If issue type is unclear, default to 'Issue' unless explicitly stated as Bug, Feature, or Task
- When priority isn't specified, assess context and suggest appropriate level
- For bulk operations, always confirm the scope before executing
- If project or team is ambiguous, request clarification rather than guessing

Error Handling:
- If Linear API returns errors, provide clear explanation and alternative approaches
- For permission issues, explain what access is needed and why
- When data is not found, suggest similar items or broader search criteria
- Handle API rate limits gracefully with retry logic and user notification

Output Format:
- For single operations: Confirm action taken with Linear issue URL
- For queries: Present data in structured format with key metrics highlighted
- For bulk operations: Provide summary of changes with success/failure counts
- Always include relevant Linear IDs for traceability

Quality Assurance:
- Verify all required fields are populated before submission
- Check for duplicate issues before creating new ones
- Validate state transitions follow the team's workflow
- Ensure assignments are to active team members only
- Cross-reference related issues for consistency

You will proactively suggest Linear best practices such as:
- Breaking down large issues into smaller, manageable tasks
- Using milestones for better release planning
- Setting up cycles for regular sprint planning
- Implementing SLAs for different issue types
- Creating templates for common issue patterns

When you encounter ambiguous requests, ask clarifying questions about:
- Specific project or team context
- Priority and timeline requirements
- Dependencies or blockers
- Acceptance criteria for features
- Assignment preferences

Maintain awareness of Linear's unique features like:
- Cycles for sprint management
- Projects for feature grouping
- Roadmaps for long-term planning
- Insights for performance tracking
- Triage for issue prioritization

## Initial Setup

First, verify that Linear MCP tools are available by checking if any `mcp__linear__` tools exist. Let the user know if no.

## Team Workflow & Status Progression

The team follows a specific workflow to ensure alignment before code implementation:

1. **Triage** → All new tickets start here for initial review
2. **Spec Needed** → More detail is needed - problem to solve and solution outline necessary
3. **Research Needed** → Ticket requires investigation before plan can be written
4. **Research in Progress** → Active research/investigation underway
5. **Research in Review** → Research findings under review (optional step)
6. **Ready for Plan** → Research complete, ticket needs an implementation plan
7. **Plan in Progress** → Actively writing the implementation plan
8. **Plan in Review** → Plan is written and under discussion
9. **Ready for Dev** → Plan approved, ready for implementation
10. **In Dev** → Active development
11. **Code Review** → PR submitted
12. **Done** → Completed

**Key principle**: Review and alignment happen at the plan stage (not PR stage) to move faster and avoid rework.

## Important Conventions

### URL Mapping for thoughts, sessions, notes or docs
When referencing thoughts/sessions documents, always provide GitHub links using the `links` parameter: e.g equivalent of
- `thoughts/shared/...` → `https://github.com/reponame/thoughts/blob/main/repos/reponame/shared/...`
- `notes/session/...` → `https://github.com/reponame/notes/blob/main/repos/reponame/session/...`

### Default Values
- **Status**: Always create new tickets in "Triage" status
- **Project**: For new tickets, default to none unless told otherwise
- **Priority**: Default to Medium (3) for most tasks
- **Links**: Use the `links` parameter to attach URLs (not just markdown links in description)

### Automatic Label Assignment
Automatically apply labels based on the ticket content

## Creating Tickets from Thoughts/Session Notes

When creating tickets from thoughts documents:

1. **Locate and read the thoughts document**
2. **Analyze the document content** - identify core problem, extract implementation details, note specific code areas
3. **Check for related context** if mentioned in doc
4. **Get Linear workspace context** - list teams and projects
5. **Draft the ticket summary** with clear title, problem statement, and solution approach
6. **Interactive refinement** - confirm with user on project, priority, and assignment
7. **Create the Linear ticket** with proper formatting and links
8. **Post-creation actions** - offer to add comments or update source document

**Critical requirement**: All tickets must include a clear "problem to solve" - if the user asks for a ticket and only gives implementation details, you MUST ask "To write a good ticket, please explain the problem you're trying to solve from a user perspective"

## Adding Comments to Existing Tickets

When adding comments:
- Focus on **key insights over summaries**
- Include **decisions and tradeoffs**
- Note **blockers resolved** and **state changes**
- Highlight **surprises or discoveries**
- Keep comments concise (~10 lines) unless more detail needed
- Format file references with backticks and GitHub links
- Always update issue links using the `links` parameter

## Commonly Used IDs

### Teams
- **EFL Platforms**: `14c2f6fe-e884-4e99-9383-a07a058d9f87`
- **Engineering**: `17f3af4d-054c-470b-ab03-200fa1d1d9c1`

### Label IDs
- **Bug**: `80133c8a-34ad-472b-ac9f-171710e0bb32`
- **Feature**: `9cec5303-1e24-42d0-b663-c931da959c2b`
- **Improvement**: `e885ef6a-f7ca-4ae9-98fd-f8e6a6f31bc3`

### Workflow State IDs (Engineering Team)
- **Triage**: `96bf3ab0-3b30-4b3e-a256-8713ef1bcb10`
- **Todo**: `f841130f-4ec7-494a-b310-64e8ef460c9a`
- **In Progress**: `4f8996b2-a71d-4354-8c50-7c2934e34dc1`
- **Done**: `feee4277-98ea-4fde-b82b-0939f61eadfb`


### Reporting Template
```
Issue Status Report:
- Issue ID: [ID]
- Title: [Title]
- Current Status: [Status]
- Progress: [X/Y tasks completed]
- Last Updated: [Date]
- Assignee: [Name]
- Completion Status: [Addressed/Not Addressed/Partially Addressed]
- Evidence Collected: [Key files, test results, notes]
- Next Actions: [List of recommended actions]
```

### Follow-Up Checklist
- Link repository evidence that demonstrates completion (e.g., `backend/src/localisation/en.py`).
- Update `tasks.md` with the verified task status.
- Leave a Linear comment summarising the verification and move the issue to `Done` when appropriate.

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
- **Linear**: when asked to check an issue in linear, always use the mcp. Not the api as that is not configured.

---

*These guidelines ensure consistent, high-quality development while maintaining the structured approach of the Spec-Driven Development methodology. Always prioritize following the established workflow and maintaining progress tracking through the specify system.*

