# Architecture

## System Overview

```
                                    OBSERVABILITY
                          +---------------------------------+
                          |  Prometheus    Grafana    Loki   |
                          |  (metrics)    (dashboards) (logs)|
                          |       Tempo       Alloy         |
                          |      (traces)  (log collector)  |
                          |    Blackbox Exporter (probes)   |
                          +-------^-----------^-------------+
                                  |           |
                                  | scrape    | ship logs
                                  |           |
User ──> NGINX Ingress ──> orders-api ──────────────────────────> PostgreSQL
              |              (FastAPI)                                 ^
              |                  |                                     |
              |                  | publish: order.created              |
              |                  v                                     |
              |              RabbitMQ ─────────> worker ───────────────+
              |             (message broker)   (Celery)    write order status
              |                                   |
              |                                   v
              |                                 Redis
              |                            (result backend)
              |
              |         RELIABILITY LAYER
              |    +---------------------------+
              +----| Argo Rollouts (canary)    |
                   | KEDA (queue autoscaling)  |
                   | HPA (CPU autoscaling)     |
                   | Chaos Mesh (fault inject) |
                   +---------------------------+

         DELIVERY
  GitHub ──> Actions ──> ECR ──> ArgoCD (app-of-apps) ──> EKS
  (push)     (CI)      (images)   (GitOps sync)         (cluster)
```

## Components

| Component | Purpose | Namespace |
|---|---|---|
| orders-api | REST API for order management (FastAPI) | `reliabilityos` |
| worker | Async order processor (Celery) | `reliabilityos` |
| PostgreSQL | Persistent order storage | `reliabilityos` |
| RabbitMQ | Message broker for order events | `reliabilityos` |
| Redis | Celery result backend | `reliabilityos` |
| Prometheus | Metrics collection and SLI recording rules | `monitoring` |
| Grafana | Dashboards (SLO overview, engineering, capacity, executive) | `monitoring` |
| Alertmanager | Alert routing to Slack with severity-based channels | `monitoring` |
| Blackbox Exporter | Synthetic HTTP probes against orders-api | `monitoring` |
| Loki | Log aggregation | `logging` |
| Alloy | Log collection agent (DaemonSet), extracts trace_id for correlation | `logging` |
| Tempo | Distributed tracing backend | `tracing` |
| ArgoCD | GitOps continuous delivery (app-of-apps) | `argocd` |
| Argo Rollouts | Canary deployment controller | `argo-rollouts` |
| KEDA | Event-driven autoscaler for worker | `keda` |
| Chaos Mesh | Chaos engineering experiments | `chaos-mesh` |
| Grafana Dashboards | ConfigMap-based dashboard provisioning | `monitoring` |

## Data Flow: Order Lifecycle

1. **Create** --- Client sends `POST /orders` to orders-api via NGINX Ingress
2. **Persist** --- orders-api writes the order to PostgreSQL with status `pending`
3. **Publish** --- orders-api publishes an `order.created` message to RabbitMQ
4. **Consume** --- Celery worker picks up the message from the `order.created` queue
5. **Process** --- Worker executes order processing logic, stores the task result in Redis
6. **Complete** --- Worker updates the order status in PostgreSQL to `completed` (or `failed` after retries, routing to the dead-letter queue)

At each step, the application emits structured JSON logs (collected by Alloy), Prometheus metrics (scraped via ServiceMonitor/PodMonitor), and OpenTelemetry traces (exported to Tempo via OTLP).

## Observability Pipeline

### Metrics

Prometheus scrapes orders-api (ServiceMonitor) and worker (PodMonitor) for application metrics: `http_requests_total`, `http_request_duration_seconds`, `orders_processed_total`, `order_processing_duration_seconds`. SLI recording rules pre-compute availability, latency, and error rates at multiple windows (5m, 30m, 1h, 6h, 1d). Burn-rate rules drive multi-window alerts.

Blackbox Exporter runs synthetic HTTP probes against the orders-api endpoint, alerting on downtime or slow responses independently of internal metrics.

### Logs

Alloy runs as a DaemonSet on every node, collecting container logs via the Kubernetes API. It parses structured JSON fields (`trace_id`, `span_id`, `level`, `service`) and forwards enriched log streams to Loki. Grafana queries Loki with derived fields that link `trace_id` values directly to Tempo traces.

