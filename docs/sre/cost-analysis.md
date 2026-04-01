# Cost vs Reliability Analysis

## The Cost of Nines

Each additional nine of availability requires roughly 10x more investment in infrastructure, tooling, and operational effort. The relationship is not linear -- it is exponential.

| Target | Allowed Downtime (30d) | Infrastructure Multiplier | What It Takes |
|--------|----------------------|--------------------------|---------------|
| 99% | 7.2 hours | 1x (baseline) | Basic health checks, single-AZ deployment, manual recovery |
| 99.9% | 43.2 minutes | 3-5x | Multi-AZ deployment, automated failover, SLO monitoring, on-call rotation |
| 99.99% | 4.3 minutes | 10-20x | Multi-region active-active, automated remediation, redundant dependencies, chaos engineering program |
| 99.999% | 26 seconds | 50-100x | Custom infrastructure, dedicated SRE team, zero-downtime everything, extensive testing at every layer |

### What ReliabilityOS Runs

ReliabilityOS targets 99.9% for orders-api and 99.5% for the worker. This places us in the 3-5x multiplier range, which is the sweet spot for a service that matters but does not require financial-sector uptime.

---

## The Economic Optimum

There is a point where the cost of additional reliability exceeds the cost of the downtime it prevents. That is the economic optimum -- the point where you should stop adding nines.

```
Total Cost = Cost of Reliability Investment + Cost of Downtime

Where:
  Cost of Downtime = (Minutes of downtime) x (Revenue per minute) x (Reputation multiplier)
  Cost of Reliability = Infrastructure + Tooling + Engineering time
```

### Finding the Right Target

| Question | If Yes | If No |
|----------|--------|-------|
| Does 1 minute of downtime lose money directly? | Target 99.99%+ | 99.9% is likely sufficient |
| Are users paying for an SLA? | Target must exceed SLA by at least one nine | SLO-driven, no external commitment |
| Is the service async/queued? | Lower target is fine (messages are durable) | Higher target needed |
| Are there retries in the client? | Some failures are absorbed, target can be lower | Every failure hits the user |
| Is there a fallback or degraded mode? | Availability target can focus on the critical path | Full service must be up |

For ReliabilityOS:
- orders-api is synchronous and user-facing --> 99.9%
- worker is async with SQS durability and DLQ --> 99.5%
- Neither has a paid SLA --> SLO-driven internally

---

## SLO Differentiation by Service Criticality

Not every service deserves the same reliability target. Over-investing in reliability for non-critical services wastes money. Under-investing for critical services loses money.

| Tier | SLO Range | Characteristics | Examples in ReliabilityOS |
|------|-----------|-----------------|--------------------------|
| Tier 1 -- Critical | 99.9% - 99.95% | User-facing, revenue-impacting, no fallback | orders-api |
| Tier 2 -- Important | 99.5% - 99.9% | Async processing, has retry/DLQ safety net | worker |
| Tier 3 -- Best Effort | 95% - 99% | Internal tools, reporting, batch jobs | Monitoring dashboards, log aggregation |

### Resource Allocation by Tier

| Investment Area | Tier 1 | Tier 2 | Tier 3 |
|-----------------|--------|--------|--------|
| Multi-AZ deployment | Required | Required | Optional |
| Automated failover | Required | Best effort | Not needed |
| On-call pages | P0-P2 | P1-P3 | P3 or async notification |
| Canary deployments | Required | Recommended | Not needed |
| Chaos testing | Regular | Periodic | None |
| Error budget tracking | Active | Active | Passive |

---

## Instance Mix Strategy

AWS costs are heavily influenced by the purchasing model. A well-tuned mix reduces spend by 40-60% compared to running everything on-demand.

### Recommended Mix for EKS

