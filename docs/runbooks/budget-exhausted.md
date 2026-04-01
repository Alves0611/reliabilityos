# Runbook: Error Budget Exhausted

## Alert
- `OrdersAPIHighBurnRate_Info` (sustained burn rate > 1x)

## Impact
Error budget is being consumed faster than the monthly allocation allows. If this continues, the SLO will be violated before the end of the measurement window.

## Context
- **SLO Target**: 99.9% availability (43.2 minutes of downtime per 30 days)
- **Error Budget**: 0.1% of total requests can fail
- **Current burn rate**: check `slo:orders_api:burn_rate:1h` in Grafana

## Diagnosis Steps

1. **Check current budget status**
   - Grafana → SLO Overview → Error Budget row
   - Note: remaining %, burn rate, projected exhaustion date

2. **Identify the cause of budget consumption**
   - Was there a recent incident? Check postmortem repository
   - Is there an ongoing slow degradation? Check error rate trend over last 7 days
   - Are there specific endpoints or error codes driving consumption?

3. **Review recent changes**
   ```bash
   # Recent deployments
   kubectl -n reliabilityos rollout history deployment/orders-api

   # Git log for recent changes
   git log --oneline -20
   ```

## Decision Framework

| Budget Remaining | Action |
|-----------------|--------|
| > 50% | Monitor. No immediate action needed. |
| 25-50% | Review and address top error sources. Consider pausing non-critical deployments. |
| 10-25% | Freeze non-critical deployments. Prioritize reliability work. |
| < 10% | Full deployment freeze except critical fixes. All engineering effort on reliability. |

## Mitigation

1. **Identify and fix the top error source** — usually one endpoint or one dependency accounts for most budget consumption

2. **If budget is near exhaustion**:
   - Communicate to stakeholders
   - Freeze feature deployments
   - Focus sprint on reliability improvements

3. **If budget was consumed by a single incident**:
   - Conduct postmortem
   - Implement preventive action items
   - Consider if SLO target is realistic

## Follow-up
- Review SLO targets in next monthly review
- Update capacity planning based on learnings
- Document in postmortem if applicable
