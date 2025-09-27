<!-- Sync Impact Report
Version change: None → 1.0.0 (Initial creation)
Modified principles: Initial constitution creation
Added sections: All sections newly created
  - Core Principles (7 principles focused on logistics AI assistant)
  - Integration Standards (External APIs, Multi-Language Support)
  - Development Workflow (SDD, Quality Gates, Documentation)
  - Governance (Amendment procedures and compliance)
Removed sections: None
Templates requiring updates:
  ✅ plan-template.md - Updated constitution version reference to v1.0.0
  ✅ spec-template.md - No changes needed (generic template)
  ✅ tasks-template.md - No changes needed (aligns with TDD principle)
  ✅ Command templates - None exist in project
Follow-up TODOs:
  - RATIFICATION_DATE: Awaiting project kickoff confirmation
-->

# EFL Agent Assistant Constitution

## Core Principles

### I. User-First Natural Language Interface
Every feature MUST support both voice and text input equally well. Natural language understanding is paramount - agents speak logistics terminology, not technical jargon. Responses must be concise for voice channels (under 30 seconds when spoken) while remaining informative.

**Rationale**: Clearing agents work in high-pressure environments where hands-free voice interaction is often necessary. Technical complexity must never leak into user interactions.

### II. Real-Time Data Accuracy
The system MUST provide current, accurate container and shipment status. Data staleness must be clearly indicated. When multiple data sources exist (EFL Terminal, CMA CGM, etc.), the most recent and authoritative source takes precedence.

**Rationale**: Clearing agents make time-sensitive decisions based on container status. Outdated or incorrect information can lead to costly delays and regulatory issues.

### III. Test-Driven Development (NON-NEGOTIABLE)
TDD is mandatory for all feature development. The cycle is strictly: Write failing tests → Get approval → Implement to pass → Refactor while green. Every API integration, data transformation, and business logic rule MUST have comprehensive test coverage (minimum 80%).

**Rationale**: The logistics domain has complex business rules and regulatory requirements. Without rigorous testing, edge cases in container tracking could cause operational failures.

### IV. Multi-Channel Architecture
Features MUST work seamlessly across chat interfaces, voice assistants, and API endpoints. Channel-specific optimizations (e.g., voice-friendly formatting) must not compromise data accuracy or completeness.

**Rationale**: Agents work from offices, warehouses, ports, and mobile. The assistant must adapt to their context without requiring different implementations.

### V. Privacy & Security First
All agent data, container information, and business relationships MUST be protected with role-based access control. Personal data handling must comply with applicable regulations. API keys and credentials must never be exposed in logs or responses.

**Rationale**: Logistics data contains sensitive commercial information. Security breaches could compromise competitive advantages and violate data protection laws.

### VI. Graceful Degradation
When external APIs (CMA CGM, shipping lines) are unavailable, the system MUST fall back to cached data with clear staleness indicators. Core Track & Trace functionality must remain operational even with partial system failures.

**Rationale**: Port operations run 24/7. The assistant must provide value even when upstream systems experience outages.

### VII. Session Management Excellence
Every interaction must maintain proper session context, track conversation state across channels, and provide seamless handoffs between voice and text. Session logs must capture full context for debugging and compliance.

**Rationale**: Complex container queries often require multiple turns. Agents shouldn't repeat information already provided in the conversation.

## Integration Standards

### External API Requirements
- All external API integrations (CMA CGM, DCSA-compliant endpoints) must implement retry logic with exponential backoff
- Response caching must respect API rate limits and data freshness requirements
- API responses must be validated against expected schemas before processing
- Fallback data sources must be clearly documented with precedence rules

### Multi-Language Support
- Core responses must support English as primary language
- Logistics terminology must be consistently translated
- Voice recognition must handle accented English common in West African logistics
- Error messages must be culturally appropriate and actionable

## Development Workflow

### Specification-Driven Development
- Every feature starts with a specification using `/specify` command
- Specifications must include clear acceptance criteria in logistics terms
- Technical clarifications must be resolved before implementation begins
- User stories must reflect actual agent workflows

### Quality Gates
- No code merges without passing all tests (unit, integration, contract)
- Voice interface changes require manual voice testing confirmation
- Performance benchmarks: API responses < 200ms, voice responses < 1 second
- Session tracking must be verified for every new conversation flow

### Documentation Requirements
- API contracts must be documented before implementation
- Voice command grammar must be documented with examples
- Error scenarios must include agent-friendly explanations
- Quickstart guides must cover both chat and voice setup

## Governance

The Constitution supersedes all other development practices. Any deviation requires:
1. Documented justification referencing specific operational constraints
2. Approval from Product & Research pair
3. Migration plan to return to constitutional compliance
4. Update to this constitution if the deviation reveals a principle gap

All pull requests must include a Constitution Compliance checklist. Code reviews must verify adherence to all principles. Complexity that violates principles must be justified in technical design documents.

For runtime development guidance, developers should reference the project CLAUDE.md file for session management patterns and visual communication standards.

**Version**: 1.0.0 | **Ratified**: TODO(RATIFICATION_DATE): Awaiting project kickoff confirmation | **Last Amended**: 2025-01-25