| Instance Type | Use Case | Savings vs On-Demand | Risk |
|--------------|----------|---------------------|------|
| Reserved Instances (1yr) | Baseline capacity: control plane, monitoring, minimum app replicas | 30-40% | Committed spend, no flexibility |
| On-Demand | Burst capacity, new workloads being right-sized, nodes that need stability | 0% (baseline) | Most expensive per hour |
| Spot Instances | Stateless workers, batch processing, non-critical workloads | 60-90% | Can be interrupted with 2-min notice |

### ReliabilityOS Instance Allocation

```
Cluster Capacity Planning:

  Baseline (Reserved):   40% of total capacity
  ├── EKS system pods (CoreDNS, kube-proxy, etc.)
  ├── Monitoring stack (Prometheus, Grafana)
  └── Minimum replicas for orders-api (2 pods)

  Flexible (On-Demand):  30% of total capacity
  ├── orders-api scaling replicas (pods 3-6)
  ├── Tier 1 workloads that need guaranteed availability
  └── New services being right-sized

  Cost-Optimized (Spot): 30% of total capacity
  ├── Worker pods (tolerant of interruption, SQS handles redelivery)
  ├── CI/CD runners
  └── Non-critical batch jobs
```

### Spot Instance Strategy for Workers

The worker is the ideal spot instance workload:
- Messages are durable in SQS -- if the instance dies, messages go back to the queue
- Processing is idempotent (at-least-once delivery is already the contract)
- No user is waiting synchronously for the result
- 2-minute interruption notice is enough to finish current message and drain

**Spot best practices:**
- Use multiple instance types and sizes (diversification reduces interruption probability)
- Set up node affinity/anti-affinity to spread across AZs
- Configure `terminationGracePeriodSeconds` to allow in-flight message completion
- Use Karpenter or Cluster Autoscaler with spot instance pools

---

## Graceful Degradation

Instead of spending money to make everything equally reliable, design the system to degrade gracefully. Protect the critical path and let non-essential features fail.

### Degradation Levels

| Level | Trigger | What Degrades | User Experience |
|-------|---------|--------------|-----------------|
| Level 0 -- Normal | All systems healthy | Nothing | Full functionality |
| Level 1 -- Reduced | Worker backlog > 5min or secondary dependency down | Background processing delays, non-critical features disabled | Core ordering works, status updates delayed |
| Level 2 -- Essential Only | Database at capacity or primary dependency degraded | Disable all non-essential queries, return cached responses where possible | Orders accepted, some data may be stale |
| Level 3 -- Survival | Core infrastructure at risk | Accept orders into queue only, disable reads that hit the database | "Order received" response, processing delayed |

### Implementation Approach

```
Degradation is implemented via:

1. Feature flags -- toggle non-essential features off without deployment
2. Circuit breakers -- automatically stop calling failing dependencies
3. Rate limiting -- shed load before the system falls over
4. Queue-based buffering -- accept work now, process later
5. Cached responses -- serve stale data rather than no data
```

### Cost Implication

Graceful degradation is a cost multiplier -- it lets you buy less infrastructure because the system can survive temporary capacity shortfalls instead of failing completely.

| Approach | Cost | Resilience |
|----------|------|-----------|
| Over-provision for peak | High | Handles peak but wastes money during normal load |
| Auto-scale reactively | Medium | Handles gradual growth but slow for sudden spikes |
| Graceful degradation + auto-scale | Lower | Degradation absorbs spikes while auto-scaling catches up |

ReliabilityOS uses the third approach: auto-scaling handles predictable load changes, and graceful degradation handles the gap between "demand spikes" and "new capacity is ready."

---

## Monthly Cost Review

Track these metrics monthly to ensure reliability investment stays proportional:

| Metric | What It Tells You |
|--------|------------------|
| Cost per request | Is efficiency improving as traffic grows? |
| Cost per nine | How much are you spending per unit of reliability? |
| Spot vs on-demand ratio | Is the instance mix optimized? |
| Idle resource percentage | Are you paying for capacity you don't use? |
| Error budget consumption vs infrastructure spend | Are reliability investments paying off in budget preservation? |

The goal is not minimum cost. The goal is optimal cost -- spending enough to meet SLOs, but not a dollar more.
