---
title: "EFL Agent Assistant Prototype Spec: Track & Trace"
date: 2025-09-25
status: approved
owner: Product & Research Pair
source_prompt:
  - [Specify Phase Prompt — CMP Chat-First Experience Refresh]
related_specs:
  - [AI Assistant for Clearing Agents — Concept Specification]
---

## EFL Agent Assistant Prototype Spec: Track & Trace (Voice + Chat)

> Phase 0 pilot of the AI assistant. Scope, metrics, and validation feed the concept spec.

## Approval Snapshot (2025-09-25)

## Clarifications

### Session 2025-09-25
- Q: What level of data protection and access control is required for the Track & Trace prototype? → A: Standard protection - encrypted data in transit, role-based access, audit logging
- Q: What are the expected data volume and scale requirements for the Track & Trace prototype? → A: Small scale - 100 concurrent users, 10K containers/day
- Q: What are the scalability limits and deployment constraints for the Track & Trace prototype? → A: Single server deployment, simple vertical scaling
- Q: What are the reliability and availability targets for the Track & Trace prototype? → A: High availability - 99.5% uptime, automated failover
- Q: What are the compliance and regulatory requirements for the Track & Trace prototype? → A: Enhanced compliance - GDPR, SOX, and industry-specific regulations
- Q: What are the different user roles/personas that will access the Track & Trace system, and do they need different access levels or data visibility? → A: Different agent types (clearing, shipping, terminal) with role-based access
- Q: What are the accessibility requirements for the Track & Trace prototype? → A: Enhanced accessibility including voice control and high contrast
- Q: What are the technical stack constraints and preferences for the Track & Trace prototype implementation? → A: Existing EFL tech stack alignment required
- Q: What are the data retention and lifecycle management requirements for the Track & Trace prototype? → A: Extended retention - 90 days with audit trails
- Q: What level of error recovery and resilience is required for the Track & Trace prototype? → A: Enterprise-grade resilience - circuit breakers and monitoring

|Reviewer | Decision | Timestamp (WAT) | Evidence |
|--- | --- | --- | --- |
|Product & Research pair | ✅ Approved | 2025-09-25 | Session log entry |

## Objective

Develop a focused prototype of the EFL Agent Assistant with only the Track & Trace capability for
bonded terminal operations, accessible via both chat and voice. This prototype will demonstrate how
agents can retrieve real-time container and shipment updates using natural language queries.

---

### 1. Scope

**Included Features:**

* Track container or BL status via natural language chat or voice.
* Return container status, location, last milestone, and next step.
* Support queries by BL number, container number, or agency ID.
* Multi-turn conversation: handle follow-ups ("What does that mean?" or "When will it be ready?").
* Voice-friendly formatting: brief, clear responses suitable for phone calls.

**Nice to Have:**

* Personalization – recognize logged-in agent and pull only their containers and access controls.
* Fetch ocean shipping status and milestones from CMA CGM APIs.
* Provide estimated port discharge and vessel arrival from shipping APIs (e.g., CMA CGM, DCSA-compliant endpoints).
* Pull shipment history across CMA and EFL terminal APIs, including transshipment events, estimated delivery timeline, and delays and present answers intelligently.
* Fallback to CMA data when a container is not yet visible in EFL's yard systems.
* LLM calculates  logic using vessel ETA and port discharge milestones from CMA `/events`.

**Excluded Features:**

* Booking, payment, document upload, or invoicing.
* Exam scheduling or TDO-related flows.
* Gate pass or loading coordination.

---

### 2. Primary User Flow

**Chat Example:**

1. Agent: "Track BL ABC1234567"
2. Assistant:
   * "BL/shipment ABC1234567 corresponds to containers EFLU7896543 and EFLU7796767."
   * "Current status: arrived from Lekki Port."
   * "Location: EFL Terminal, Ikorodu"
   * "Next step: Awaiting exam booking."

**Voice Example:**

1. Assistant: "Welcome to EFL Agent Assistant. How can I help?"
2. Agent: "I want to check the status of a shipment.
3. Assistant: "Alright, I can help you with that. What is your Shipment number? 
4. Agent: It is container EFLU7896543.
5. Assistant: "That's a container number on Shipment ABC9876543"
3. Assistant: "Container EFLU7896543 is currently at EFL Terminal, Ikorodu. Status: Cleared for exam. Would you like to hear the next step?"
4. Agent: "Yes."
5. Assistant: "Next step: You may now book a customs examination."

**Fallback Logic Example (CMA-enhanced):**

* If a container is not found in TOS API:
  > Assistant: "Container ABC123 is not yet at the terminal. Let me check global shipping status…"
  >
  > "It's currently aboard vessel *Marco Polo* and is expected to discharge at Lagos Port on Sept 27. We’ll notify you when it’s transferred to EFL."

---

### 3. Intent & Entity Examples

* **Intents:**

  * TrackContainer
  * TrackBL
  * ClarifyContainerStatus
  * ClarifyAgentIntent

  * RequestNextStep
  * Fallback

* **Entities:**

  * BLNumber (e.g., "ABC1234567")
  * ContainerID (e.g., "EFLU7896543")
  * UserIdentity (e.g., phone number or CMP login ID)

---

### 4. Data & Integration Requirements

* Query container info from Terminus API:
  * Endpoint: `GET /containers/status`
  * Parameters: `container_id`, `bl_number`, `agent_id`
  * Returns: status, location, milestone history, owner, ETA

* Query container info from TOS API:
  * Endpoint: `GET /containers/status`
  * Parameters: `container_id`, `bl_number`, `agent_id`
  * Returns: status, location, milestone history, owner, ETA

