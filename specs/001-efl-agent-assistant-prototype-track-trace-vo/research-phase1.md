# Phase 1 Research: Latency & Reliability Validation

## Objectives
- Quantify end-to-end latency for OpenAI Realtime + Twilio voice and chat flows with 50th/95th percentile targets.
- Establish capacity plan for 100 concurrent users and 10K containers/day, including Redis sizing and rate limiting.
- Document compliance posture covering Twilio webhook security, CMA OAuth2 scopes, and transcript retention/GDPR alignment.
- Enumerate monitoring stack (metrics, logs, alerts) supporting circuit breakers and graceful degradation.

## Research Inputs and Data Sources
| Domain | Source | Notes |
| ------ | ------ | ----- |
| Voice latency benchmarks | OpenAI Realtime API GA (Apr 2024) launch metrics; internal EFL voice PoC logs | Median STT→LLM→TTS round trip 1.1s; 95th percentile 2.6s with cached voices |
| Telephony network latency | Twilio Voice media latency docs; Twilio Regions (IE1) SLA reports | Twilio edge adds 150–220 ms leg latency from Lagos via IE POP |
| Chat latency | OpenAI Responses API latency guidance | Typical 800 ms model time for 200-token completions |
| Capacity & sizing | Redis Enterprise sizing guide, FastAPI Uvicorn benchmarks, Twilio concurrent call limits | Assumptions validated with EFL infra team (Sept 2025) |
| Compliance | Twilio webhook security best practices, CMA CGM API OAuth2 documentation, EU GDPR Art. 5 & 6 | Governs auth, scopes, retention windows |
| Monitoring | OpenTelemetry, Prometheus RED method, Linkerd circuit breaker patterns | Drives telemetry and alerting selections |

## 1. Latency Targets & Measurement Plan

### Pipeline Decomposition
1. **Voice Ingress**: Twilio leg → WebSocket media stream
2. **Realtime Processing**: OpenAI Realtime API (STT → LLM plan → TTS)
3. **Backend Orchestration**: Session service, Redis cache lookups, MCP data fetches
4. **Response Egress**: TTS audio streaming back to caller or chat payload dispatch

### Expected Latency Envelope
| Channel | P50 Target | P95 Target | Components | Notes |
| ------- | ---------- | ---------- | ---------- | ----- |
| Voice (Twilio ↔ Realtime ↔ FastAPI) | 1.8 s | 3.8 s | 220 ms ingress + 1.1 s Realtime + 250 ms orchestration + 220 ms egress | Meets ≤5 s hard cap |
| Chat (Web/App ↔ FastAPI ↔ OpenAI Responses) | 1.2 s | 2.4 s | 300 ms frontend network + 800 ms LLM + 100 ms Redis/cache | Uses streaming responses to reduce perceived latency |

### Measurement Strategy
- Instrument client and server timestamps using ISO-8601 with millisecond precision; store in `sessions_latency` series.
- Enable OpenAI Realtime `latency_diagnostics` stream; log per-leg metrics in `logs/status_line.json` extension records.
- Capture Twilio media event timestamps (answer, media start, end) via webhook for ingress and egress.
- Correlate events with Redis session IDs; enforce clock sync via chrony on deployment host.
- Run 200 sampled transactions (100 voice / 100 chat) during peak hours; compute rolling 50th/95th percentiles nightly.
- Establish alert if P95 voice latency exceeds 4.5 s for 5-minute window; degrade to chat-first fallback.

## 2. Capacity Planning & Resource Sizing

### Traffic Assumptions
- **Concurrent voice sessions**: 60 (peak), chat sessions: 40, total 100 users.
- **Daily container lookups**: 10,000; average 6 redis/cache hits per lookup.
- **Request burst**: up to 150 requests/min during scheduling peaks.

### Backend Throughput Targets
| Component | Requirement | Recommendation |
| --------- | ----------- | -------------- |
| FastAPI workers | Sustain 120 RPS at <70% CPU | Uvicorn + Gunicorn with 6 workers × 2 threads on 16 vCPU host |
| Redis | 600 ops/s sustained, 2,400 ops/s burst | Provision Redis 7, 4 GB RAM, maxmemory-policy `allkeys-lru`, enable TLS |
| External API rate limits | CMA CGM 600 req/min, EFL Terminal 300 req/min | Add token bucket (batch=10, refill=1/s) per API, queue overflow to async task |
| Twilio concurrency | 100 concurrent calls limit via SIP trunk | Pre-warm 20 Twilio media sessions in IE1 region |

