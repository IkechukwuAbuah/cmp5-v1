# Data Model: EFL Agent Assistant Track & Trace

## Core Entities

### Container
**Purpose**: Primary entity for tracking container status and location

```typescript
interface Container {
  id: string;                    // Unique container identifier (e.g., "EFLU7896543")
  containerNumber: string;       // ISO container number
  isoCode: string;              // Container size/type code
  status: ContainerStatus;      // Current status (see enum below)
  location: TerminalLocation;    // Current physical location
  billOfLading: BillOfLading;    // Associated BL reference
  agentId: string;              // Assigned clearing agent
  milestones: ContainerMilestone[]; // Historical status changes
  lastUpdated: Date;            // Last status update timestamp
  nextStep: string;             // Next action required (human-readable)
}

enum ContainerStatus {
  IN_TRANSIT = "in_transit",
  AT_TERMINAL = "at_terminal",
  DISCHARGED = "discharged",
  CLEARED_FOR_EXAM = "cleared_for_exam",
  UNDER_EXAM = "under_exam",
  RELEASED = "released",
  DELIVERED = "delivered"
}
```

### Bill of Lading (BL/Shipment)
**Purpose**: Groups multiple containers under a single shipment

```typescript
interface BillOfLading {
  id: string;                   // BL number (e.g., "ABC1234567")
  blNumber: string;             // Bill of Lading number
  containers: Container[];      // Associated containers
  vesselVoyage: VesselVoyage;   // Transport vessel and voyage
  origin: string;               // Port of origin
  destination: string;          // Port of destination
  estimatedArrival: Date;       // ETA at destination port
  actualArrival?: Date;         // Actual arrival if available
  shippingLine: string;         // CMA CGM or other carrier
  agentId: string;              // Assigned clearing agent
}
```

### Agent/User
**Purpose**: Represents clearing agents with access controls

```typescript
interface Agent {
  id: string;                   // Unique agent identifier
  name: string;                 // Agent company name
  type: AgentType;             // Clearing, Shipping, or Terminal agent
  contactInfo: ContactInfo;     // Phone, email, etc.
  containers: Container[];      // Containers assigned to this agent
  permissions: Permission[];    // Role-based permissions
  sessionHistory: AgentSession[]; // Voice/chat session history
}

enum AgentType {
  CLEARING = "clearing",
  SHIPPING = "shipping",
  TERMINAL = "terminal",
  ADMIN = "admin"
}

interface Permission {
  resource: string;            // "container", "bl", "terminal_data"
  actions: string[];           // ["read", "write", "track"]
  conditions?: string[];       // Optional conditions for access
}
```

### Terminal Location
**Purpose**: Physical locations within the terminal system

```typescript
interface TerminalLocation {
  id: string;                  // Unique location identifier
  name: string;                // Human-readable name
  type: LocationType;          // Yard, Gate, Warehouse, etc.
  coordinates?: Coordinates;   // GPS coordinates if available
  terminalId: string;          // Associated terminal
  isActive: boolean;           // Whether location is operational
}

enum LocationType {
  YARD = "yard",
  GATE_IN = "gate_in",
  GATE_OUT = "gate_out",
  WAREHOUSE = "warehouse",
  EXAM_AREA = "exam_area"
}
```

### Vessel/Voyage Information
**Purpose**: Maritime transport details from CMA CGM

```typescript
interface VesselVoyage {
  id: string;                  // Unique voyage identifier
  vesselName: string;          // Name of the vessel
  voyageNumber: string;        // Voyage reference number
  carrier: string;             // CMA CGM or other
  originPort: string;          // Port of departure
  destinationPort: string;     // Port of arrival
  estimatedDeparture: Date;    // ETD from origin
  estimatedArrival: Date;      // ETA at destination
  actualDeparture?: Date;      // Actual departure if available
  actualArrival?: Date;        // Actual arrival if available
  status: VoyageStatus;       // Current voyage status
}

enum VoyageStatus {
  PLANNED = "planned",
  DEPARTED = "departed",
  IN_TRANSIT = "in_transit",
  ARRIVED = "arrived",
  DELAYED = "delayed"
}
```

