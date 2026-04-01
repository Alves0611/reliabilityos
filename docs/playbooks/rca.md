# Root Cause Analysis (RCA)

**Incident:** [Title — same as postmortem]
**Date of incident:** YYYY-MM-DD
**RCA Author:** [Name]
**Linked postmortem:** [link]

---

## Method Selection

Use the right tool for the problem:

| Situation | Use |
|---|---|
| Single chain of failure — one thing led to another | **5 Whys** |
| Multiple contributing factors from different domains | **Fishbone (Ishikawa)** |
| Both — complex incident with a primary chain and contributing factors | **5 Whys for the primary chain + Fishbone for the full picture** |

---

## Technique 1: 5 Whys

Start with the observable symptom and ask "why?" until you reach a systemic root cause. Stop when you hit something you can fix at a systems/process level — not at a person.

### Template

**Problem statement:** _[One sentence: what happened]_

| # | Why? | Answer |
|---|---|---|
| 1 | Why did [problem] happen? | _Because..._ |
| 2 | Why did [answer 1] happen? | _Because..._ |
| 3 | Why did [answer 2] happen? | _Because..._ |
| 4 | Why did [answer 3] happen? | _Because..._ |
| 5 | Why did [answer 4] happen? | _Because..._ |

**Root cause:** _[Summarize the systemic issue revealed by the chain]_

### Example: Orders Started Failing

**Problem statement:** Customers received 500 errors when placing orders for 47 minutes.

| # | Why? | Answer |
|---|---|---|
| 1 | Why were orders returning 500 errors? | Because the orders-api could not acquire a database connection. |
| 2 | Why could it not acquire a database connection? | Because all 10 connections in the pool were in use and none were being released. |
| 3 | Why were connections not being released? | Because a new query introduced in v2.3.1 was running for 30+ seconds instead of the expected 200ms. |
| 4 | Why was the slow query not caught before production? | Because the load test suite does not include slow-query or degraded-database scenarios. |
| 5 | Why does the load test suite not cover degraded scenarios? | Because there is no requirement or checklist for testing failure modes before release. |

**Root cause:** The release process has no gate for validating behavior under degraded conditions (slow dependencies, resource exhaustion). The connection pool had no circuit breaker to shed load when saturated.

---

## Technique 2: Fishbone (Ishikawa) Diagram

Use this when multiple independent factors contributed to the incident. Organize causes into four categories relevant to SRE work.

### Template

```
                                    INCIDENT
                                       |
        -------------------------------------------------------
        |              |                |                      |
  INFRASTRUCTURE   APPLICATION       PROCESS              EXTERNAL
        |              |                |                      |
   _________       _________        _________             _________
  |         |     |         |      |         |           |         |
  | cause   |     | cause   |      | cause   |           | cause   |
  | cause   |     | cause   |      | cause   |           | cause   |
  |_________|     |_________|      |_________|           |_________|
```

### Category Guide

| Category | What to look for |
|---|---|
| **Infrastructure** | Resource limits, capacity, networking, cloud provider issues, hardware |
| **Application** | Code bugs, config errors, missing validations, dependency failures |
| **Process** | Missing runbooks, no review gates, deployment process gaps, alert gaps |
| **External** | Third-party outages, DNS, traffic spikes, upstream API changes |

### Example: Orders Failing — Fishbone Analysis

```
                              ORDERS FAILING (500s for 47 min)
                                           |
            --------------------------------------------------------------
            |                |                  |                         |
      INFRASTRUCTURE    APPLICATION          PROCESS                 EXTERNAL
            |                |                  |                         |
   ________________    _______________    ___________________      ______________
  | Pool max=10    |  | Slow query   |  | No load test for |    | None         |
  | (too low for   |  | in v2.3.1    |  | degraded deps    |    | identified   |
  |  peak load)    |  |              |  |                  |    |              |
  |                |  | No circuit   |  | No pre-deploy    |    |              |
  | No pool        |  | breaker on   |  | query review     |    |              |
  | utilization    |  | DB calls     |  |                  |    |              |
  | monitoring     |  |              |  | Runbook for DB   |    |              |
  |                |  | No query     |  | issues outdated  |    |              |
  |________________|  | timeout set  |  |__________________|    |______________|
                      |______________|
```

---

## RCA Checklist

Before finalizing this RCA, verify every item:

