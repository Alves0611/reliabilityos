# ReliabilityOS

ReliabilityOS is a production-grade SRE portfolio project that demonstrates end-to-end reliability engineering on Kubernetes. It runs a FastAPI-based order processing system on AWS EKS, instrumented with SLO-driven alerting, full observability (metrics, logs, traces), canary deployments, chaos engineering, and event-driven autoscaling --- all managed through GitOps.

## What It Demonstrates

- **SLO-Based Alerting** --- Multi-window burn-rate alerts with error budget tracking, routed to Slack by severity
- **Full Observability Stack** --- Correlated metrics (Prometheus), logs (Loki), and traces (Tempo) with Grafana dashboards
- **Canary Deployments** --- Progressive rollouts with automated Prometheus analysis at each traffic shift
- **Chaos Engineering** --- Controlled fault injection via Chaos Mesh with structured gameday experiments
- **Event-Driven Autoscaling** --- Worker pods scale on RabbitMQ queue depth (KEDA) alongside CPU-based HPA for the API
- **GitOps Delivery** --- ArgoCD app-of-apps pattern with automated sync, self-heal, and pruning
- **Infrastructure as Code** --- Terraform modules for VPC, EKS cluster, and ECR repositories
- **CI/CD Pipeline** --- GitHub Actions with change detection, Docker build/push to ECR, and automated Helm values update

## Tech Stack

| Layer | Components |
|---|---|
| Application | FastAPI (orders-api), Celery (worker), Python |
| Data | PostgreSQL, RabbitMQ, Redis |
| Orchestration | AWS EKS, Helm, ArgoCD (app-of-apps) |
| Observability | Prometheus, Grafana, Loki, Tempo, Alloy, Blackbox Exporter |
| Reliability | Argo Rollouts (canary), Chaos Mesh, KEDA, HPA |
| Alerting | Alertmanager with multi-window burn-rate rules, Slack integration |
| Infrastructure | Terraform (VPC, EKS, ECR), AWS |
| CI/CD | GitHub Actions, Amazon ECR |

## Documentation

- [Architecture](architecture.md) --- System design, component map, and data flows
- **SRE Practices**
    - [SLOs & SLIs](sre/slos.md) --- Service level objectives and indicators
    - [Error Budgets](sre/error-budgets.md) --- Budget tracking and policies
    - [On-Call](sre/on-call.md) --- On-call procedures
    - [Incident Response](sre/incident-response.md) --- Incident management process
    - [Change Policy](sre/change-policy.md) --- Change management guidelines
    - [Cost Analysis](sre/cost-analysis.md) --- Infrastructure cost breakdown
- **Runbooks**
    - [High Error Rate](runbooks/high-error-rate.md) --- Triage and mitigation for elevated 5xx rates
    - [High Latency](runbooks/high-latency.md) --- Diagnosis steps for p95 latency breaches
    - [Budget Exhausted](runbooks/budget-exhausted.md) --- Response when error budget is depleted
- **Templates**
    - [Postmortem](playbooks/postmortem.md) --- Incident postmortem template
    - [Root Cause Analysis](playbooks/rca.md) --- RCA template
