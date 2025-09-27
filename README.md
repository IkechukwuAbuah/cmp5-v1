# EFL Agent Assistant Prototype

A comprehensive AI-powered container tracking system for EFL clearing agents, featuring multi-channel support (voice + chat) with natural language processing and real-time integration to EFL Terminal and CMA CGM APIs.

## 🚀 Overview

This project implements an intelligent assistant for logistics professionals that enables natural language queries for container and shipment tracking through both voice and chat interfaces. Built using modern web technologies with robust error handling, circuit breakers, and graceful degradation mechanisms.

## 📋 Features

### Core Functionality
- **Natural Language Tracking**: Query container status using everyday language
- **Multi-Channel Interface**: Seamless voice and chat support with session continuity
- **Real-time Data Integration**: Live data from EFL Terminal and CMA CGM APIs
- **Intelligent Fallbacks**: Graceful degradation when external services are unavailable
- **Session Management**: Multi-turn conversations with context preservation
- **Agent Authentication**: Role-based access control and permissions

### Technical Capabilities
- **Response Time**: <5 seconds for chat, <20 seconds for voice
- **Concurrent Users**: Support for 100 simultaneous users
- **Container Volume**: Handle 10K tracking requests per day
- **Availability**: 99.5% uptime with comprehensive health monitoring
- **Security**: TLS 1.3+, GDPR compliance, audit logging

## 🏗️ Architecture

### Technology Stack
- **Backend**: FastAPI (Python 3.11)
- **Frontend**: React/TypeScript (planned)
- **Database**: Redis for session management and caching
- **External APIs**: EFL Terminal, CMA CGM, OpenAI Realtime, Twilio
- **Testing**: pytest with comprehensive contract and integration tests

### System Components
- **API Layer**: RESTful endpoints for tracking, containers, sessions, health checks
- **Services Layer**: Business logic for tracking, session management, external API integration
- **Data Models**: Pydantic models for type safety and validation
- **Middleware**: Security, error handling, rate limiting, CORS
- **MCP Servers**: Model Context Protocol integration for external APIs
- **Circuit Breakers**: Protection against external API failures

## 📁 Project Structure

```
cmp5-v1/
├── backend/                    # FastAPI backend implementation
│   ├── src/
│   │   ├── models/            # Pydantic data models
│   │   ├── services/          # Business logic services
│   │   ├── api/              # API endpoint handlers
│   │   ├── schemas/          # Request/response schemas
│   │   ├── middleware/       # FastAPI middleware
│   │   ├── lib/              # Utility libraries
│   │   └── mcp/              # External API integration servers
│   └── tests/                # Comprehensive test suite
├── specs/                    # Feature specifications and planning
│   └── 001-efl-agent-assistant-prototype-track-trace-vo/
│       ├── plan.md           # Implementation plan and architecture
│       ├── tasks.md          # Detailed task breakdown
│       ├── data-model.md     # Data model specifications
│       ├── contracts/        # API contract definitions
│       └── research.md       # Research findings and decisions
├── logs/                     # Session tracking and monitoring
└── docs/                     # Documentation and guides
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Redis server
- Git

### Setup
```bash
# Clone the repository
git clone <repository-url>
cd cmp5-v1

# Set up feature context
export SPECIFY_FEATURE=001-efl-agent-assistant-prototype-track-trace-vo

# Install dependencies
cd backend
pip install -r requirements.txt

# Run the application
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### API Usage
```bash
# Health check
curl http://localhost:8000/api/v1/health

# Track container (natural language)
curl -X POST http://localhost:8000/api/v1/track \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Track container EFLU7896543",
    "channel": "chat",
    "agentId": "agent_123"
  }'
```

## 📊 Development Status

### ✅ Completed Phases
- **Phase 1**: Specification and planning complete
- **Phase 2**: Task generation and breakdown complete
- **Phase 3.1**: Setup and configuration complete
- **Phase 3.2**: Test-driven development (contract + integration tests) complete
- **Phase 3.3**: Core implementation (models + services) complete
- **Phase 3.4**: API endpoints implementation complete

### 🔄 Current Phase
- **Phase 3.5**: Voice integration (in progress)
- **Phase 3.6**: Chat integration and multi-channel routing
- **Phase 3.7**: Polish, testing, and performance validation

