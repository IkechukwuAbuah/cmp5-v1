# Research: Conversation Export Architecture for EFL Agent Assistant

## Executive Summary

This research analyzes the architecture requirements for implementing conversation export functionality to satisfy T052.3's acceptance criterion while maintaining existing session continuity work. The analysis reveals that a **hybrid approach** combining quick JSON export with background job processing is the optimal strategy to balance user needs, implementation effort, and compliance requirements.

## Current Architecture Context

### Session Management Foundation
- **SessionService**: Manages multi-channel sessions with Redis persistence (90-day TTL)
- **Redis Storage**: Serializes full session objects including conversation history
- **Message History**: Stored as `List[Message]` with timestamp, content, and metadata
- **Multi-Channel Continuity**: Voice ↔ Chat context preservation via ChannelRouterService
- **Current Capacity**: 50 messages per session limit, 10K containers/day scale target

### Existing Data Structures
```python
# Current session structure (from session_service.py)
AgentSession:
  - id: str
  - agentId: str
  - channel: ChannelType
  - conversationHistory: List[Message]
  - context: SessionContext
  - startTime/endTime: datetime
  - status: SessionStatus

Message:
  - id: str
  - type: "user" | "assistant"
  - content: str
  - timestamp: datetime
  - metadata: Dict[str, Any]
```

## Key Research Findings

### 1. Export Format Analysis

#### **JSON Export (Recommended Primary Format)**
**Pros:**
- Native format for existing session serialization
- Minimal transformation overhead
- Preserves full conversation structure
- Easy client-side processing
- Fastest to implement (leverages existing Redis serialization)

**Cons:**
- Large file sizes for long conversations
- Not human-readable for manual review
- No built-in PII redaction UI

**Implementation Effort:** Low (1-2 days)
**User Value:** High (immediate export capability)

#### **CSV Export (Secondary Format)**
**Pros:**
- Human-readable tabular format
- Easy to import into spreadsheets
- Good for audit trail analysis
- Built-in Excel compatibility

**Cons:**
- Loses conversation flow/timing
- Difficult to represent nested metadata
- Requires significant transformation logic

**Implementation Effort:** Medium (3-4 days)
**User Value:** Medium (audit-focused users)

#### **PDF Export (Future Enhancement)**
**Pros:**
- Professional document format
- Built-in formatting and styling
- Good for compliance reporting
- PII redaction can be visually applied

**Cons:**
- Heavy client-side processing requirements
- Complex implementation with report generation
- Large file sizes
- Requires PDF library dependencies

**Implementation Effort:** High (7-10 days)
**User Value:** High (formal reporting needs)

**Recommendation**: Start with JSON export (T052.3 closure), add CSV as T052.3.1, defer PDF to future iteration.

### 2. API Endpoint Strategy

#### **Option A: Synchronous Export Endpoint**
```http
GET /sessions/{sessionId}/export?format=json&includePII=false
```
**Pros:** Simple implementation, immediate response
**Cons:** Timeout risk with large transcripts, blocks API thread

#### **Option B: Asynchronous Job with Polling**
```http
POST /sessions/{sessionId}/export
{
  "format": "json",
  "includePII": false,
  "emailNotification": true
}

GET /export/{jobId}/status
GET /export/{jobId}/download
```
**Pros:** Handles large exports, non-blocking, email delivery
**Cons:** More complex implementation, job queue required

#### **Option C: Hybrid Approach (Recommended)**
- **Immediate JSON export** for small/medium sessions (<100 messages)
- **Background job** for large sessions (>100 messages)
- **Streaming response** for direct downloads

**Recommendation**: Hybrid approach - immediate export for most cases, background jobs for edge cases.

### 3. Performance & Scalability Strategy

#### **Large Transcript Handling**
- **Pagination**: Export API supports `?limit=100&offset=0` for incremental downloads
- **Streaming**: Use FastAPI `StreamingResponse` for memory-efficient large exports
- **Compression**: Automatic gzip compression for large JSON exports
- **Chunking**: Break voice transcripts into manageable segments

#### **Background Job Architecture**
```python
# Proposed job queue integration
class ExportJobService:
    async def queue_export(
        session_id: str,
        format: str,
        include_pii: bool,
        user_email: str = None
    ) -> str:
        job_id = f"export_{uuid.uuid4()}"
        # Queue background task
        return job_id

    async def get_job_status(job_id: str) -> Dict:
        # Check Redis job status
        pass

    async def download_export(job_id: str) -> FileResponse:
        # Stream completed export file
        pass
```

### 4. PII Sanitization & Security Strategy

#### **Data Classification Levels**
1. **Public Data**: Container IDs, timestamps, status information
2. **Internal Data**: Agent IDs, system metadata
3. **Sensitive PII**: User names, phone numbers, specific location details
4. **Highly Sensitive**: Authentication tokens, session IDs

#### **Redaction Rules**
```python
@dataclass
class RedactionRule:
    pattern: str          # Regex pattern to match
    replacement: str      # Replacement text
    classification: str   # PII level
    confidence: float     # Detection confidence

# Example rules
PII_RULES = [
    RedactionRule(
        pattern=r'\b\d{3}-\d{3}-\d{4}\b',  # Phone numbers
        replacement='[PHONE_REDACTED]',
        classification='sensitive_pii',
        confidence=0.95
    ),
    RedactionRule(
        pattern=r'\b[A-Za-z]+@.+\..+\b',   # Email addresses
        replacement='[EMAIL_REDACTED]',
        classification='sensitive_pii',
        confidence=0.90
    )
]
```

