# Multi-Channel Routing Service

The Multi-Channel Routing Service enables seamless transitions between voice and chat channels while preserving conversation context and supporting concurrent multi-channel sessions.

## Overview

This service addresses Linear issue **EFLP-228** by implementing a comprehensive multi-channel routing system that allows users to switch between voice and chat channels without losing context or conversation history.

## Key Features

### ✅ Seamless Channel Switching
- **Voice to Chat**: Users can transition from voice calls to chat interface
- **Chat to Voice**: Users can switch from chat to voice calls
- **Context Preservation**: Full conversation context is maintained during switches
- **No Data Loss**: All conversation history and entities are preserved

### ✅ Concurrent Multi-Channel Sessions
- **Simultaneous Sessions**: Support for active voice and chat sessions simultaneously
- **Session Synchronization**: Context is synchronized between concurrent sessions
- **Primary Channel**: One channel designated as primary for context resolution
- **Automatic Cleanup**: Expired concurrent sessions are automatically cleaned up

### ✅ Channel Preference Detection & Learning
- **Behavioral Learning**: System learns user preferences based on channel switching patterns
- **Context-Aware**: Preferences can be context-specific (urgent, complex queries, etc.)
- **Intent-Based Detection**: Automatic channel recommendation based on query intent
- **Confidence Scoring**: Preference confidence increases with consistent behavior

### ✅ Advanced Context Management
- **Entity Preservation**: Container IDs, BL numbers, and other entities preserved across channels
- **Intent Continuity**: Current conversation intent maintained during switches
- **Action Tracking**: Pending actions preserved and synchronized
- **History Merging**: Intelligent merging of conversation histories from different channels

## API Endpoints

### Channel Switching

#### `POST /api/v1/channel-routing/switch`
Switch a session to a different channel while preserving context.

```json
{
  "session_id": "sess_123",
  "target_channel": "voice",
  "context_override": {
    "priority": "urgent"
  },
  "preserve_history": true
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "sess_123",
  "channel": "voice",
  "context": {
    "current_intent": "track_container",
    "recent_entities": [...]
  },
  "message": "Successfully switched to voice channel"
}
```

### Session Management

#### `POST /api/v1/channel-routing/merge-sessions`
Merge two sessions from different channels for the same user.

```json
{
  "primary_session_id": "sess_123",
  "secondary_session_id": "sess_456",
  "merge_strategy": "preserve_primary"
}
```

**Merge Strategies:**
- `preserve_primary`: Keep primary session context, add secondary entities
- `merge_context`: Intelligently merge all context elements
- `interleave`: Interleave based on timestamps

### Preference Management

#### `POST /api/v1/channel-routing/set-preference`
Set channel preference for an agent.

```json
{
  "preferred_channel": "voice",
  "context": "urgent"
}
```

#### `GET /api/v1/channel-routing/preference?context=urgent`
Get channel preference for an agent in a specific context.

**Response:**
```json
{
  "agent_id": "agent_123",
  "preferred_channel": "voice",
  "context": "urgent",
  "confidence": 0.85,
  "learned": true
}
```

### Analytics

#### `GET /api/v1/channel-routing/stats`
Get channel routing statistics for an agent.

```json
{
  "agent_id": "agent_123",
  "total_sessions": 45,
  "channel_distribution": {
    "voice": 20,
    "chat": 25
  },
  "switch_count": 12,
  "most_common_switch": "chat_to_voice",
  "average_session_duration": {
    "voice": 180,
    "chat": 420
  }
}
```

#### `GET /api/v1/channel-routing/session/{session_id}/channels`
Get channel switch history for a specific session.

## Service Architecture

### ChannelRouterService

The core service class that handles all multi-channel routing functionality:

```python
class ChannelRouterService:
    async def route_to_voice(session_id, agent_id, context_override=None)
    async def route_to_chat(session_id, agent_id, voice_context=None)
    async def create_concurrent_session(agent_id, primary_channel, secondary_channel)
    async def sync_concurrent_sessions(agent_id)
    async def detect_preferred_channel(agent_id, intent=None, context=None)
    async def learn_channel_preference(agent_id, chosen_channel, intent=None, context=None)
```

### Data Models

#### ChannelPreference
```python
@dataclass
class ChannelPreference:
    agent_id: str
    preferred_channel: ChannelType
    context: Optional[str] = None
    confidence: float = 0.5
    learned_from_behavior: bool = False
    last_updated: datetime = field(default_factory=datetime.utcnow)
    usage_count: int = 0
```

#### ConcurrentSession
```python
@dataclass
class ConcurrentSession:
    agent_id: str
    sessions: Dict[ChannelType, str] = field(default_factory=dict)
    primary_channel: Optional[ChannelType] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
```

## Integration Points

### Voice Integration
- **Voice Continuity Manager**: Integrates with existing voice session management
- **Twilio Handler**: Seamless handoff from voice calls to chat
- **Audio Processing**: Voice context extraction for chat handoff

### Chat Integration
- **Chat Continuity Manager**: Integrates with chat session management
- **Message History**: Chat context preservation for voice handoff
- **Entity Extraction**: Chat entities preserved in voice sessions

### Session Management
- **SessionService**: Core session management integration
- **Redis Storage**: Session persistence across channel switches
- **Context Synchronization**: Real-time context updates

## Usage Examples

