# Quickstart: EFL Agent Assistant Track & Trace

## Overview

This quickstart guide provides setup instructions and validation scenarios for the EFL Agent Assistant Track & Trace prototype. The prototype enables clearing agents to track container and shipment status using natural language queries via both chat and voice interfaces.

## Prerequisites

### System Requirements
- Python 3.11+
- Node.js 18+ (for frontend development)
- Docker & Docker Compose (for containerized deployment)
- Redis (for session management and caching)
- 4GB RAM minimum, 8GB recommended
- 2 CPU cores minimum

### External API Access
- EFL Terminal API access (Terminus/TOS)
- CMA CGM Track & Trace API credentials
- Twilio account for voice integration
- OpenAI API key with GPT-4 and Realtime API access

## Quick Setup

### 1. Environment Configuration
```bash
# Clone the repository
git clone <repository-url>
cd efl-agent-assistant

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install backend dependencies
pip install -r backend/requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### 2. Environment Variables
Create `.env` file in the repository root:
```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_ORGANIZATION=your_org_id

# Voice Integration
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number

# External API Integration
EFL_TERMINAL_API_BASE_URL=https://api.efl.com/terminal/v1
EFL_TERMINAL_API_KEY=your_efl_api_key

CMA_CGM_API_BASE_URL=https://api.cma-cgm.com/track/v1
CMA_CGM_CLIENT_ID=your_cma_client_id
CMA_CGM_CLIENT_SECRET=your_cma_client_secret
CMA_CGM_BEHALF_OF=your_agent_identifier

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Application Settings
APP_ENV=development
LOG_LEVEL=INFO
SESSION_TIMEOUT_MINUTES=30
```

### 3. Database and Cache Setup
```bash
# Start Redis
docker run -d -p 6379:6379 redis:7-alpine

# For development, you can also use:
redis-server
```

### 4. Run the Application
```bash
# Start backend server
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload

# In another terminal, start frontend (if applicable)
cd frontend
npm run dev
```

### 5. Health Check
```bash
curl http://localhost:8000/api/v1/health
```
Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-25T10:00:00Z",
  "version": "1.0.0",
  "services": {
    "redis": "up",
    "openai": "up",
    "efl_terminal": "up",
    "cma_cgm": "up"
  }
}
```

## Voice Integration Setup

### Twilio Configuration
1. Purchase a phone number in Twilio Console
2. Configure webhook URL: `https://your-domain.com/api/v1/voice/webhook`
3. Set up voice response handling for both inbound and outbound calls

### OpenAI Realtime Configuration
1. Ensure your OpenAI account has Realtime API access
2. Configure voice model preferences in application settings
3. Set up audio processing parameters for optimal voice recognition

## Testing Scenarios

### Scenario 1: Basic Container Tracking (Chat)
**User Story**: Agent tracks a single container via chat interface

**Setup**:
- Container EFLU7896543 exists in EFL Terminal system
- Agent has permissions for this container
- Container status: "at_terminal", location: "Yard A1"

**Test Steps**:
1. Send chat message: "Track container EFLU7896543"
2. Verify response contains:
   - Container ID recognition
   - Current status: "at_terminal"
   - Location: "Yard A1"
   - Next step: "Awaiting exam booking"
3. Verify session context is maintained for follow-up questions

**Expected Response**:
```
Container EFLU7896543 is currently at EFL Terminal, Ikorodu.
Status: At terminal - Yard A1
Last milestone: Discharged from vessel Marco Polo
Next step: You may now book a customs examination.
```

### Scenario 2: Bill of Lading Tracking (Chat)
**User Story**: Agent tracks all containers under a BL number

**Setup**:
- BL ABC1234567 exists with 2 containers
- Agent has permissions for all containers
- Mixed data sources: one container in EFL, one still at sea

**Test Steps**:
1. Send chat message: "Track BL ABC1234567"
2. Verify response includes:
   - BL number recognition
   - List of associated containers
   - Mixed data sources (terminal + shipping line)
   - Fallback logic for containers not in terminal
3. Test follow-up: "What about the second container?"

**Expected Response**:
```
BL/shipment ABC1234567 corresponds to containers EFLU7896543 and EFLU7796767.

Container EFLU7896543:
- Current status: at_terminal - Yard A1
- Last milestone: Discharged from vessel
- Next step: Awaiting exam booking

Container EFLU7796767:
- Current status: in_transit
- Location: Aboard vessel CMA MONTEVIDEO
- ETA: Sept 27 at Lagos Port
```

### Scenario 3: Voice Interaction
**User Story**: Agent uses voice interface for container tracking

**Setup**:
- Twilio phone number configured
- Voice model tuned for logistics terminology
- Container EFLU7896543 available in system

**Test Steps**:
1. Call the configured Twilio number
2. Wait for greeting: "Welcome to EFL Agent Assistant. How can I help?"
3. Say: "I want to check the status of a shipment"
4. Respond to prompt: "Container EFLU7896543"
5. Verify voice response is clear and under 20 seconds
6. Test confirmation: "Did you say container EFLU7896543?"

**Expected Voice Flow**:
```
Assistant: "Welcome to EFL Agent Assistant. How can I help?"
Agent: "I want to check the status of a shipment"
Assistant: "Alright, I can help you with that. What is your container number?"
Agent: "EFLU7896543"
Assistant: "Container EFLU7896543 is currently at EFL Terminal, Ikorodu. Status: Cleared for exam. Would you like to hear the next step?"
Agent: "Yes"
Assistant: "Next step: You may now book a customs examination."
```

