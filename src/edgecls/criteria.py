"""Acceptance criteria (ADR 0002, docs/acceptance_criteria.md), frozen in code.

Fixed before any experiment runs. Changing a value is a new ADR, never an edit
made after looking at results.
"""

from dataclasses import dataclass

from edgecls.errors import InvalidConfiguration


@dataclass(frozen=True)
class AcceptanceCriteria:
    max_p95_latency_ms: float = 200.0
    max_model_size_mb: float = 500.0
    max_peak_rss_mb: float = 1000.0
    max_macro_f1_drop_pp: float = 2.0
    max_class_recall_drop_pp: float = 5.0
    max_critical_recall_drop_pp: float = 1.0

    def __post_init__(self) -> None:
        for name, value in vars(self).items():
            if value <= 0:
                raise InvalidConfiguration(f"{name} must be positive, got {value}")
        if self.max_critical_recall_drop_pp > self.max_class_recall_drop_pp:
            raise InvalidConfiguration(
                "critical classes cannot tolerate a larger recall drop than other classes"
            )


@dataclass(frozen=True)
class Measurement:
    """What one deployment path achieved on one device. Drops are in percentage points."""

    p95_latency_ms: float
    model_size_mb: float
    peak_rss_mb: float
    macro_f1_drop_pp: float
    worst_class_recall_drop_pp: float
    critical_recall_drop_pp: float


def failures(m: Measurement, c: AcceptanceCriteria) -> list[str]:
    """Names of the criteria the measurement fails; empty means accepted."""
    checks = {
        "latency": m.p95_latency_ms <= c.max_p95_latency_ms,
        "model size": m.model_size_mb <= c.max_model_size_mb,
        "peak memory": m.peak_rss_mb <= c.max_peak_rss_mb,
        "macro-F1": m.macro_f1_drop_pp <= c.max_macro_f1_drop_pp,
        "per-class recall": m.worst_class_recall_drop_pp <= c.max_class_recall_drop_pp,
        "critical recall": m.critical_recall_drop_pp <= c.max_critical_recall_drop_pp,
    }
    return [name for name, ok in checks.items() if not ok]
