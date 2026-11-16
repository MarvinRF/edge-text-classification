# 0004. Measurement protocol

- Status: accepted (16/11/2026)

## Context
Latency on small inputs is noisy and depends on warm-up, threads, and CPU instruction sets. In the original challenge, the same int8 model ran 2.8× faster on one CPU and slower than float32 on another. Quality differences of a few examples are within sampling noise.

## Decision
- One input at a time, no batching. Latency includes tokenization.
- `intra_op_num_threads` ∈ {1, 2}. 50 warm-up inferences discarded. 3 full passes over the test split. Report p50, p95, p99.
- Peak RSS via `psutil`, in a fresh process per model.
- Quality: accuracy, macro-F1, per-class precision and recall, confusion matrix, with 1,000-sample bootstrap 95% CIs.
- 3 fine-tuning seeds per transformer; report mean ± std.
- Every run writes a manifest: commit, dataset hash, model, config, seed, machine, and CPU flags (VNNI, AVX-512, ARM dotprod).

## Consequences
- Speedups can be explained by hardware, not just observed.
- A full benchmark pass takes longer; that cost is accepted.

## Alternatives
- Batched throughput: more stable, but not what a user waiting for one classification experiences.
