# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Claude Code session management project with sophisticated logging and orchestration capabilities. The repository contains session logs and configuration for enhanced session management with "The SMD" output style.

## Output Style Configuration

This project uses **The SMD** output style, configured in `.claude/settings.local.json`. This is a sophisticated Session Manager output style that emphasizes:
- Visual-first communication with tables and diagrams
- Systematic session tracking and orchestration
- 3-layer response architecture (Session Governance, Decision Intelligence, Execution & Tracking)
- WAT (West Africa Time) timestamp signatures

## Key Project Components

### Session Logging System
- **Location**: `logs/status_line.json`
- Contains detailed session tracking data including timestamps, costs, API usage, and status line outputs
- Tracks model usage (Sonnet 4, Opus 4.1)
- Records session IDs and transcript paths

### Cursor Rules Integration
- **Location**: `.cursor/rules/session-manager.mdc`
- Contains detailed session manager orchestration rules
- Defines delegation strategies for different task complexities
- Includes SDD/TDD workflow integration patterns

## Session Management Architecture

### Delegation Decision Matrix
When working on tasks in this codebase, use this complexity assessment:

| Task Complexity | Routing Strategy | Tool Selection |
|----------------|-----------------|----------------|
| Simple (<50 lines, single file) | Direct implementation | Claude Code |
| Medium (multiple files, architectural) | Strategic orchestration | Subagents + SDD/TDD |
| Complex (technical expertise) | Tactical delegation | Gemini/Cursor/Codex CLI |
| Massive (>50 files, large context) | Large context analysis | Gemini CLI |

### Tool Preference Hierarchy

**For Analysis & Discovery:**
1. Gemini CLI - Large-scale analysis (50+ files)
2. Subagent - Specialized domain analysis
3. Direct Claude - Focused file analysis

**For Implementation:**
1. Codex CLI - Autonomous implementation
2. Cursor CLI - Interactive development
3. Subagent - Specialized modifications
4. Direct Claude - Simple edits

## Development Workflow

### Session Governance Requirements
Every session should track:
- Session ID and phase (discovery/planning/execution)
- Context usage and token limits
- Tool validation status
- Active delegation stack

### Response Pattern
When responding to requests in this project, follow this structure:
1. Session state header with governance info
2. Decision matrix showing routing logic
3. Action plan with visual workflow
4. Tool selection justification
5. Execution steps with status tracking
6. Artifacts summary
7. Next session handoff instructions

### Visual Communication Standards
- Use Mermaid diagrams for workflows
- Include tables for all comparisons
- Use Unicode status symbols: ✓ ⚠ ✗ ● ○
- Format all code and commands in code blocks
- Include progress bars for multi-step processes

## SDD/TDD Integration

The project supports Spec-Driven Development and Test-Driven Development workflows:

### SDD Phases
1. `/specify` - Define requirements with testable criteria
2. `/plan` - Technical approach and architecture
3. `/tasks` - Break down into ordered implementation steps
4. `/implement` - Execute with TDD enforcement

### TDD Guard Integration
- Enforces test-first development
- Blocks implementation without failing tests
- Integrates with specification-derived test requirements

## Session Logging Protocol

### Session Entry Structure
```json
{
  "session_id": "uuid",
  "timestamp": "ISO-8601",
  "model": "model-name",
  "cost": {
    "total_cost_usd": 0.0,
    "total_api_duration_ms": 0
  },
  "status_line_output": "formatted-status"
}
```

### Key Metrics Tracked
- Total cost in USD
- API duration in milliseconds
- Lines added/removed
- Token usage status

## Important Notes

1. **WAT Timestamp**: End every response with current West Africa Time timestamp
2. **Visual First**: Include at least one table or diagram per response
3. **Session Hygiene**: Track all file operations with timestamps
4. **Logic Review**: Run critical reasoning pass before closing updates
5. **Tool Validation**: Always validate recommended tools before use

## Error Handling

Use structured error reporting:
```
┌─ ERROR ENCOUNTERED ─────────────────┐
│ Error: [message]                     │
│ Context: [what-was-attempted]        │
│ Fallback: [alternative-approach]     │
│ Prevention: [future-avoidance]       │
└─────────────────────────────────────┘
```

## Session Continuity
us t
When resuming work:
1. Check `logs/status_line.json` for previous session context
2. Review cost metrics and token usage
3. Identify incomplete tasks from previous sessions
4. Maintain tool selection reasoning for consistency

This project emphasizes systematic session management, visual communication, and sophisticated orchestration of AI tools and workflows.