# Runbook: High Latency

## Alert
- `OrdersAPIHighLatency` (p95 > 200ms for 5 minutes)
- `OrdersAPISlowResponse` (synthetic probe > 1s for 3 minutes)

## Impact
Users are experiencing slow response times. API SLO for latency is being violated.

## Diagnosis Steps

1. **Identify slow endpoints**
   - Grafana → Engineering Dashboard → Latency row
   - PromQL: `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{namespace="reliabilityos"}[5m])) by (le, endpoint))`

2. **Check for resource saturation**
   ```bash
   kubectl -n reliabilityos top pods
   ```
   - High CPU → compute bottleneck
   - High memory → possible GC pressure or memory leak

3. **Check database performance**
   - Grafana → Explore → Tempo: filter by `service.name=orders-api`, sort by duration
   - Look for slow SQL spans (SQLAlchemy instrumentation)

4. **Check network and dependencies**
   ```bash
   # DNS resolution time
   kubectl -n reliabilityos exec deploy/orders-api -- nslookup postgresql.reliabilityos.svc.cluster.local

   # RabbitMQ connection latency
   kubectl -n reliabilityos logs -l app=orders-api --tail=50 | jq 'select(.message | contains("rabbitmq"))'
   ```

5. **Check for noisy neighbor**
   ```bash
   kubectl top nodes
   ```

## Mitigation

1. **If database is slow**: check connection pool, slow queries, missing indexes

2. **If compute-bound**: scale horizontally
   ```bash
   kubectl -n reliabilityos scale deployment/orders-api --replicas=4
   ```

3. **If network-related**: check node health and CNI

4. **If single endpoint**: check for N+1 queries or missing pagination

## Escalation
- If database-related, escalate to database team
- If infrastructure-related, escalate to platform team
