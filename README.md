# ReliabilityOS

Production-grade SRE platform demonstrating observability, SLOs, incident response, and reliability engineering on Kubernetes.


![ReliabilityOS Architecture](images/reliabilityos.drawio.svg)

## What This Project Demonstrates

| Area | Implementation |
|------|---------------|
| **Observability** | Prometheus metrics, Loki logs, Tempo traces — correlated via trace_id |
| **SLOs** | 99.9% availability, p95 < 200ms, error budget tracking with burn-rate alerts |
| **Alerting** | Multi-window burn-rate (P1/P2/P3), Slack notifications, runbooks linked |
| **Dashboards** | SLO Overview, Engineering (drill-down), Executive (business), Capacity |
| **Progressive Delivery** | Argo Rollouts canary (10% → 30% → 60% → 100%) with Prometheus analysis |
| **Chaos Engineering** | Chaos Mesh: pod-kill, network latency, CPU stress — with documented hypotheses |
| **Autoscaling** | HPA (CPU) for API, KEDA (RabbitMQ queue depth) for worker |
| **IaC** | Terraform modules (VPC, EKS, ECR), GitOps with ArgoCD app-of-apps |
| **CI/CD** | GitHub Actions: build, push to ECR, auto-update Helm values |
| **Incident Response** | IMAG model, severity P0-P3, postmortem templates, escalation ladder |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Application | Python 3.12, FastAPI, Celery, SQLAlchemy |
| Data | PostgreSQL 16, RabbitMQ 3.13, Redis 7 |
| Orchestration | AWS EKS (K8s 1.34), Helm, ArgoCD |
| Observability | Prometheus, Grafana, Loki, Tempo, Alloy, Blackbox Exporter |
| Reliability | Argo Rollouts, Chaos Mesh, KEDA, HPA |
| Infrastructure | Terraform, AWS (VPC, EKS, ECR, S3, IAM) |
| CI/CD | GitHub Actions |

## Quick Start

### Prerequisites

- AWS account with CLI configured
- Terraform >= 1.5
- kubectl
- Helm 3

### Deploy Infrastructure

```bash
cd terraform/01-vpc && terraform init && terraform apply
cd ../02-cluster && terraform init && terraform apply
cd ../03-ecr && terraform init && terraform apply
```

### Configure Cluster Access

```bash
aws eks update-kubeconfig --name studying-cluster --region us-east-1
```

### Create Required Secrets

```bash
kubectl create secret generic slack-webhook -n monitoring \
  --from-literal=url='https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
```

### Verify Deployment

ArgoCD automatically deploys all applications via the app-of-apps pattern. Check status:

```bash
kubectl get applications -n argocd
```

### Access Services

| Service | URL |
|---------|-----|
| Orders API | https://orders.gabrielstudying.click |
| Grafana | https://grafana.gabrielstudying.click |
| ArgoCD | https://argocd.gabrielstudying.click |

## Documentation

Full documentation available via [Backstage TechDocs](docs/) including SLIs/SLOs, error budgets, incident response, on-call procedures, runbooks, postmortem templates, root cause analysis, and architecture details.

## Project Structure

```
terraform/          # IaC (VPC, EKS, ECR, IRSA)
apps/               # Application source (orders-api, worker)
helm/               # Helm values for all services
argocd/             # ArgoCD Application manifests
chaos/              # Chaos Mesh experiment definitions
docs/               # SRE documentation (TechDocs)
.github/workflows/  # CI/CD pipelines
```
