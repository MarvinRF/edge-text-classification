# Quantize, Distill, or Go Classical?

### A reproducible benchmark for text classification on real edge hardware, across languages

> When a text classifier has to leave the GPU server and run on a handheld device with no network, which option holds up: quantizing the large model, switching to a smaller one, or a classical baseline? We answer it milestone by milestone, measuring accuracy, per-class recall, latency, and memory on real edge hardware, in several languages, against acceptance criteria fixed **before** any experiment runs.

![status](https://img.shields.io/badge/status-M0%20in%20progress-yellow)
![license](https://img.shields.io/badge/code-MIT-blue)
![data](https://img.shields.io/badge/data-CC%20BY%204.0-lightgrey)

---

## Milestone overview

| # | Milestone | Answers | Key deliverable | Status |
|---|---|---|---|---|
| **M0** | Foundations | — | Repo, environment, acceptance criteria committed | 🟡 In progress |
| **M1** | First end-to-end baseline | RQ1, RQ4 (partial) | First accept/reject matrix (`en-US`, `pt-PT`, laptop CPU) | ⚪ Not started |
| **M2** | Languages at scale | RQ2 | Quantization sensitivity by language, with CIs | ⚪ Not started |
| **M3** | Real edge hardware | RQ3 | Speedup and memory table per device (incl. Raspberry Pi 5) | ⚪ Not started |
| **M4** | Safety-critical classes | RQ5 | Guard rule and recall vs. false-alarm trade-off | ⚪ Not started |
| **M5** | Field data case study | Generalization | Same matrix on real maintenance logs (MaintNet) | ⚪ Not started |
| **M6** | Public release | — | Report, HF models, live demo, write-up | ⚪ Not started |

```
M0 ──► M1 ──┬──► M2 ──┐
            ├──► M3 ──┼──► M6
            └──► M4 ──┤
                 M5 ──┘   (M5 starts after M1; it depends on the licensing check in M0)
```

Status legend: ⚪ not started · 🟡 in progress · 🟢 done · 🔴 blocked

---

## Why this project

This project grew out of an industrial AI training challenge. A maintenance company wanted field technicians' short incident reports to be classified **on the handheld device itself**, with no cloud connection, no GPU, 8 GB of RAM, and a response in under one second. The IT team's proposal was to buy devices with GPUs. Our measurements said otherwise:

| Model | Size | Latency / report (CPU, 2 threads) | Accuracy |
|---|---|---|---|
| Portuguese BERT-base, float32 | 436 MB | 71–94 ms | 0.843 |
| Portuguese BERT-base, int8 (dynamic) | 110 MB | 47–55 ms | 0.873 |
| TF-IDF + logistic regression | 0.04 MB | 0.8 ms | 0.863 |

*300-report sample, synthetic data; differences of a few reports are within sampling noise.*

Three lessons:

1. **The constraint was assumed, not measured.** The original model already fit the device.
2. **The int8 speedup depended on the hardware.** It was 2.8× on one CPU and slower than float32 on another (CPUs with and without VNNI).
3. **A 40 KB classical model tied a 436 MB transformer.** The real question became per-class behavior on the safety class, which aggregate accuracy hides.

The challenge data is private. This project repeats the question **on public data, at scale, on real edge hardware, and across languages**, to find out when each lesson holds in general.

## Research questions

| ID | Question | Milestone |
|---|---|---|
| **RQ1** | How much accuracy and per-class recall does int8 quantization (dynamic vs. static) cost? | M1 |
| **RQ2** | Does quantization hurt some languages more than others? | M2 |
| **RQ3** | How much of the theoretical int8 speedup appears on edge CPUs, with single-item inference and 1–2 threads? | M3 |
| **RQ4** | When does a distilled or classical model match a quantized large one, and how does that change with the number of classes? | M1, M2 |
| **RQ5** | Can a guard rule for safety-critical classes recover the recall that cheaper models lose, and at what false-alarm cost? | M4 |

---

## M0 · Foundations

**Goal:** everything needed to run experiments honestly, before running any.

**Tasks**
- [ ] Create the repo (`develop` + `main`), MIT license, `pyproject.toml` with uv, ruff, pyright strict and pytest; `scripts/gate.sh` and a CI that runs the same steps
- [ ] `tests/smoke/test_layers.py`: import rules between components, enforced from day one
- [ ] Write `docs/acceptance_criteria.md` (table below) and **merge it before any experiment**; the commit date is the evidence that criteria came first
- [ ] Start `docs/adr/`: ADR 0001 (decision records), 0002 (acceptance criteria before measuring), 0003 (ONNX Runtime as common runtime), 0004 (measurement protocol)
- [ ] Check licenses: MASSIVE (CC BY 4.0, confirmed) and MaintNet (per dataset, **pending**); record the findings in an ADR
- [ ] Set up MLflow tracking (local SQLite) and the run-naming convention
- [ ] Assign owners per milestone; set up the project board with one issue per task

**Acceptance criteria (the content of `docs/acceptance_criteria.md`)**

A path is *accepted* on a device only if it meets all of them:

| Dimension | Criterion | Rationale |
|---|---|---|
| Latency | p95 ≤ **200 ms** per input, batch 1, ≤ 2 threads | 5× margin under a 1 s requirement |
| Model size | ≤ **500 MB** on disk | Fits alongside OS and app on an 8 GB device |
| Peak memory | ≤ **1 GB** RSS during inference | Real footprint incl. tokenizer and activations |
| Aggregate quality | Macro-F1 drop ≤ **2.0 pp** vs. float32 reference | Small classes count equally |
| Per-class quality | No class loses more than **5 pp** recall | Aggregates hide class regressions |
| Critical classes | Critical-class recall drop ≤ **1 pp** (judged on the 95% CI upper bound) | Misrouting a safety report is the costliest error |

Drops count against aggregate and per-class criteria only when distinguishable from noise (95% bootstrap CI lower bound above the limit). For critical classes the burden is reversed: the upper bound must stay within the limit. Details in `docs/acceptance_criteria.md`; status: **proposed**, to be ratified before M1.

**Deliverables:** repo skeleton · `acceptance_criteria.md` · `docs/adr/` (0001–0004) · `scripts/gate.sh` + CI · `tests/smoke/test_layers.py` · licensing note

**Done when:** CI is green, the criteria are merged on `main`, and every M1 task has an owner.

---

## M1 · First end-to-end baseline

**Goal:** one complete run of every path on one task, two languages, one device, producing the first accept/reject matrix.

**Scope**
- **Dataset:** [MASSIVE](https://huggingface.co/datasets/AmazonScience/massive) (Amazon Science, CC BY 4.0, about 1M utterances, 51 languages, 60 intents, 18 domains; [paper](https://arxiv.org/abs/2204.08582))
- **Task:** domain classification (18 classes, closest to the original 5-class problem)
- **Languages:** `en-US`, `pt-PT`
- **Splits:** official train / dev / test
- **Device:** a laptop x86 CPU (record whether it has VNNI)

**Paths compared**

| Path | Model | Notes |
|---|---|---|
| Reference | `xlm-roberta-base`, float32 | Plays the "current GPU model" role |
| Quantize, dynamic | same, int8 weights | ONNX Runtime `quantize_dynamic`, no calibration |
| Quantize, static | same, int8 weights and activations | `quantize_static`, calibrated on **train** only |
| Distill | `microsoft/Multilingual-MiniLM-L12-H384`, float32 and int8 | Smaller transformer |
| Classical | TF-IDF (word 1–2 + char 2–5 grams) + logistic regression | One per language, CPU-trained |

**Measurement protocol** (implemented once in `bench.py` and reused by every later milestone)
- One input at a time, no batching; latency **includes tokenization**
- `intra_op_num_threads` ∈ {1, 2}; 50 warm-up inferences discarded; 3 full passes; report p50 / p95 / p99
- Peak RSS via `psutil`, in a fresh process per model
- Accuracy, macro-F1, per-class precision/recall, confusion matrix; 1,000-sample bootstrap CIs
- 3 fine-tuning seeds per transformer; mean ± std
- Every run logged to MLflow with model, device, threads, and criteria version

**Tasks**
- [ ] `data.py`: load MASSIVE and select languages and task
- [ ] `train.py`: fine-tune transformers (same budget for all) and train the classical path
- [ ] `export.py` and `quantize.py`: ONNX export, dynamic and static int8
- [ ] `bench.py`: the protocol above, with unit tests on the metric code
- [ ] Fill the matrix in `results/m1_matrix.csv` and in this README

**Deliverable: the first accept/reject matrix**

| Path | p95 latency | Size | Peak RSS | Macro-F1 Δ | Worst class Δ | Accepted? |
|---|---|---|---|---|---|---|
| XLM-R float32 | | | | — | — | |
| XLM-R int8 dynamic | | | | | | |
| XLM-R int8 static | | | | | | |
| MiniLM float32 | | | | | | |
| MiniLM int8 | | | | | | |
| TF-IDF + LR | | | | | | |

**Done when:** the matrix is filled for both languages, each cell links to its MLflow run, and a teammate reproduces one row from a clean clone.

---

## M2 · Languages at scale

**Goal:** answer RQ2 (does quantization hurt some languages more?) and extend RQ4 to a harder task.

**Scope**
- **Languages:** `en-US`, `pt-PT`, `es-ES`, `de-DE`, `hi-IN`, `ar-SA`, `ja-JP`, `sw-KE` (a mix of high and low resource, Latin and non-Latin scripts)
- **Tasks:** domain (18 classes) **and** intent (60 classes)
- **Device:** same as M1

**Tasks**
- [ ] Run the M1 pipeline for all 8 languages × 2 tasks (config-driven, no code changes)
- [ ] Compute the macro-F1 drop (int8 vs. float32) per language, with CIs
- [ ] Check whether the drop correlates with script, tokenizer fertility (tokens per word), or pretraining data size
- [ ] Compare how the classical path's gap to the transformers changes from 18 to 60 classes

**Deliverables**
- Figure: quantization drop per language with 95% CIs (`results/m2_language_drop.png`)
- Table: accept/reject per language × task × path
- Short findings section in `docs/report.md`

**Done when:** every language × task × path cell exists, and the RQ2 answer is written with its evidence and limits.

---

## M3 · Real edge hardware

**Goal:** answer RQ3 (does the int8 speedup survive on real edge CPUs?) and replace the laptop numbers with on-device numbers.

**Devices**

| Device | CPU | Why |
|---|---|---|
| Laptop x86 with VNNI | e.g. Intel 12th gen+ | Best case for int8 |
| x86 without VNNI | e.g. a Colab CPU instance | Common case where int8 gains vanish |
| **Raspberry Pi 5 (8 GB)** | ARM Cortex-A76, 4 cores | Realistic edge device |

**Tasks**
- [ ] `scripts/bench_device.sh`: runs `bench.py` using only the ONNX/pickle artifacts (no training dependencies)
- [ ] Record `lscpu` flags (VNNI, AVX-512, ARM dotprod) next to every result
- [ ] Run the M1 matrix on each device, with 1 and 2 threads
- [ ] Measure the tokenizer's share of total latency on each device

**Deliverables**
- Table: speedup (float32 p50 / int8 p50) per device, with instruction-set flags
- Final accept/reject matrix **on the Raspberry Pi 5**, which is the headline result of the project
- Short explanation of *why* speedups differ, tied to the flags

**Done when:** the Pi matrix is filled and every speedup number has a hardware explanation next to it.

---

## M4 · Safety-critical classes

**Goal:** answer RQ5. In the original problem, a safety report routed to the wrong team is the costliest error; here we test whether a cheap safeguard fixes what cheap models miss.

**Tasks**
- [ ] Designate critical classes (in MASSIVE, alarm-related intents) and record the choice in an ADR
- [ ] Measure critical-class recall for every path, with CIs
- [ ] `guard.py`: a small keyword / char-n-gram detector that forces "critical, human review" when it fires
- [ ] Plot recall gained vs. false alarms added, for each path with and without the guard

**Deliverables**
- Trade-off curve (`results/m4_guard_tradeoff.png`)
- Answer to: *does "cheap model + guard rule" beat "expensive model alone" on critical recall?*

**Done when:** every path has a critical-recall number with a CI, with and without the guard, and the criteria row for critical classes is filled in the matrix.

---

## M5 · Field data case study

**Goal:** test whether conclusions from clean benchmark text survive noisy, domain-specific field text, which is the original use case.

**Dataset:** MaintNet ([paper](https://arxiv.org/abs/2005.12443)): maintenance logbooks from aviation (about 6.2k records), automotive (about 0.6k), and facilities (about 87k), with abbreviations and typos.

**Entry condition:** the M0 licensing check allows use. If it does not, replace MaintNet with another public maintenance-log dataset and record the switch in a new ADR.

**Tasks**
- [ ] Confirm whether usable class labels exist; if not, derive them (e.g. by system or component) and document the rule
- [ ] Run the M1 pipeline (English models) on the chosen subset
- [ ] Compare the matrix with MASSIVE `en-US`: which conclusions hold and which flip?

**Deliverables:** accept/reject matrix on field data · "what changes on real field text" section in the report

**Done when:** the matrix is filled and the comparison with MASSIVE is written.

---

## M6 · Public release

**Goal:** turn results into something people can use, verify, and cite.

**Tasks**
- [ ] `docs/report.md`: short paper-style write-up (motivation, method, results with CIs, limitations)
- [ ] Publish quantized ONNX models on the Hugging Face Hub, with model cards stating measured latency per device and per-class metrics
- [ ] Hugging Face Space demo: type a sentence and see each path's prediction and latency side by side
- [ ] Write-up post (blog or LinkedIn), plus an optional workshop submission
- [ ] Clean-clone reproduction check by someone outside the team
- [ ] Tag `v1.0`

**Done when:** a stranger can go from the README to the reproduced Raspberry Pi matrix using only the documentation.

---

## Key findings

*Filled in as milestones close. Each finding states its evidence, its milestone, and its limits.*

| Finding | Evidence | Milestone |
|---|---|---|
| | | |

## Repository structure

```
edge-text-classification/
├── README.md                    # this document: milestones and results
├── LICENSE
├── pyproject.toml               # uv, ruff, pyright strict, pytest
├── uv.lock
├── .github/workflows/ci.yml     # same steps as scripts/gate.sh
├── docs/
│   ├── adr/                     # numbered architecture decision records
│   ├── acceptance_criteria.md   # M0, merged before any experiment
│   └── report.md                # M6 write-up
├── configs/                     # one YAML per experiment (language × task × path)
├── src/edgecls/
│   ├── errors.py                # shared errors, imports nothing from the package
│   ├── ports.py                 # Classifier protocol; bench and guard depend only on it
│   ├── data/                    # M1, loading, language subsets, splits
│   ├── train/                   # M1, fine-tuning and classical training
│   ├── export/                  # M1, ONNX export
│   ├── quantize/                # M1, dynamic and static int8
│   ├── bench/                   # M1, reused by M2–M5; runs on-device without torch
│   └── guard/                   # M4
├── tests/
│   └── smoke/test_layers.py     # import rules between components, read from the AST
├── scripts/
│   ├── gate.sh                  # lint, format, types, tests: same as CI
│   └── bench_device.sh          # M3, on-device entry point
├── notebooks/                   # exploration and figures only
├── results/                     # CSVs and figures (models stay out of git)
└── app/                         # M6, Hugging Face Space
```

## Reproducing

```bash
git clone <repo-url> && cd edge-text-classification
python -m venv .venv && source .venv/bin/activate
pip install -e .

python -m edgecls.train    --config configs/massive_domain_en.yaml   # GPU recommended for transformers
python -m edgecls.export   --config configs/massive_domain_en.yaml
python -m edgecls.quantize --config configs/massive_domain_en.yaml
python -m edgecls.bench    --config configs/massive_domain_en.yaml --threads 1 2
```

On a Raspberry Pi, copy only the `.onnx` / `.pkl` artifacts and run `scripts/bench_device.sh`.

## Limitations

- MASSIVE is virtual-assistant text, cleaner and shorter than field reports; M5 exists to test that gap.
- Translated data shares content across languages. That makes the comparison controlled, but it isn't naturally occurring text in each language.
- A Raspberry Pi approximates, but isn't, an industrial handheld; re-measure on the target device before deployment.
- Only post-training int8 quantization is covered; quantization-aware training and 4-bit weights are out of scope for v1.

## Team

Built by a team of AI students from Brazil.

| Name | Milestone ownership | GitHub |
|---|---|---|
| | M0, M6 | |
| | M1, M2 | |
| | M3 | |
| | M4, M5 | |

Contributions are welcome, especially benchmark results from new edge hardware. Open an issue describing the device or experiment.

## License and citation

- **Code:** MIT
- **MASSIVE:** CC BY 4.0, © Amazon.com, Inc. Cite FitzGerald et al., 2022 ([arXiv:2204.08582](https://arxiv.org/abs/2204.08582))
- **MaintNet:** per its own terms; cite Akhbardeh et al., 2020 ([arXiv:2005.12443](https://arxiv.org/abs/2005.12443))

```bibtex
@misc{edgecls2026,
  title  = {Quantize, Distill, or Go Classical? Text Classification on Real Edge Hardware Across Languages},
  author = {<team>},
  year   = {2026},
  url    = {<repo-url>}
}
```