* Supplement with CMA CGM Track & Trace API:
  * Endpoint: `GET /operation/trackandtrace/v1/events`
    * Filters: `transportDocumentReference`, `equipmentReference`
    * Event types: `ARRI`, `DEPA`, `LOAD`, `DISC`, `GTIN`, `GTOT`
    * Returns: shipping leg events, vessel milestones, transshipment hops
  * Endpoint: `GET /shipments/{bookingReference}`
    * Use: retrieve booking meta, validation, container-to-booking mapping

* Combined data model: Assistant merges terminal view from EFL with global view from CMA for full end-to-end context.

* Authentication:
  * Chat: via CMP portal session or WhatsApp ID mapping
  * Voice: caller ID matched to agent ID + passphrase or OTP
  * CMA APIs: OAuth2 client credentials and `behalfOf` required for private endpoints

* User Roles & Access Control:
  * **Clearing Agents:** Full access to their assigned containers and associated documentation
  * **Shipping Agents:** Access to vessel schedules, discharge information, and container status
  * **Terminal Agents:** Access to yard locations, gate passes, and terminal operations data
  * **Admin Users:** Full system access with audit capabilities

* Security Requirements:
  * Encrypted data in transit (TLS 1.3+)
  * Role-based access control for container data based on agent type
  * Audit logging for all data access and modifications
  * Data protection standards for sensitive shipping information
  * User access limited to containers under their agency relationship

* Compliance & Regulatory Requirements:
  * GDPR compliance for personal data handling
  * SOX compliance for financial reporting and audit trails
  * Industry-specific shipping and logistics regulations
  * Regular compliance audits and documentation

* Data Retention & Lifecycle Management:
  * **Operational Data:** 90-day retention period for container tracking and interaction logs
  * **Audit Trails:** Complete audit logging with 90-day retention for compliance review
  * **Personal Data:** GDPR-compliant retention with user consent and right to erasure
  * **Data Archival:** Automated archival process for data exceeding retention periods
  * **Lifecycle Management:** Clear data classification and disposal procedures

---

### 5. Technical Requirements

* Response latency ≤ 5 seconds for chat and voice answers
* Voice responses limited to 20 seconds max
* Include confirmation for voice inputs ("Did you say container EFLU7896543?")
* Use progressive disclosure (break info into parts)
* Re-prompt after silence ("Still there? Do you want the next step?")

### 5.3. Accessibility Requirements

* **Enhanced Accessibility:** Full WCAG 2.1 AA compliance including voice control and high contrast modes
* **Voice Interface:** Support for users with visual impairments through enhanced voice navigation
* **Screen Reader Support:** Complete screen reader compatibility for all chat and voice interfaces
* **High Contrast Mode:** High contrast color schemes for users with visual impairments
* **Keyboard Navigation:** Full keyboard accessibility for all interactive elements
* **Multiple Input Methods:** Support for voice, chat, and touch/click interfaces

### 5.4. Technical Stack & Architecture

* **Core Framework:** OpenAI Agents SDK with Voice capabilities and Responses API
* **Voice Pipeline:** OpenAI Realtime API with Twilio telephony integration
* **Backend:** FastAPI with Python 
* **Frontend:** React with TypeScript 
* **Orchestration:** AI SDK/ LangGraph for planner-based tool coordination
* **Data Integration:** MCP (Model Context Protocol) servers for Terminus(TOS) and CMA APIs
* **Architecture:** Multi-agent system with specialized agents for different functions
* **Stack Alignment:** Must integrate with existing EFL tech stack and deployment practices

### 5.1. Scale & Performance Requirements

* **Concurrent Users:** Support up to 100 simultaneous chat and voice sessions
* **Daily Volume:** Handle up to 10,000 container tracking requests per day
* **Data Scale:** Manage container status data for active shipments across EFL terminal and CMA CGM systems
* **Deployment Model:** Single server deployment with vertical scaling approach
* **Caching Strategy:** Implement appropriate caching to maintain performance under load

### 5.2. Reliability & Availability Requirements

* **Uptime Target:** 99.5% availability (approximately 3.5 hours of downtime per month)
* **Automated Failover:** Implement health checks and automatic recovery mechanisms
* **Monitoring:** Real-time system monitoring and alerting for critical failures
* **Recovery Time:** Target < 5 minutes recovery time for system failures
* **Enterprise Resilience:** Circuit breakers, retry logic, and graceful degradation patterns
* **Error Recovery:** Comprehensive error handling with automated fallback mechanisms

---

### 6. Error Handling

* **User-Friendly Error Messages:** Clear, actionable error responses for all failure scenarios
* **Graceful Degradation:** System continues to function with reduced capabilities during partial failures
* **Circuit Breakers:** Automatic failure detection and isolation for external API dependencies
* **Retry Logic:** Intelligent retry mechanisms with exponential backoff for transient failures
* **Fallback Mechanisms:** Automated failover to alternative data sources (CMA when Terminus unavailable)

* **Specific Error Scenarios:**
  * If BL/container not found:
    * "Sorry, I couldn't find a record for BL ABC1234567. Please check the number and try again."
  * If multiple containers under a BL:
    * List them and prompt: "I found 3 containers under that BL. Which one would you like to track?"
  * If not found in EFL system:
    * "I couldn't find that container in our terminal. Checking CMA shipping events…"
    * "Container not yet discharged in Lagos. Last seen in transit via vessel 'CMA MONTEVIDEO'. ETA Sept 26."
  * On backend failure:
    * "Sorry, I'm unable to retrieve status right now. Please try again shortly or contact customer service."
  * On partial system failure:
    * "Some services are temporarily unavailable. I can provide basic tracking information while we restore full functionality."

---