### Container Milestone/Event
**Purpose**: Historical status changes and events

```typescript
interface ContainerMilestone {
  id: string;                  // Unique milestone identifier
  containerId: string;         // Associated container
  eventType: EventType;        // Type of event (see enum)
  location: TerminalLocation;  // Location where event occurred
  timestamp: Date;             // When the event happened
  description: string;         // Human-readable description
  source: DataSource;          // EFL Terminal or CMA CGM
  metadata?: Record<string, any>; // Additional event-specific data
}

enum EventType {
  LOADED = "loaded",
  DISCHARGED = "discharged",
  GATE_IN = "gate_in",
  GATE_OUT = "gate_out",
  CUSTOMS_EXAM = "customs_exam",
  RELEASED = "released",
  DELIVERED = "delivered",
  TRANSSHIPMENT = "transshipment"
}

enum DataSource {
  EFL_TERMINAL = "efl_terminal",
  CMA_CGM = "cma_cgm",
  TOS = "tos"
}
```

### Session Management
**Purpose**: Track conversation context across voice and chat

```typescript
interface AgentSession {
  id: string;                  // Unique session identifier
  agentId: string;             // Associated agent
  channel: ChannelType;        // Voice or Chat
  startTime: Date;             // Session start timestamp
  endTime?: Date;              // Session end timestamp (if completed)
  conversationHistory: Message[]; // All messages in session
  context: SessionContext;     // Current conversation context
  status: SessionStatus;       // Active, completed, expired
}

enum ChannelType {
  VOICE = "voice",
  CHAT = "chat",
  API = "api"
}

interface SessionContext {
  currentIntent?: string;      // TrackContainer, ClarifyStatus, etc.
  activeEntities: EntityReference[]; // Container IDs, BL numbers, etc.
  lastResponse: string;        // Last assistant response
  pendingActions: string[];    // Actions awaiting user response
}

interface EntityReference {
  type: "container" | "bl" | "agent";
  id: string;
  confidence: number;          // Recognition confidence score
}
```

## Data Relationships

### Entity Relationship Diagram
```
Agent ───┬─── Container ───┬─── BillOfLading
         │                 │
         │                 └─── VesselVoyage
         │
         ├─── AgentSession ───┬─── SessionContext
         │                     │
         │                     └─── Message
         │
         └─── TerminalLocation

Container ───┬─── ContainerMilestone
             │
             └─── Location History
```

### Key Relationships:
- **One-to-Many**: Agent → Container (one agent manages many containers)
- **One-to-Many**: BillOfLading → Container (one BL covers multiple containers)
- **One-to-Many**: Container → ContainerMilestone (container has many status changes)
- **Many-to-One**: Container → TerminalLocation (many containers in one location)
- **One-to-Many**: Agent → AgentSession (agent has many conversation sessions)

## Validation Rules

### Container Validation
- Container number must match ISO 6346 format
- Status transitions must follow business rules (e.g., can't go from DELIVERED back to IN_TRANSIT)
- Agent must have permission to access container
- Location must exist and be active

### Bill of Lading Validation
- BL number must be unique across systems
- All associated containers must belong to same agent
- Voyage information must be consistent

### Session Validation
- Session timeout after 30 minutes of inactivity
- Maximum 50 messages per session for performance
- Context must be preserved across channel switches

## Data Flow Patterns

### Track Container Flow
1. User queries container status
2. System validates agent permissions
3. Query EFL Terminal API for container data
4. If not found, fallback to CMA CGM API
5. Merge and validate data from multiple sources
6. Return formatted response with next steps

### Voice Channel Flow
1. Twilio receives voice input
2. OpenAI Realtime API processes speech-to-text
3. Extract intent and entities from natural language
4. Query relevant data sources
5. Generate voice-friendly response
6. Text-to-speech conversion and playback

### Session Continuity Flow
1. User switches between voice and chat
2. Session context preserved in Redis
3. Entity references maintained across channels
4. Conversation history synchronized
5. Seamless handoff between modalities
