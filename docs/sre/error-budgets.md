# Error Budget Policy

## How Error Budgets Work

An error budget is the inverse of an SLO. If the SLO says "99.9% of requests must succeed," the error budget says "0.1% of requests are allowed to fail." Over a 30-day window, that 0.1% translates to a concrete amount of tolerable failure.

The error budget is not a target -- it is an allowance. The goal is not to consume it. The goal is to spend it deliberately on things that matter: deploying new features, running chaos experiments, performing infrastructure migrations.

---

## Budget Calculations

### orders-api Availability

```
SLO: 99.9%
Budget: 0.1% of 30 days = 43.2 minutes of downtime
```

```promql
# Remaining error budget (ratio, 0 to 1)
1 - (
  (1 - (
    sum(rate(http_requests_total{job="orders-api", status!~"5.."}[30d]))
    /
    sum(rate(http_requests_total{job="orders-api"}[30d]))
  ))
  /
  (1 - 0.999)
)
```

When this value hits 0, the error budget is exhausted.

### Worker Processing Success

```
SLO: 99.5%
Budget: 0.5% of 30 days = 3.6 hours of processing failures
```

```promql
# Remaining error budget (ratio, 0 to 1)
1 - (
  (1 - (
    sum(rate(worker_messages_processed_total{status="success"}[30d]))
    /
    sum(rate(worker_messages_processed_total[30d]))
  ))
  /
  (1 - 0.995)
)
```

---

## Burn Rate

Burn rate measures how fast the error budget is being consumed relative to a uniform consumption rate.

| Burn Rate | Meaning | Time to Exhaust Budget |
|-----------|---------|----------------------|
| 1x | Consuming budget at exactly the expected rate | 30 days |
| 6x | Consuming 6x faster than expected | 5 days |
| 14.4x | Consuming 14.4x faster than expected | 50 hours |
| 36x | Consuming 36x faster than expected | 20 hours |

```promql
# Burn rate for orders-api availability (1h window)
(
  1 - (
    sum(rate(http_requests_total{job="orders-api", status!~"5.."}[1h]))
    /
    sum(rate(http_requests_total{job="orders-api"}[1h]))
  )
)
/
(1 - 0.999)
```

### Alert Tiers Based on Burn Rate

| Tier | Burn Rate | Long Window | Short Window | Action |
|------|-----------|-------------|--------------|--------|
| P1 Critical | 14.4x | 1h | 5min | Page on-call immediately. Active incident. |
| P2 Warning | 6x | 6h | 30min | Notify team channel. Investigate within the hour. |
| P3 Info | 1x | 3d | 6h | Track in daily standup. No immediate action required. |

The two-window approach (long + short) prevents alert fatigue. The long window catches sustained burns. The short window confirms the problem is still happening right now, preventing alerts that fire after an issue has already resolved.

---

## Budget Consumption Policy

### At 50% Budget Consumed

**Status: Yellow -- Caution**

Actions:
- Review recent deployments and changes for correlation with budget consumption
- Increase monitoring attention on affected service
- Consider reducing deployment frequency for the affected service
- No mandatory freeze, but team should be aware of the trend

### At 75% Budget Consumed

**Status: Orange -- Elevated Risk**

Actions:
- All deployments to the affected service require explicit approval from the on-call engineer
- Prioritize any open reliability-related tickets for the service
- Begin root cause analysis if consumption is not explained by known events
- Cancel or postpone any planned chaos experiments targeting the service
- Daily error budget review in standup

### At 100% Budget Consumed (Exhausted)

**Status: Red -- Budget Freeze**

Actions:
- **Deployment freeze** for the affected service. Only reliability fixes and critical security patches may be deployed.
- Feature work for the service is paused. Engineering effort redirects to reliability improvements.
- Incident review required: produce a summary of what consumed the budget and what systemic improvements will prevent recurrence
- Freeze lifts when the 30-day rolling budget recovers above 25% remaining (i.e., enough bad data has aged out of the window)

---

## Budget Consumption Tracking

The error budget dashboard shows:

1. **Current remaining budget** -- Absolute (minutes/hours) and percentage
2. **Consumption timeline** -- How the budget was spent over the past 30 days
3. **Projection line** -- At current burn rate, when will the budget exhaust?
4. **Event markers** -- Deployments, incidents, and config changes overlaid on the timeline

### Attribution

When budget is consumed, we attribute it to categories:

| Category | Description |
|----------|-------------|
| Planned | Deployments, migrations, maintenance windows |
| Incident | Unplanned outages or degradation |
| Dependency | Failures caused by upstream services (RDS, SQS, etc.) |
| Unknown | Cannot be attributed -- triggers investigation |

Good error budget hygiene means most consumption is either "planned" or "incident with a completed postmortem." High "unknown" attribution is a signal that observability needs improvement.

---

## Relationship Between Error Budget and Velocity

The error budget creates a self-regulating system:

- **Budget is healthy** -- Ship fast, take risks, run experiments. The budget exists to be spent on innovation.
- **Budget is shrinking** -- Slow down, be more careful with changes, invest in testing.
- **Budget is gone** -- Stop shipping features, fix reliability. This is not punishment; it is the system working as designed.

This removes the reliability vs. velocity argument. Both sides get what they want: product teams get a clear green light to ship when the service is healthy, and SRE gets a clear mechanism to pump the brakes when reliability degrades.