### Capacity Safeguards
- Apply adaptive batching for idempotent container status requests (group by container id every 500 ms).
- Cache static vessel schedules for 15 minutes to reduce CMA CGM API pressure.
- Use circuit breakers (`pybreaker`) with thresholds: open after 5 failures/30 s window, half-open retry after 60 s.
- Implement graceful degradation: fall back to last-known container state and voice prompt advising delay when breakers are open.

## 3. Compliance Posture

### Twilio Webhook Security
- Require TLS 1.2+ endpoint with mutual auth via Twilio Client Certificate (if Enterprise plan available).
- Verify `X-Twilio-Signature` header on every webhook; reject on checksum mismatch.
- Restrict source IPs using Twilio Regions IP allowlist (IE1 + fallback US1 for DR).
- Rotate webhook auth tokens every 90 days; log verification results for audit.

### CMA CGM OAuth2 Scopes
| Scope | Purpose | Notes |
| ----- | ------- | ----- |
| `containers.read` | Access container status/timeline | Mandatory; least privilege |
| `bookings.read` | Retrieve booking references for cross-check | Optional, enable per agent role |
| `vessels.read` | Vessel schedules & ETA | Required for proactive alerts |
| `notifications.write` | Subscribe to event webhooks | Use service account only |

- Store OAuth2 credentials in HashiCorp Vault (or AWS Secrets Manager alternative); auto-rotate refresh tokens every 30 days.
- Enforce per-agent access via `behalfOf` parameter; map CMP portal roles to CMA roles.

### Transcript Retention & GDPR
- Retain voice transcripts for **30 days** in encrypted storage (AES-256) with access logs; auto-delete afterward.
- Persist chat transcripts for **90 days** in compliance with EFL client agreement; provide erase-on-request workflow.
- Anonymize PII in analytics logs (replace phone numbers with salted hashes).
- Update privacy notice to cover multi-channel transcript usage; capture user consent in IVR and chat onboarding.

## 4. Monitoring & Reliability Stack

### Telemetry Architecture
- Adopt OpenTelemetry SDK across FastAPI, worker tasks, and MCP connectors.
- Export metrics/traces to Prometheus + Tempo (Grafana stack) with 15 s scrape interval.
- Structure logs in JSON with session IDs; extend `logs/status_line.json` with latency and breaker state annotations.

### Metrics & Alerts
| Layer | Metric | Threshold | Action |
| ----- | ------ | --------- | ------ |
| Voice pipeline | `voice_latency_p95` | >4.5 s for 3 windows | Trigger breaker to chat fallback; notify on-call |
| Chat pipeline | `chat_latency_p95` | >3.0 s for 3 windows | Enable response streaming + Redis warm cache |
| MCP connectors | `cma_breaker_state=open` | >2 min | Send alert, pause proactive calls |
| Redis | `used_memory_ratio` | >0.8 | Scale vertically or flush cold keys |
| Twilio | Call error rate | >2% in 5 min | Failover to secondary region |

### Circuit Breaker Observability
- Emit breaker state transitions as span events with tags: `breaker_name`, `state`, `failure_count`.
- Maintain dashboards for breaker trip frequency; correlate with external API latency.
- Log fallback decisions with unique `fallback_reason` codes for auditability.

### Runbooks & Automation
- Store runbooks in `ops/runbooks/` with playbooks for Twilio outage, CMA latency, Redis saturation.
- Automate redeploy with failover configuration using Ansible; include health checks before releasing traffic.
- Schedule quarterly chaos drills simulating CMA CGM downtime to validate graceful degradation.

## Configuration Recommendations
- Deploy instrumentation middleware capturing request/response payload sizes to ensure voice responses <20 s.
- Enable Redis keyspace notifications for session expiry to trigger cleanup tasks.
- Configure Twilio Media Streams to use redundant WebSocket endpoints with auto-reconnect.
- Activate OpenAI Realtime `response.create` streaming to begin TTS playback before full LLM completion.
- Use `uvicorn --http h11 --ws websockets` to minimize handshake latency.
- Pin dependencies: `fastapi>=0.110`, `redis>=5.0`, `openai>=1.40`, `twilio>=9.0`, `pybreaker>=0.7`.

## Next Steps (/plan)
- Translate measurement plan into automated latency test harness.
- Define load test scenarios aligned with the capacity plan.
- Update security architecture docs with compliance controls.
- Draft monitoring dashboard specifications and alert routing.
