# On-Call Structure

## Rotation Schedule

On-call rotations are weekly, starting and ending on Wednesdays at 10:00 UTC. Wednesday handoffs avoid Monday (post-weekend issues) and Friday (pre-weekend stress).

| Role | Rotation Length | Overlap | Coverage |
|------|----------------|---------|----------|
| Primary on-call | 7 days | 1 hour with previous primary | 24/7 |
| Secondary on-call | 7 days | None (shadow role) | Business hours + escalation |

### Handoff Procedure

1. Outgoing on-call writes a handoff summary: open issues, things to watch, pending changes
2. Incoming on-call reviews the summary and acknowledges in Slack (#on-call-handoff)
3. 1-hour overlap window for live Q&A
4. Outgoing on-call remains reachable (best-effort) for 2 hours after handoff

---

## Severity Definitions

| Severity | Definition | Examples | Response Time | Resolution Target |
|----------|-----------|----------|---------------|-------------------|
| P0 | Total service outage. All users affected. Revenue impact. | orders-api returning 100% errors, database unreachable, cluster down | 15 min | 1 hour |
| P1 | Partial outage. Significant user impact. Core functionality degraded. | Error rate above P1 burn threshold, significant latency spike, one AZ down | 30 min | 4 hours |
| P2 | Service degraded. Some users affected. Non-critical functionality impaired. | Elevated error rate above P2 threshold, worker processing delays, non-critical dependency failure | 2 hours | 24 hours |
| P3 | Minor issue. Minimal user impact. | Informational alerts, slow burn rate, non-urgent capacity warnings | 24 hours | 5 business days |

### Response Time Definitions

- **Response time** = Time from alert firing to a human acknowledging the alert and beginning investigation
- **Resolution target** = Time from acknowledgment to the service returning to SLO compliance (not necessarily root cause resolution)

---

## Escalation Ladder

### P0 -- Total Outage

```
0 min     Alert fires → Page primary on-call (PagerDuty/Slack)
15 min    No ack → Auto-escalate to secondary on-call
30 min    No ack → Escalate to engineering lead
45 min    No ack → Escalate to engineering manager
60 min    If unresolved → Incident Commander takes over, war room opens
```

### P1 -- Partial Outage

```
0 min     Alert fires → Page primary on-call
30 min    No ack → Auto-escalate to secondary on-call
60 min    If unresolved → Notify engineering lead
2h        If unresolved → Consider escalating to P0
```

### P2 -- Degraded Service

```
0 min     Alert fires → Notify #alerts-warning Slack channel
2h        No ack → Notify primary on-call directly
4h        If unresolved → Escalate to P1
```

### P3 -- Minor Issue

```
0 min     Alert fires → Notify #alerts-info Slack channel
24h       No ack → Add to next standup agenda
```

---

## AlertManager Routing

Alerts are routed to Slack channels based on severity, with inhibition rules to prevent alert storms.

| Severity | Slack Channel | Notification Method |
|----------|--------------|-------------------|
| critical | #alerts-critical | Slack + PagerDuty page |
| warning | #alerts-warning | Slack notification |
| info | #alerts-info | Slack (no notification sound) |

### Inhibition Rules

- A P0/critical alert on a service **suppresses** P1/P2/P3 alerts for the same service. If the whole thing is down, we don't need 15 alerts about its individual components.
- Infrastructure-level alerts (node down, cluster issues) suppress application-level alerts on the affected nodes.

---

## On-Call Responsibilities

### During On-Call

- Acknowledge alerts within the response time for their severity
- Triage: determine severity, assess impact, decide if escalation is needed
- Communicate: post status updates in the incident channel
- Resolve or escalate: fix what you can, escalate what you cannot
- Document: update the incident timeline as you work

### Not On-Call Responsibilities

- On-call does not mean "the person who does all the work." On-call triages and coordinates.
- On-call does not own the postmortem. The Incident Commander assigns that.
- On-call does not deploy fixes alone for P0/P1. The on-call pulls in the relevant team members.

---

## Tools

| Tool | Purpose | Access |
|------|---------|--------|
| Slack | Communication, alert routing, incident channels | All team members |
| Grafana | Dashboards, SLO monitoring, log exploration | `https://grafana.reliabilityos.internal` |
| PagerDuty | Paging, escalation, schedule management | On-call rotation members |
| kubectl | Cluster access for debugging | On-call + designated responders |
| AWS Console | Infrastructure investigation and remediation | Role-based access via SSO |

### Runbook Access

All runbooks are in `/docs/runbooks/` and linked from alert annotations. Every alert that pages on-call must include a `runbook_url` annotation pointing to the relevant procedure.

---

## Compensation and Well-being

### On-Call Load Targets

- No individual should be on-call more than 1 week in 4 (25% of the time)
- Maximum 2 pages per on-call shift is the target. More than that signals a problem with alert quality, not with the on-call engineer.
- If an on-call shift has more than 5 pages, a review is triggered to improve alert signal-to-noise ratio.

### After Incidents

- On-call engineer who handles a P0/P1 during off-hours gets a compensatory half-day off within the same week
- No blame. If an incident reveals a gap, we fix the system, not the person.

### On-Call Health Metrics

Track these monthly:

| Metric | Target | Red Flag |
|--------|--------|----------|
| Pages per shift | < 2 | > 5 |
| Mean time to acknowledge | < 10 min | > 30 min |
| False positive rate | < 20% | > 50% |
| Escalation rate | < 10% | > 30% |
| On-call satisfaction (survey) | > 7/10 | < 5/10 |