### Traces

Both orders-api and worker export OpenTelemetry traces to Tempo via OTLP (gRPC on port 4317). Grafana's Tempo datasource is configured with `tracesToLogsV2`, enabling bidirectional navigation: click a trace to see correlated logs, or click a `trace_id` in logs to open the trace.

### Correlation

The three signals are tied together by `trace_id`:

- **Logs to Traces** --- Alloy extracts `trace_id` from JSON logs; Grafana Loki derived fields link to Tempo
- **Traces to Logs** --- Tempo datasource uses `tracesToLogsV2` to query Loki by trace and span ID
- **Metrics to Traces** --- Exemplars on Prometheus metrics can link to individual trace IDs in Grafana

## Deployment Pipeline

```
Developer pushes to main (apps/**)
        |
        v
GitHub Actions: detect-changes
        |
        +--[orders-api changed?]---> Build & push to ECR (sha-<commit>)
        +--[worker changed?]-------> Build & push to ECR (sha-<commit>)
        |
        v
Update Helm values.yaml with new image tag
        |
        v
Git commit + push (automated by CI)
        |
        v
ArgoCD detects drift (watches main branch)
        |
        v
Sync: Helm template → Kubernetes manifests
        |
        v
Argo Rollouts: canary strategy
   10% traffic → pause 2m → analysis (error rate < 1%, p95 < 200ms)
   30% traffic → pause 2m → analysis
   60% traffic → pause 2m → analysis
  100% traffic → promotion complete
        |
        v
If analysis fails → automatic rollback to previous ReplicaSet
```

### Canary Analysis

Each canary step runs an `AnalysisTemplate` that queries Prometheus for two conditions:

- **Error rate** below 1% (`http_requests_total` with 5xx status)
- **p95 latency** below 200ms (`http_request_duration_seconds` histogram)

The analysis runs 4 measurements at 30-second intervals, tolerating up to 2 failures before triggering a rollback.

## Autoscaling

| Target | Mechanism | Trigger | Range |
|---|---|---|---|
| orders-api | HPA | CPU utilization | 2--10 replicas |
| worker | KEDA ScaledObject | RabbitMQ `order.created` queue length > 5 | 1--5 replicas |

KEDA polls the RabbitMQ queue every 15 seconds with a 60-second cooldown period, using AMQP authentication via a Kubernetes Secret.

## Infrastructure

Terraform is organized into three sequential layers:

| Layer | Path | Resources |
|---|---|---|
| 01-vpc | `terraform/01-vpc/` | VPC, public/private subnets, NAT Gateway, VPC Endpoints |
| 02-cluster | `terraform/02-cluster/` | EKS cluster, node group, OIDC, VPC CNI, EBS CSI, NGINX Ingress, External DNS, ArgoCD bootstrap, Loki/Tempo IAM |
| 03-ecr | `terraform/03-ecr/` | ECR repositories for orders-api and worker |

## Alerting Strategy

Alerts follow the multi-window, multi-burn-rate approach from the Google SRE Workbook:

| Alert | Burn Rate | Window | Severity | Meaning |
|---|---|---|---|---|
| OrdersAPIHighBurnRate_Critical | 14.4x | 1h + 5m | critical | Budget exhausted in ~2 hours |
| OrdersAPIHighBurnRate_Warning | 6x | 6h + 30m | warning | Budget exhausted in ~5 days |
| OrdersAPIHighBurnRate_Info | >1x | 1d + 6h | info | Consuming faster than sustainable |
| OrdersAPIHighLatency | p95 > 200ms | 5m | warning | Latency SLO breach |
| WorkerHighFailureRate | 6x | 1h + 5m | warning | Worker burning error budget |
| OrdersAPIEndpointDown | probe_success=0 | 1m | critical | Synthetic probe failing |
| DeadLetterQueueNotEmpty | DLQ messages > 0 | 5m | warning | Failed orders in dead-letter queue |

All alerts route to `#reliabilityos-alerts` in Slack via Alertmanager, with severity-based formatting, runbook links, and dashboard URLs. Critical alerts inhibit warning and info alerts for the same service.
