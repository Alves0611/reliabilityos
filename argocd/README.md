# ArgoCD — GitOps Stack

App-of-apps pattern managing all cluster workloads via ArgoCD.

![ArgoCD Stack](../images/stack-argocd.drawio.svg)

## Sync Waves

| Wave | Application | Chart | Namespace |
|------|-------------|-------|-----------|
| 1 | Loki | grafana/loki 6.29.0 | logging |
| 1 | Tempo | grafana/tempo 1.24.4 | tracing |
| 2 | kube-prometheus-stack | prometheus-community 72.4.0 | monitoring |
| 2 | Alloy | grafana/alloy 0.12.5 | logging |
| 2 | Blackbox Exporter | prometheus-community 9.4.0 | monitoring |
| 2 | Chaos Mesh | chaos-mesh 2.8.2 | chaos-mesh |
| 2 | KEDA | kedacore 2.19.0 | keda |
| 3 | PostgreSQL | bitnami 18.5.12 | reliabilityos |
| 3 | Redis | bitnami 25.3.8 | reliabilityos |
| 3 | RabbitMQ | bitnami 16.0.5 | reliabilityos |
| 3 | Argo Rollouts | argoproj 2.39.1 | argo-rollouts |
| 3 | Grafana Dashboards | custom | monitoring |
| 4 | orders-api | custom | reliabilityos |
| 4 | worker | custom | reliabilityos |
