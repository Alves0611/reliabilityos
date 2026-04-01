# SLI/SLO Definitions

## Concepts

**SLI (Service Level Indicator)** -- A quantitative measure of a specific aspect of the service. It answers "how well is this thing working right now?"

**SLO (Service Level Objective)** -- A target value or range for an SLI over a time window. It answers "how well should this thing be working?"

**SLA (Service Level Agreement)** -- A contract with consequences when an SLO is missed. SLAs are always looser than SLOs -- the SLO is the internal target, the SLA is the external promise.

In ReliabilityOS, we define SLOs but do not expose SLAs. The SLOs drive our alerting, error budgets, and operational priorities.

---

## SLI Definitions

### orders-api Availability

Measures the proportion of successful HTTP requests served by the orders-api.

```promql
# SLI: ratio of non-5xx responses to total responses
sum(rate(http_requests_total{job="orders-api", status!~"5.."}[{{window}}]))
/
sum(rate(http_requests_total{job="orders-api"}[{{window}}]))
```

A request counts as "good" if it returns any status code outside the 5xx range. Client errors (4xx) are not counted as failures -- a 400 means the server correctly rejected a bad request.

### orders-api Latency (p95)

Measures the 95th percentile response time for the orders-api.

```promql
# SLI: p95 latency
histogram_quantile(0.95,
  sum(rate(http_request_duration_seconds_bucket{job="orders-api"}[{{window}}])) by (le)
)
```

Only non-error responses are included. A slow error is an availability problem, not a latency problem.

### Worker Processing Success

Measures the proportion of messages the worker processes successfully.

```promql
# SLI: ratio of successfully processed messages to total attempts
sum(rate(worker_messages_processed_total{status="success"}[{{window}}]))
/
sum(rate(worker_messages_processed_total[{{window}}]))
```

A message counts as "good" if the worker completes processing without error. Messages that are retried and eventually succeed count once as success. Messages that exhaust all retries count as failures.

---

## SLO Targets

| Service | SLI | SLO Target | Error Budget (30d) | Rationale |
|---------|-----|------------|-------------------|-----------|
| orders-api | Availability | 99.9% | 43.2 min | User-facing API, directly impacts order flow. Every failed request is a lost or delayed order. |
| orders-api | Latency p95 | < 200ms | N/A | Users expect sub-second responses. 200ms at p95 keeps the overall experience snappy while allowing headroom for tail latency. |
| worker | Processing success | 99.5% | 3.6 hours | Async processing with built-in retries. Occasional failures are tolerable since messages are durable in the queue. Higher target not justified given retry safety net. |

### Why These Numbers

**99.9% for orders-api availability** -- This is the sweet spot for an API that directly handles user transactions. Going to 99.99% would require multi-region active-active, which is not justified for a single-region deployment. Dropping to 99.5% would allow nearly 4 hours of downtime per month, which is too much for an order-processing system.

**200ms p95 for orders-api latency** -- Measured at the application boundary (not including client network time). This target accounts for database queries, SQS publishing, and serialization. The p95 threshold catches systemic slowdowns while ignoring one-off GC pauses or cold starts.

**99.5% for worker processing** -- The worker consumes from SQS with at-least-once delivery. Failed messages go to a dead-letter queue and can be reprocessed. The 99.5% target reflects that some message failures are expected (poison messages, transient dependency issues) and the system is designed to handle them gracefully.

---

## Measurement Windows

SLIs are evaluated at multiple time windows for different purposes:

| Window | Purpose | Use Case |
|--------|---------|----------|
| 5m | Real-time dashboards | Spot issues as they emerge. High noise, not used for alerting. |
| 30m | Short-term burn rate | Fast-burn alert detection (P1 Critical). Catches acute incidents. |
| 1h | Medium-term burn rate | Confirms sustained issues, reduces false positives from brief spikes. |
| 6h | Slow-burn detection | P2 Warning alerts. Catches gradual degradation that short windows miss. |
| 1d | Daily reporting | Used in daily SLO status reviews and trend analysis. |
| 30d | SLO compliance | The official compliance window. Error budget is calculated against this. |

### Rolling vs Calendar Windows

All windows are **rolling** (trailing), not calendar-aligned. A 30-day window means "the last 720 hours from right now," not "since the first of the month." This prevents the budget reset problem where teams burn through budget at month-end knowing it resets.

---

## Dashboard Layout

Grafana dashboards are organized around these SLOs:

1. **SLO Overview** -- Current compliance percentage for each SLO, burn rate, and remaining error budget
2. **orders-api Detail** -- Request rate, error rate, latency histogram, availability SLI over multiple windows
3. **Worker Detail** -- Processing rate, success/failure breakdown, queue depth, DLQ count
4. **Error Budget Tracker** -- Budget consumption over time with projection line showing when budget will exhaust at current burn rate
