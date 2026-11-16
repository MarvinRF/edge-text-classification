# Acceptance criteria

- Status: **proposed** (16/11/2026). To be ratified by the team before M1 starts; see [ADR 0002](adr/0002-acceptance-criteria-before-measuring.md).
- Code: `src/edgecls/criteria.py`. The two must always match.

A deployment path is **accepted** on a device only if it meets every criterion below.

| Dimension | Criterion | Rationale |
|---|---|---|
| Latency | p95 ≤ **200 ms** per input, batch 1, ≤ 2 threads | Interactive use; 5× margin under a 1 s requirement for slower devices |
| Model size | ≤ **500 MB** on disk | Fits alongside OS and app on an 8 GB device |
| Peak memory | ≤ **1 GB** RSS during inference | Real footprint, including tokenizer and activations |
| Aggregate quality | Macro-F1 drop ≤ **2.0 pp** vs. the float32 reference | Macro-F1 weighs small classes equally |
| Per-class quality | No class loses more than **5 pp** recall | Aggregate metrics hide class-level regressions |
| Critical classes | Critical-class recall drop ≤ **1 pp** | Misrouting a safety-critical input is the costliest error |

## How drops are counted

Quality drops are measured against the float32 reference on the same test split, with 1,000-sample bootstrap 95% confidence intervals.

- **Aggregate and per-class criteria:** a drop fails the criterion when the **lower** bound of its interval exceeds the limit, so it must be distinguishable from noise.
- **Critical classes:** the burden is reversed. The criterion fails when the **upper** bound exceeds the limit: a path must show it is safe, not merely that harm went undetected.
