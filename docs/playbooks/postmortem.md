# Postmortem: [Incident Title]

**Date:** YYYY-MM-DD
**Author:** [Name]
**Severity:** SEV-[1/2/3/4]
**Status:** Draft | In Review | Final

---

## Incident Summary

_One or two sentences describing what happened and the user-facing impact._

> Example: The orders-api returned 500 errors for 47 minutes due to a database connection pool exhaustion, preventing users from placing new orders.

---

## Impact

| Metric | Value |
|---|---|
| Duration | _start time_ to _end time_ (XX minutes) |
| Users affected | _number or percentage_ |
| Orders/requests lost | _number or "none — retried successfully"_ |
| SLO affected | _e.g., Availability SLO (99.9%)_ |
| Error budget consumed | _e.g., 38% of monthly budget_ |
| Error budget remaining | _e.g., 62%_ |
| Revenue impact | _estimated or N/A_ |
| Support tickets opened | _number_ |

---

## Timeline

All times in UTC.

| Time | Event | Action Taken |
|---|---|---|
| HH:MM | First alert fires (e.g., error rate > 5%) | On-call acknowledges |
| HH:MM | _What happened next_ | _What someone did_ |
| HH:MM | _Escalation or diagnosis step_ | _Debugging action_ |
| HH:MM | Root cause identified | _Fix applied_ |
| HH:MM | Service restored | Monitoring confirms recovery |
| HH:MM | All-clear declared | Incident channel closed |

---

## Detection

- **How was the incident detected?** _Alert / customer report / internal discovery_
- **Time to detect (TTD):** _X minutes from first impact to first alert_
- **Was alerting effective?** _Yes/No — explain gaps_

---

## Root Cause

_Describe what failed at a systems level. Focus on the mechanism, not the person._

> Example: The connection pool was configured with a max of 10 connections. A slow query introduced in release v2.3.1 held connections for 8x longer than normal, exhausting the pool under standard load. No circuit breaker existed to shed load when the pool was full.

---

## Contributing Factors

_List the conditions that allowed this to happen or made it worse._

- [ ] _e.g., No connection pool metrics were being monitored_
- [ ] _e.g., Load testing did not cover slow-query scenarios_
- [ ] _e.g., Rollback took 12 minutes because the deploy pipeline has no fast-rollback path_
- [ ] _e.g., Runbook for database issues was outdated_

---

## What Went Well

_Acknowledge what worked. This matters for morale and for knowing what to keep doing._

- _e.g., On-call responded within 3 minutes of the alert_
- _e.g., Communication in the incident channel was clear and structured_
- _e.g., Grafana dashboards made it easy to pinpoint the connection pool as the bottleneck_

---

## What Went Wrong

_Be specific about what broke down in systems, processes, or tooling._

- _e.g., The alert threshold was too high — 5% error rate means hundreds of failed requests before we notice_
- _e.g., No runbook existed for connection pool exhaustion_
- _e.g., The rollback required manual steps that added 8 minutes to recovery_

---

## Action Items

| # | Action | Owner | Priority | Due Date | Status |
|---|---|---|---|---|---|
| 1 | _e.g., Add connection pool utilization alert at 80%_ | _@name_ | P1 | YYYY-MM-DD | Open |
| 2 | _e.g., Implement circuit breaker on orders-api_ | _@name_ | P1 | YYYY-MM-DD | Open |
| 3 | _e.g., Add slow-query scenario to load tests_ | _@name_ | P2 | YYYY-MM-DD | Open |
| 4 | _e.g., Write runbook for connection pool incidents_ | _@name_ | P2 | YYYY-MM-DD | Open |
| 5 | _e.g., Reduce rollback time to under 2 minutes_ | _@name_ | P3 | YYYY-MM-DD | Open |

**Action item status:** Open | In Progress | Done | Won't Do (with justification)

---

## Lessons Learned

- _e.g., Connection pool limits must scale with expected query latency, not just connection count_
- _e.g., Alerts on resource utilization (not just errors) would have given us 10+ minutes of early warning_
- _e.g., Fast rollback capability is not optional for production services_

---

## Related

- **Incident Slack channel:** #inc-YYYY-MM-DD-short-name
- **Monitoring dashboard:** _link_
- **Related postmortems:** _links if this is a recurring pattern_
- **RCA document:** _link to detailed root cause analysis if applicable_

---

> **A note on blameless culture**
>
> This postmortem exists to make our systems more reliable, not to assign blame.
> Humans make mistakes — that is expected. The question is never "who caused this?"
> but "why did our systems allow this to happen, and what do we change so it
> cannot happen the same way again?"
>
> If you find yourself writing a sentence with someone's name attached to a failure,
> rewrite it to describe the system gap instead:
>
> - Instead of: "Alice deployed the bad config"
> - Write: "The deployment pipeline did not validate config changes against the schema"
>
> People act rationally given the information they had at the time. Fix the systems.