### Basic Channel Switch (Voice to Chat)
```python
# User starts on voice, wants to switch to chat
channel_router = await ChannelRouterService().get_instance()

result = await channel_router.route_to_chat(
    session_id="voice_sess_123",
    agent_id="agent_456",
    voice_context={
        "current_intent": "track_container",
        "recent_entities": [{"type": "container", "id": "EFLU1234567"}]
    }
)
```

### Concurrent Sessions
```python
# Create concurrent voice and chat sessions
primary_id, secondary_id = await channel_router.create_concurrent_session(
    agent_id="agent_123",
    primary_channel=ChannelType.VOICE,
    secondary_channel=ChannelType.CHAT
)

# Sync context between sessions
await channel_router.sync_concurrent_sessions("agent_123")
```

### Preference Learning
```python
# Learn from user behavior
await channel_router.learn_channel_preference(
    agent_id="agent_123",
    chosen_channel=ChannelType.VOICE,
    intent="track_container",
    context="urgent"
)

# Get learned preference
preferred_channel = await channel_router.detect_preferred_channel(
    agent_id="agent_123",
    intent="track_container",
    context="urgent"
)
```

## Testing

### Unit Tests
- **ChannelRouterService**: Complete test coverage for all methods
- **Preference Learning**: Test confidence scoring and preference updates
- **Context Merging**: Test intelligent context merging strategies
- **Concurrent Sessions**: Test session synchronization and cleanup

### Integration Tests
- **API Endpoints**: Full test coverage for all REST endpoints
- **Authentication**: Test endpoint security and authorization
- **Error Handling**: Test error scenarios and edge cases
- **Performance**: Test concurrent session limits and performance

### Test Files
- `backend/tests/unit/test_channel_router.py`: Unit tests for service logic
- `backend/tests/integration/test_channel_routing_api.py`: API integration tests

## Configuration

### Environment Variables
- `ENABLE_CHANNEL_ROUTING`: Enable/disable channel routing (default: true)
- `MAX_CONCURRENT_SESSIONS`: Maximum concurrent sessions per agent (default: 2)
- `PREFERENCE_LEARNING_ENABLED`: Enable preference learning (default: true)
- `SESSION_SYNC_INTERVAL`: Interval for syncing concurrent sessions (default: 30s)

### Settings
```python
# Channel routing settings
CHANNEL_ROUTING_ENABLED = True
MAX_CONCURRENT_SESSIONS_PER_AGENT = 2
PREFERENCE_CONFIDENCE_THRESHOLD = 0.7
CONCURRENT_SESSION_TIMEOUT = 3600  # 1 hour
```

## Performance Considerations

### Memory Usage
- **Preference Storage**: In-memory storage with periodic persistence
- **Concurrent Sessions**: Limited per agent to prevent memory bloat
- **Context Caching**: Efficient context storage and retrieval

### Scalability
- **Stateless Design**: Service can be scaled horizontally
- **Redis Integration**: Shared state for multi-instance deployments
- **Background Tasks**: Cleanup and synchronization in background threads

### Monitoring
- **Metrics**: Channel switch frequency, preference accuracy, session duration
- **Logging**: Comprehensive logging for debugging and analytics
- **Health Checks**: Service health monitoring and alerting

## Security

### Authentication
- **JWT Tokens**: All endpoints require valid authentication
- **Agent Verification**: Sessions verified against agent ownership
- **Rate Limiting**: Prevent abuse of channel switching

### Data Protection
- **Context Encryption**: Sensitive context data encrypted at rest
- **Audit Logging**: All channel switches logged for compliance
- **Privacy**: User preferences stored securely with consent

## Future Enhancements

### Planned Features
- **Smart Channel Recommendations**: AI-powered channel suggestions
- **Voice-to-Text Integration**: Automatic transcription for chat handoff
- **Multi-Language Support**: Channel preferences per language
- **Advanced Analytics**: Deep insights into channel usage patterns

### Performance Optimizations
- **Caching Layer**: Redis caching for frequent operations
- **Batch Operations**: Bulk preference updates and session management
- **Async Processing**: Background processing for non-critical operations

## Troubleshooting

### Common Issues

#### Channel Switch Fails
- **Cause**: Session not found or expired
- **Solution**: Verify session exists and is active
- **Prevention**: Implement session validation before switching

#### Context Loss During Switch
- **Cause**: Context serialization/deserialization issues
- **Solution**: Check context format and required fields
- **Prevention**: Validate context structure before transfer

#### Preference Learning Not Working
- **Cause**: Learning disabled or insufficient data
- **Solution**: Enable learning and ensure sufficient usage data
- **Prevention**: Monitor preference confidence scores

### Debug Commands
```bash
# Check channel routing stats
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/channel-routing/stats

# Get session channel history
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/channel-routing/session/sess_123/channels

# Check agent preferences
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/channel-routing/preference
```

## Support

For issues or questions regarding the Multi-Channel Routing Service:

1. **Check Logs**: Review application logs for error details
2. **Run Tests**: Execute unit and integration tests
3. **Documentation**: Refer to API documentation and examples
4. **Monitoring**: Check service metrics and health status

---

**Status**: ✅ **COMPLETED** - All Linear issue requirements implemented and tested.

**Version**: 1.0.0  
**Last Updated**: December 2024  
**Maintainer**: EFL Development Team