### Root Cause Quality

- [ ] The root cause identifies a **system or process gap**, not a person
- [ ] The root cause explains **why the system allowed the failure**, not just what broke
- [ ] If you removed this root cause, the incident **could not recur in the same way**
- [ ] The root cause is **specific enough to act on** (not "we need better monitoring")

### Action Items Are SMART

Every action item must be:

- [ ] **S**pecific — clear what needs to be done (_"Add connection pool utilization alert at 80% threshold"_, not _"improve monitoring"_)
- [ ] **M**easurable — you can verify it is done (_"Alert fires in staging test"_)
- [ ] **A**ssignable — has a named owner
- [ ] **R**ealistic — can be done with available resources
- [ ] **T**ime-bound — has a due date

### Completeness

- [ ] All contributing factors are documented (use Fishbone if >2 factors)
- [ ] Timeline in the linked postmortem is accurate and complete
- [ ] Detection gaps are identified (could we have caught this earlier?)
- [ ] Action items cover **prevention**, **detection**, and **mitigation**
- [ ] This RCA is linked from the postmortem document

---

## Full Example: Orders-API Connection Pool Exhaustion

**Incident:** Orders-API 500 errors due to connection pool exhaustion
**Date of incident:** 2026-03-15
**Linked postmortem:** /docs/postmortems/2026-03-15-orders-api-pool-exhaustion.md

### 5 Whys

**Problem statement:** Customers received 500 errors when placing orders for 47 minutes.

| # | Why? | Answer |
|---|---|---|
| 1 | Why were orders returning 500 errors? | The orders-api could not acquire a database connection from the pool. |
| 2 | Why were no connections available? | All 10 connections were held by a query running 30+ seconds (expected: 200ms). |
| 3 | Why was a 30-second query in production? | Release v2.3.1 introduced a full table scan that was not caught in review or testing. |
| 4 | Why was it not caught? | No query performance validation exists in the CI pipeline or deploy process. |
| 5 | Why is there no query validation? | Failure-mode testing has never been added to the release checklist. |

**Root cause:** The release process lacks query performance validation, and the application has no protection (circuit breaker, connection timeout) against slow dependencies exhausting shared resources.

### Fishbone

```
                              ORDERS FAILING (500s for 47 min)
                                           |
            --------------------------------------------------------------
            |                |                  |                         |
      INFRASTRUCTURE    APPLICATION          PROCESS                 EXTERNAL
            |                |                  |                         |
   ________________    _______________    ___________________      ______________
  | Connection     |  | Full table   |  | No query perf    |    | N/A          |
  | pool max=10    |  | scan in      |  | check in CI      |    |              |
  | (undersized)   |  | v2.3.1       |  |                  |    |              |
  |                |  |              |  | No failure-mode  |    |              |
  | No pool usage  |  | No circuit   |  | testing in       |    |              |
  | metric or      |  | breaker      |  | release process  |    |              |
  | alert          |  |              |  |                  |    |              |
  |                |  | No per-query |  | DB incident      |    |              |
  |                |  | timeout      |  | runbook outdated |    |              |
  |________________|  |______________|  |__________________|    |______________|
```

### Action Items

| # | Action | Type | Owner | Priority | Due Date | Status |
|---|---|---|---|---|---|---|
| 1 | Add circuit breaker with 5s timeout on all DB calls in orders-api | Prevention | @backend | P1 | 2026-03-22 | Open |
| 2 | Increase connection pool to 50, add pool utilization alert at 80% | Detection | @sre | P1 | 2026-03-22 | Open |
| 3 | Add EXPLAIN ANALYZE check to CI for queries touching >10k rows | Prevention | @backend | P1 | 2026-03-29 | Open |
| 4 | Add degraded-dependency scenario to load test suite | Prevention | @qa | P2 | 2026-04-05 | Open |
| 5 | Rewrite DB incident runbook with connection pool troubleshooting | Mitigation | @sre | P2 | 2026-04-05 | Open |
| 6 | Add per-query timeout of 5s as application default | Prevention | @backend | P2 | 2026-03-29 | Open |

### Summary

The primary chain of failure was: slow query -> pool exhaustion -> 500 errors. This was enabled by three systemic gaps: no query performance gate in the release process, no resource protection (circuit breaker/timeout) in the application, and no pool utilization monitoring to provide early warning. Action items address all three layers.