### Scenario 4: Fallback Logic
**User Story**: Container not found in terminal system, fallback to CMA CGM

**Setup**:
- Container TRANSIT123 exists only in CMA CGM system
- Not yet discharged at Lagos Port
- Agent has permissions for this container

**Test Steps**:
1. Send chat message: "Track container TRANSIT123"
2. Verify system:
   - Recognizes container not in EFL Terminal
   - Queries CMA CGM API
   - Returns shipping status information
   - Provides clear fallback messaging
3. Test error handling: "Sorry, I couldn't find a record for BL ABC1234567. Please check the number and try again."

**Expected Response**:
```
I couldn't find container TRANSIT123 in our terminal system. Let me check global shipping status...

Container TRANSIT123 is currently aboard vessel CMA MONTEVIDEO and is expected to discharge at Lagos Port on Sept 27. We'll notify you when it's transferred to EFL.

Current status: In transit via CMA MONTEVIDEO
Last update: Sept 25, 10:30 AM
ETA at Lagos Port: Sept 27
```

### Scenario 5: Multi-turn Conversation
**User Story**: Agent engages in follow-up conversation

**Setup**:
- Active session with container tracking context
- Container with multiple status changes

**Test Steps**:
1. Initial query: "Track BL ABC1234567"
2. Follow-up: "What does that mean?"
3. Another follow-up: "When will it be ready?"
4. Context switching: "Now track container XYZ789"
5. Return to previous: "What about the first one?"

**Expected Behavior**:
- Session context preserved across multiple turns
- Entity references maintained
- Clear conversation flow
- No repetition of already-provided information

### Scenario 6: Error Handling
**User Story**: System handles various error conditions gracefully

**Test Cases**:
1. **Invalid container number**: "Sorry, I couldn't find a record for container INVALID123. Please check the number and try again."
2. **No permissions**: "I'm sorry, but you don't have permission to access information for that container."
3. **API outage**: "Sorry, I'm unable to retrieve status right now. Please try again shortly or contact customer service."
4. **Ambiguous query**: "I found 3 containers matching your description. Which one would you like to track?"

## Performance Validation

### Response Time Tests
- **Chat responses**: < 5 seconds for 95% of requests
- **Voice responses**: < 1 second for speech recognition + < 5 seconds for full response
- **API calls**: < 200ms for individual API requests
- **Concurrent users**: Support 100 simultaneous sessions

### Load Testing
```bash
# Install load testing tools
pip install locust

# Run load test
locust -f load_test.py --host http://localhost:8000

# Expected results:
# - 100 concurrent users: < 5s response time
# - 1000 requests/minute: 99% success rate
```

## Security Validation

### Authentication Tests
1. Test JWT token validation
2. Verify session timeout (30 minutes)
3. Test role-based access control
4. Validate audit logging for all data access

### Data Protection Tests
1. Verify container data is filtered by agent permissions
2. Test GDPR compliance for personal data
3. Validate TLS encryption in transit
4. Check audit trails for compliance requirements

## Monitoring & Observability

### Health Monitoring
- Service health endpoints
- External API status monitoring
- Redis connection monitoring
- Voice pipeline health checks

### Logging Verification
- Session tracking logs
- API request/response logging
- Error tracking and alerting
- Performance metrics collection

## Troubleshooting

### Common Issues

**Voice Recognition Problems**:
- Check OpenAI Realtime API quotas
- Verify audio quality and network connectivity
- Review voice model training for logistics terminology

**API Integration Failures**:
- Verify API credentials and endpoints
- Check network connectivity and rate limits
- Review circuit breaker and retry logic
- Monitor fallback mechanism activation

**Session Management Issues**:
- Check Redis connectivity and memory usage
- Verify session timeout configuration
- Review session cleanup processes
- Monitor concurrent session limits

### Debug Commands
```bash
# Check service health
curl http://localhost:8000/api/v1/health

# View session information
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/sessions/{sessionId}

# Check API integration status
curl http://localhost:8000/api/v1/debug/integrations
```

## Success Criteria

✅ **Functional Requirements Met**:
- Natural language container tracking works via chat and voice
- Multi-turn conversations maintain context
- Fallback logic handles API failures gracefully
- Response times meet performance targets

✅ **Integration Requirements Met**:
- EFL Terminal API integration functional
- CMA CGM API integration with fallback logic
- Voice pipeline (OpenAI + Twilio) operational
- Session management across channels

✅ **Constitutional Requirements Met**:
- User-first natural language interface
- Real-time data accuracy with staleness indicators
- Test-driven development approach
- Multi-channel architecture
- Privacy and security compliance
- Graceful degradation
- Session management excellence

## Next Steps

1. **Production Deployment**: Set up CI/CD pipeline and production monitoring
2. **User Training**: Create agent training materials for voice and chat interfaces
3. **Feature Expansion**: Plan Phase 2 features based on pilot feedback
4. **Performance Optimization**: Implement caching and query optimization
5. **Advanced Analytics**: Add usage analytics and performance metrics

## Support

For technical support or questions about this prototype:
- Check the troubleshooting section above
- Review application logs for detailed error information
- Contact the development team for integration issues
- Monitor system health endpoints for operational status
