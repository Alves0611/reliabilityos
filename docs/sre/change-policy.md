# Change Management Policy

## Change Categories

Every change to production falls into one of three categories. The category determines the approval process, deployment window, and rollback requirements.

### Standard Changes

Pre-approved, low-risk changes that follow a well-documented procedure. No per-change approval needed.

**Examples:**
- Image tag updates via CI/CD pipeline
- Scaling replicas within pre-defined bounds (2-10 pods)
- Feature flag toggles
- Certificate rotations (automated)
- Dependency updates that pass all tests

**Requirements:**
- Automated pipeline handles deployment
- Automated rollback on health check failure
- Change is logged for audit trail

### Normal Changes

Changes that require review and approval before deployment. Most feature work and infrastructure modifications fall here.

**Examples:**
- New API endpoints or behavior changes
- Database schema migrations
- Kubernetes manifest changes (resource limits, new services)
- Terraform infrastructure changes
- Helm chart version upgrades
- Alerting rule modifications

**Requirements:**
- Pull request with at least one approval
- CI pipeline passes (tests, lint, security scan)
- Deployment during approved window
- Rollback plan documented in the PR
- On-call engineer is aware of the change

### Emergency Changes

Changes deployed outside normal process to restore service during an active incident. Speed over process, but with accountability.

**Examples:**
- Hotfix for an active P0/P1 incident
- Emergency rollback
- Config change to mitigate ongoing impact

**Requirements:**
- Approved by the Incident Commander
- Deployed by the Ops Lead or designated responder
- Retroactive PR and review within 24 hours
- Documented in the incident postmortem

---

## Risk Assessment Matrix

Every normal change is assessed on two dimensions: **blast radius** (how much breaks if it goes wrong) and **recovery time** (how long to roll back or fix).

|  | Recovery: Fast (< 5 min) | Recovery: Medium (5-30 min) | Recovery: Slow (> 30 min) |
|--|--------------------------|---------------------------|--------------------------|
| **Blast Radius: Low** (single component, < 10% users) | Low Risk | Low Risk | Medium Risk |
| **Blast Radius: Medium** (multiple components, 10-50% users) | Low Risk | Medium Risk | High Risk |
| **Blast Radius: High** (full service, > 50% users) | Medium Risk | High Risk | Critical Risk |

### Approval Requirements by Risk Level

| Risk Level | Approvals | Additional Requirements |
|------------|-----------|------------------------|
| Low | 1 peer review | Standard CI checks |
| Medium | 1 peer review + on-call ack | Canary deployment required |
| High | 2 peer reviews + engineering lead | Canary deployment + manual verification gate |
| Critical | 2 peer reviews + engineering lead + SRE sign-off | Canary + staged rollout + dedicated monitoring during rollout |

---

## Deployment Windows

### Preferred Windows

| Day | Window (UTC) | Notes |
|-----|-------------|-------|
| Monday | 14:00 - 18:00 | Avoid early Monday (weekend issues may surface) |
| Tuesday | 10:00 - 18:00 | Full deployment window |
| Wednesday | 10:00 - 18:00 | Full deployment window |
| Thursday | 10:00 - 16:00 | Shorter window, avoid late Thursday deploys |
| Friday | None | No non-standard deployments on Friday |
| Weekend | Emergency only | Requires IC approval |

### Rationale

Deployments happen when the team is alert, available, and has time to observe the rollout. No Friday deploys because no one wants to debug a rollout over the weekend.

---

## Freeze Periods

### Automatic Freezes

- **Error budget exhausted** -- Deployment freeze for the affected service until budget recovers above 25%
- **Active P0/P1 incident** -- No unrelated changes to the affected service or its dependencies
- **On-call handoff window** -- No deployments during the 1-hour handoff overlap

### Planned Freezes

- **End-of-quarter business events** -- Coordinate with product team for blackout windows around critical business periods
- **Infrastructure migrations** -- Freeze application deployments during major infrastructure changes (node upgrades, cluster migrations)

---

## Canary Strategy

All medium-risk and above changes use canary deployments.

### Canary Gates

```
Stage 1: Deploy to canary (1 pod, ~10% traffic)
  Gate: 5 minutes, error rate < 1%, p95 latency < 200ms
  Fail: automatic rollback

Stage 2: Expand to 25% of pods
  Gate: 10 minutes, error rate delta < 0.5% vs baseline
  Fail: automatic rollback

Stage 3: Expand to 50% of pods
  Gate: 10 minutes, no SLO violation detected
  Fail: automatic rollback

Stage 4: Full rollout (100%)
  Gate: 15 minutes observation
  Fail: manual decision (rollback or investigate)
```

### Canary Metrics

The following metrics are compared between canary and baseline:

| Metric | Threshold | Action on Breach |
|--------|-----------|-----------------|
| Error rate (5xx) | > 1% absolute or > 2x baseline | Auto rollback |
| p95 latency | > 200ms or > 1.5x baseline | Auto rollback |
| Pod restart count | > 0 | Auto rollback |
| CPU/memory usage | > 2x baseline | Alert, manual decision |

### Manual Verification Gates

For high and critical risk changes, the canary process includes a manual gate after Stage 2. The deployer must explicitly confirm:

1. Dashboards show expected behavior
2. Logs show no unexpected errors
3. Business metrics (order count, processing rate) are within normal range

---

## Rollback Policy

Every deployment must have a rollback path. The rollback method depends on the change type.

| Change Type | Rollback Method | Expected Time |
|-------------|----------------|---------------|
| Application deployment | Revert to previous image tag | < 2 min |
| Helm values change | `helm rollback` to previous revision | < 2 min |
| Terraform change | `terraform apply` with previous state | 5-15 min |
| Database migration | Forward-fix migration (backward migrations are a last resort) | Varies |
| Feature flag | Toggle off | < 30 sec |

### Rollback Triggers

Automatic rollback is triggered when:
- Canary gates fail during deployment
- Health check failures exceed threshold after deployment
- Error rate doubles within 10 minutes of deployment

Manual rollback is initiated when:
- On-call engineer observes degradation correlated with a recent change
- SLO burn rate enters P1 territory after a deployment