### 📈 Progress Tracking
- **Tasks Completed**: T001-T041 (41/72 tasks)
- **Test Coverage**: Comprehensive contract and integration tests
- **API Endpoints**: All core endpoints implemented and tested
- **External Integration**: Circuit breakers and graceful degradation implemented

## 🧪 Testing

The project follows **Test-Driven Development (TDD)** principles:

### Test Structure
```bash
tests/
├── contract/          # API contract validation
├── integration/       # End-to-end scenarios
├── unit/             # Individual component testing
└── performance/      # Load and performance testing
```

### Running Tests
```bash
# Run all tests
pytest tests/

# Run specific test types
pytest tests/contract/     # Contract tests
pytest tests/integration/  # Integration tests
pytest tests/unit/         # Unit tests

# Run with coverage
pytest --cov=src tests/
```

## 📝 Contributing

This project uses the **Spec-Driven Development (SDD)** methodology. Please read the [CONTRIBUTING.md](CONTRIBUTING.md) file for detailed guidelines.

### Key Development Guidelines

#### **Commit Strategy**
- **One task = one commit** (reference task number in commit message)
- **Conventional commits** format: `feat: description (T[task_number])`
- **Atomic commits** for easy rollback and review

#### **PR Structure**
- **Single PR per feature** with multiple commits
- **Follow task dependencies** (setup → tests → implementation → endpoints)
- **Squash merge** when approved

#### **Progress Tracking**
- Update `tasks.md` with [x] checkboxes for completed tasks
- Use specify system to save progress: `.specify/scripts/bash/update-agent-context.sh`
- Maintain session continuity through structured logging

## 🏛️ Constitutional Compliance

This implementation adheres to all seven constitutional principles:

✅ **User-First Natural Language Interface**: Natural language processing for logistics terminology
✅ **Real-Time Data Accuracy**: Current container status with clear staleness indicators
✅ **Test-Driven Development**: Comprehensive test coverage (minimum 80%)
✅ **Multi-Channel Architecture**: Seamless voice and chat support with session continuity
✅ **Privacy & Security First**: Role-based access control with audit logging
✅ **Graceful Degradation**: Fallback mechanisms for external API failures
✅ **Session Management Excellence**: Multi-turn conversation support with context preservation

## 🔗 API Endpoints

### Health & Monitoring
- `GET /api/v1/health` - System health status and service monitoring

### Container Tracking
- `POST /api/v1/track` - Natural language container tracking queries
- `GET /api/v1/containers/{containerId}` - Container details and status
- `GET /api/v1/containers/{containerId}/milestones` - Container milestone history

### Bill of Lading
- `GET /api/v1/bl/{blNumber}` - Bill of lading details and associated containers

### Session Management
- `GET /api/v1/sessions/{sessionId}` - Session information and context
- `GET /api/v1/sessions/{sessionId}/messages` - Session message history

## 📚 Documentation

- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Development guidelines and workflow
- **[Backend README](backend/README.md)** - Detailed backend implementation guide
- **[API Documentation](docs/)** - Complete API specifications and examples
- **[Architecture Overview](specs/001-efl-agent-assistant-prototype-track-trace-vo/plan.md)** - System design and technical decisions

## 🔐 Security

- **Authentication**: JWT-based agent authentication
- **Authorization**: Role-based access control for containers and shipments
- **Encryption**: TLS 1.3+ for all communications
- **Audit Logging**: Comprehensive logging of all operations
- **Rate Limiting**: Protection against abuse and DoS attacks
- **Input Validation**: Strict validation of all user inputs

## 📈 Performance

- **Response Time**: <200ms target, <5s maximum for chat queries
- **Voice Response**: <20 seconds maximum for voice interactions
- **Concurrent Users**: Support for 100 simultaneous users
- **Throughput**: 10K container tracking requests per day
- **Uptime**: 99.5% service availability with monitoring

## 🤝 Support

For questions, issues, or contributions:
1. Check the [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines
2. Review existing issues and discussions
3. Follow the commit and PR guidelines for contributions
4. Use the specify system for progress tracking and context management

---

*Built with ❤️ using Spec-Driven Development methodology for reliable, maintainable, and scalable software delivery.*
