# Incident Response

## IMAG Model

ReliabilityOS uses the IMAG (Incident Management for Awesome Groups) model. Four distinct roles ensure no single person is overwhelmed and nothing falls through the cracks during an incident.

---

## Roles

### Incident Commander (IC)

The IC owns the incident from declaration to resolution. They do not fix anything -- they coordinate.

**Responsibilities:**
- Declare the incident and assign severity
- Open the incident Slack channel
- Assign all other IMAG roles
- Make decisions on mitigation strategy (rollback, failover, scale up)
- Authorize emergency changes
- Decide when to escalate or de-escalate severity
- Declare the incident resolved
- Assign postmortem owner

**The IC does not:**
- Debug code or SSH into servers
- Write status updates (that's Comms Lead)
- Investigate root cause during the incident (that's Ops Lead)

### Communications Lead (Comms)

The Comms Lead is the single source of truth for anyone outside the war room.

**Responsibilities:**
- Post status updates at the defined cadence (see below)
- Update the status page
- Communicate with stakeholders who are not in the war room
- Manage external communication if customer-facing impact exists
- Keep the incident channel topic updated with current status
- Coordinate with support teams if user reports are coming in

**Update Format:**
```
Status Update #N | [Severity] | [Timestamp UTC]
Impact: [what users are experiencing]
Current action: [what we are doing right now]
Next update: [when]
```

### Operations Lead (Ops)

The Ops Lead is the technical point person. They lead the debugging and remediation work.

**Responsibilities:**
- Lead technical investigation and root cause identification
- Coordinate with other engineers pulled into the incident
- Propose mitigation actions to the IC for approval
- Execute approved changes (rollbacks, config changes, scaling)
- Verify that mitigations are working
- Provide technical summaries to the IC and Comms Lead

### Scribe

The Scribe records everything. Their notes become the foundation of the postmortem.

**Responsibilities:**
- Maintain a real-time timeline of events in the incident channel
- Record all decisions and who made them
- Record all actions taken and their outcomes
- Note any theories proposed and whether they were confirmed or ruled out
- Capture timestamps for key events (detection, response, mitigation, resolution)
- Compile the raw incident record for the postmortem

**Timeline Format:**
```
[HH:MM UTC] [Actor] [Action/Decision]
[14:23 UTC] @ops-lead — Rolled back orders-api to v1.2.3
[14:25 UTC] @ic — Error rate dropping, monitoring for 10 minutes
[14:35 UTC] @ic — Confirmed recovery. Declaring incident resolved.
```

---

## Incident Channel

### Naming Convention

```
#inc-YYYYMMDD-service
```

Examples:
- `#inc-20260401-orders-api`
- `#inc-20260315-worker`
- `#inc-20260220-infrastructure`

For multiple incidents on the same service on the same day, append a sequence number:
- `#inc-20260401-orders-api-2`

### Channel Setup

When the IC opens the incident channel:

1. Set the channel topic:
   ```
   [P1] orders-api elevated error rate | IC: @name | Ops: @name | Comms: @name | Scribe: @name
   ```
2. Pin the initial incident description
3. Post the relevant Grafana dashboard links
4. Post links to relevant runbooks

### Who Joins the Channel

- All IMAG role holders (required)
- Subject matter experts pulled in by the Ops Lead (as needed)
- Engineering lead (observer, available for escalation)
- No one else should be actively posting -- observers can react with emoji but should not add noise

---

## Status Update Cadence

| Severity | Update Frequency | Audience |
|----------|-----------------|----------|
| P0 | Every 15 minutes | Incident channel + status page + stakeholder DMs |
| P1 | Every 15 minutes | Incident channel + status page |
| P2 | Every 30 minutes | Incident channel |
| P3 | On meaningful progress | Incident channel |

Updates continue until the incident is resolved, even if the update is "no change, still investigating."

---

## Incident Lifecycle

### 1. Detection

An alert fires or a user report comes in. The on-call engineer triages.

### 2. Declaration

If the issue meets the threshold for P0-P2, the on-call declares an incident:
- Creates the incident channel
- Assigns initial IMAG roles (on-call typically starts as both IC and Ops, then hands off IC as more people join)
- Posts initial assessment

### 3. Triage

The IC confirms severity and ensures all roles are staffed. The Ops Lead begins investigation.

### 4. Mitigation

Priority is restoring service, not finding root cause. Common mitigations:
- Rollback the last deployment
- Scale up resources
- Disable a feature flag
- Failover to a healthy component
- Apply a known workaround from a runbook

### 5. Resolution

The IC declares the incident resolved when:
- The service is back within SLO compliance
- The immediate mitigation is stable
- No further user impact is observed

Resolution does not mean root cause is found. It means the bleeding has stopped.

### 6. Postmortem

Within 48 hours of resolution, the assigned owner produces a blameless postmortem. See `/docs/templates/` for the postmortem template.

---

## War Room Setup

For P0 incidents, the IC may call a synchronous war room (video call).

**War room rules:**
- IC controls the call. One speaker at a time.
- Mute when not speaking.
- Ops Lead shares screen when debugging.
- All decisions are repeated by the IC and confirmed by the Scribe in the incident channel.
- Side conversations happen in threads, not in the main channel or the call.

---

## Handoff Procedures

### Shift Handoff During Active Incident

If an incident spans an on-call shift change:

1. Outgoing on-call stays on until a clean handoff point (not mid-debug)
2. Incoming on-call reads the incident timeline in the channel
3. The IC introduces the incoming on-call to the current state
4. Formal handoff: "I am handing Ops Lead to @incoming. @incoming, do you accept?"
5. Incoming confirms: "Accepted. I have context on X, Y, Z."
6. Scribe records the handoff

### Role Handoff During Incident

If the IC needs to hand off (fatigue, expertise needed elsewhere):

1. IC identifies the new IC
2. IC briefs the new IC on current state, open actions, and pending decisions
3. IC announces in channel: "Handing IC to @new-ic effective now."
4. New IC confirms and takes over

---

## After the Incident

| Action | Owner | Deadline |
|--------|-------|----------|
| Postmortem draft | Assigned by IC | 48 hours |
| Postmortem review | Team | 5 business days |
| Action items filed | Postmortem owner | With the postmortem |
| Action items completed | Assigned owners | Per priority (P0 actions within 1 week) |
| Incident data added to SLO tracking | On-call | Same day |
