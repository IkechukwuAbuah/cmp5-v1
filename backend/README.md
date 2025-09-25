# EFL Agent Assistant - Backend

A FastAPI-based backend for the EFL Agent Assistant that provides container tracking capabilities with voice and chat support.

## Features

- **Container Tracking**: Natural language queries for container status and location
- **Multi-Channel Support**: Voice and chat interfaces with session continuity
- **External API Integration**: EFL Terminal and CMA CGM API integration with circuit breakers
- **Graceful Degradation**: Fallback mechanisms when external services are unavailable
- **Real-time Health Monitoring**: Comprehensive health checks for all services
- **Session Management**: Multi-turn conversations with context preservation
- **Rate Limiting**: Built-in rate limiting to prevent abuse
- **Authentication & Authorization**: Role-based access control for agents

## Architecture

### Core Components

- **API Endpoints**: RESTful endpoints for tracking, containers, sessions, and health checks
- **Data Models**: Pydantic models for containers, agents, sessions, and related entities
- **Services**: Business logic for tracking, session management, and external API integration
- **Middleware**: Error handling, security, and rate limiting middleware
- **Circuit Breakers**: Protection against external API failures
- **Graceful Degradation**: Fallback mechanisms for service resilience

### Technology Stack

- **Framework**: FastAPI 0.104.1
- **Language**: Python 3.11
- **Authentication**: JWT tokens with role-based access
- **Database**: Redis for session management
- **External APIs**: EFL Terminal, CMA CGM, OpenAI, Twilio
- **Testing**: pytest with contract and integration tests

## API Endpoints

### Health Check
- `GET /api/v1/health` - System health status and service monitoring

### Tracking
- `POST /api/v1/track` - Natural language container tracking queries

### Containers
- `GET /api/v1/containers/{containerId}` - Container details and status
- `GET /api/v1/containers/{containerId}/milestones` - Container milestone history

### Bill of Lading
- `GET /api/v1/bl/{blNumber}` - Bill of lading details and associated containers

### Sessions
- `GET /api/v1/sessions/{sessionId}` - Session information and context
- `GET /api/v1/sessions/{sessionId}/messages` - Session message history

## Setup and Installation

1. **Install Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Environment Configuration**
   Copy `.env.example` to `.env` and configure:
   ```bash
   # External API Keys
   EFL_TERMINAL_API_KEY=your_efl_api_key
   CMA_CGM_API_KEY=your_cma_cgm_api_key
   OPENAI_API_KEY=your_openai_api_key
   TWILIO_ACCOUNT_SID=your_twilio_sid
   TWILIO_AUTH_TOKEN=your_twilio_token

   # Redis Configuration
   REDIS_URL=redis://localhost:6379/0

   # Security
   SECRET_KEY=your_secret_key
   ```

3. **Run the Application**
   ```bash
   python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## Testing

Run the test suite:
```bash
pytest tests/ -v
```

Run contract tests to validate API specifications:
```bash
pytest tests/contract/ -v
```

Run integration tests for end-to-end scenarios:
```bash
pytest tests/integration/ -v
```

## Performance Requirements

- **Response Time**: < 5 seconds for chat, < 20 seconds for voice
- **Concurrent Users**: Support for 100 concurrent users
- **Container Tracking**: Handle 10K container requests per day
- **Uptime**: 99.5% service availability with graceful degradation

## Monitoring and Observability

- Health checks provide real-time service status
- Circuit breakers monitor external API availability
- Request/response logging for debugging
- Performance metrics and error tracking

## Security

- JWT-based authentication
- Role-based authorization
- Rate limiting per IP
- Security headers (CORS, XSS protection, etc.)
- TLS encryption in production

## Development

### Adding New Features

1. Update data models in `src/models/`
2. Create API schemas in `src/schemas/`
3. Implement endpoints in `src/api/`
4. Add contract tests in `tests/contract/`
5. Add integration tests in `tests/integration/`

### Code Style

- Follow PEP 8 conventions
- Use Black for code formatting
- Use isort for import sorting
- Use flake8 for linting

## Production Deployment

1. Set `ENVIRONMENT=production` in environment variables
2. Configure Redis for session persistence
3. Set up monitoring and alerting
4. Configure reverse proxy (nginx) for SSL termination
5. Set up log aggregation and analysis

## Contributing

1. Follow the existing code structure and patterns
2. Write comprehensive tests for new features
3. Update documentation for API changes
4. Ensure all contract tests pass
5. Follow TDD principles for new implementations
