# GameDay Template

## Pre-GameDay Checklist

- [ ] All participants notified and available
- [ ] Grafana dashboards open (SLO Overview + Engineering)
- [ ] Kill switches documented and tested
- [ ] Baseline metrics recorded
- [ ] Communication channel established

## Experiment Execution

### Experiment: [Name]

**Hypothesis:** [What do we expect to happen?]

**Blast Radius:** [What percentage of the system is affected?]

**Kill Switch:** `kubectl delete chaosengine [name] -n reliabilityos`

**Pre-experiment baseline:**
- API availability: ____%
- API p95 latency: ____ms
- Worker success rate: ____%
- Error budget remaining: ____%

**Execution:**
```bash
kubectl apply -f chaos/experiments/[experiment].yaml
```

**Observations during experiment:**
- [ ] Dashboard shows impact? Y/N
- [ ] Alerts fired? Which ones?
- [ ] Recovery detected? How long?

**Post-experiment metrics:**
- API availability: ____%
- API p95 latency: ____ms
- Worker success rate: ____%
- Error budget remaining: ____%

**Result:** PASS / FAIL

**Findings:**
- [What did we learn?]
- [What was surprising?]
- [What should we harden?]

## Post-GameDay

- [ ] Cleanup all ChaosEngines
- [ ] Document results
- [ ] Create action items for failures
- [ ] Share findings with team
- [ ] Schedule next GameDay