#### **Sanitization Pipeline**
1. **Pattern-based Detection**: Regex rules for common PII patterns
2. **Context-aware Analysis**: NLP analysis for contextual PII
3. **Classification Tagging**: Mark data by sensitivity level
4. **Selective Redaction**: Apply based on user permissions and export settings

### 5. Component Impact Analysis

#### **Minimal Changes Required**
- **SessionService**: Add export methods, maintain existing serialization
- **Redis Store**: No changes (already handles full session serialization)
- **API Layer**: Add export endpoints with proper authentication
- **Channel Router**: No changes (context preservation intact)

#### **New Components Needed**
- **ExportService**: Core export logic and format conversion
- **SanitizationService**: PII detection and redaction
- **JobQueueService**: Background job management (if needed)
- **NotificationService**: Email delivery for completed exports

### 6. Test Strategy

#### **Unit Tests**
- **ExportService**: Format conversion, PII detection, data transformation
- **SanitizationService**: Pattern matching, redaction accuracy
- **SessionService**: Export method integration

#### **Integration Tests**
- **End-to-End Export**: Full session export with PII redaction
- **Multi-Channel Continuity**: Export preserves voice/chat context
- **Performance**: Large session handling, memory usage validation

#### **Contract Tests**
- **Export API**: Request/response schemas, error handling
- **Authentication**: Agent permission validation
- **Data Integrity**: Verify no data loss during export

## Implementation Checklist

### **Phase 1: Core Export (T052.3 Closure - 3-4 days)**
- [ ] T052.3.1 ExportService with JSON format conversion
- [ ] T052.3.2 PII sanitization with configurable redaction levels
- [ ] T052.3.3 GET /sessions/{id}/export endpoint (synchronous)
- [ ] T052.3.4 Contract tests for export functionality
- [ ] T052.3.5 Integration tests for multi-channel export

### **Phase 2: Enhanced Export (T052.3.1 - 2-3 days)**
- [ ] T052.3.1.1 CSV format support
- [ ] T052.3.1.2 Background job queue for large exports
- [ ] T052.3.1.3 Email notification system
- [ ] T052.3.1.4 Performance tests for large transcripts

### **Phase 3: Advanced Features (Future - 5-7 days)**
- [ ] T052.3.2.1 PDF generation with formatting
- [ ] T052.3.2.2 Advanced PII detection (NLP-based)
- [ ] T052.3.2.3 Export scheduling and automation
- [ ] T052.3.2.4 Audit trail reporting

## Risk Assessment & Mitigation

### **Security Risks**
**Risk**: PII leakage in exported conversations
**Mitigation**: Multi-layer redaction with configurable sensitivity levels, audit logging of all exports, agent permission validation

**Risk**: Unauthorized export access
**Mitigation**: JWT authentication on all export endpoints, session ownership verification, rate limiting

### **Performance Risks**
**Risk**: Large export blocking API threads
**Mitigation**: Hybrid sync/async approach, streaming responses, background job processing for large exports

**Risk**: Memory exhaustion with large sessions
**Mitigation**: Pagination support, streaming responses, memory-efficient JSON serialization

### **Operational Risks**
**Risk**: Export job queue failures
**Mitigation**: Redis-based job persistence, retry logic, monitoring and alerting

**Risk**: Storage exhaustion from export files
**Mitigation**: Automatic cleanup of temporary export files, size limits, compression

## Relative Impact Analysis

### **Quick JSON Export (T052.3 Closure)**
**Effort**: 3-4 days
**Value**: ✅ Closes T052.3 acceptance criterion
**Risk**: Low (leverages existing architecture)
**User Benefit**: Immediate export capability for compliance/audit needs

### **Full-Featured Export Package**
**Effort**: 10-14 days
**Value**: ✅ Enhanced user experience with multiple formats
**Risk**: Medium (new components, background jobs)
**User Benefit**: Professional exports, large session handling, automated delivery

### **Recommendation**
Implement **quick JSON export** to close T052.3, then manage enhanced export features through the dedicated **ENG-18** Linear issue. This approach:
- Satisfies acceptance criterion without delay
- Maintains existing session continuity work
- Provides foundation for future enhancements
- Minimizes risk to current implementation

## Linear Issue Mapping

### ENG-18 <-> EFLP-227 Alignment
Linear issue **ENG-18 - Enhanced conversation export with multiple formats and background** now owns the extended export scope that was previously described here as a follow-up to T052.3 (**EFLP-227: Chat Session Continuity**).

```
Scope handshake:

- EFLP-227 (T052.3) -> JSON export foundation + session continuity guarantees (complete)
- ENG-18 -> CSV format, background job orchestration, email notifications, advanced PII guardrails, large-session performance validation

Linkage notes:
- ENG-18 must preserve the continuity guarantees delivered in EFLP-227
- Progress updates for export enhancements should reference both ENG-18 and T052.3 artifacts
- When ENG-18 milestones land, capture evidence in this document and tasks.md under T052.3 annotations
```

## Conclusion

The proposed architecture enables T052.3 closure through a focused JSON export implementation while establishing a foundation for enhanced export capabilities. The hybrid approach balances immediate user needs with long-term scalability requirements, ensuring compliance with audit trail and PII protection standards while maintaining the robust session continuity already implemented.

**Next Steps**:
1. Implement core JSON export (T052.3 closure)
2. Track enhanced export progress via ENG-18 alongside EFLP-227 records
3. Monitor usage patterns to inform format prioritization
4. Consider PDF export in future iteration based on user feedback
