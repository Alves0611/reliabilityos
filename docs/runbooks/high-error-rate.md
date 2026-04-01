# Runbook: High Error Rate

## Alert
- `OrdersAPIHighBurnRate_Critical` (14.4x burn rate, ~2h to budget exhaustion)
- `OrdersAPIHighBurnRate_Warning` (6x burn rate, ~5d to budget exhaustion)
- `WorkerHighFailureRate` (worker error budget burning at 6x)

## Impact
Users are experiencing elevated 5xx errors. Orders may be failing to process.

## Diagnosis Steps

1. **Check error rate and recent changes**
   ```bash
   # Recent deployments
   kubectl -n reliabilityos rollout history deployment/orders-api

   # Pod status
   kubectl -n reliabilityos get pods -l app=orders-api
   kubectl -n reliabilityos get pods -l app=worker
   ```

2. **Check application logs**
   ```bash
   # orders-api errors
   kubectl -n reliabilityos logs -l app=orders-api --tail=100 | jq 'select(.level == "ERROR")'

   # worker errors
   kubectl -n reliabilityos logs -l app=worker --tail=100 | jq 'select(.level == "ERROR")'
   ```

   Or use Grafana → Explore → Loki: `{namespace="reliabilityos"} |= "error" | json`

3. **Check dependencies**
   ```bash
   # PostgreSQL
   kubectl -n reliabilityos exec -it deploy/orders-api -- python -c "import asyncpg; print('DB OK')"

   # RabbitMQ
   kubectl -n reliabilityos get pods -l app.kubernetes.io/name=rabbitmq

   # Redis
   kubectl -n reliabilityos get pods -l app.kubernetes.io/name=redis
   ```

4. **Check resource saturation**
   - Grafana → Engineering Dashboard → Saturation row
   - `kubectl -n reliabilityos top pods`

## Mitigation

1. **If caused by bad deploy**: rollback
   ```bash
   kubectl -n reliabilityos rollout undo deployment/orders-api
   ```

2. **If caused by dependency failure**: restart the dependency
   ```bash
   kubectl -n reliabilityos rollout restart statefulset/postgresql
   ```

3. **If caused by resource exhaustion**: scale up
   ```bash
   kubectl -n reliabilityos scale deployment/orders-api --replicas=4
   ```

## Escalation
- If not resolved within 15 minutes, escalate to infrastructure team
- If database-related, escalate to database team
