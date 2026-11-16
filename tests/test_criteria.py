import dataclasses

import pytest

from edgecls.criteria import AcceptanceCriteria, Measurement, failures
from edgecls.errors import InvalidConfiguration

PASSING = Measurement(
    p95_latency_ms=50,
    model_size_mb=110,
    peak_rss_mb=400,
    macro_f1_drop_pp=0.5,
    worst_class_recall_drop_pp=3,
    critical_recall_drop_pp=0,
)


def test_measurement_within_every_limit_is_accepted() -> None:
    assert failures(PASSING, AcceptanceCriteria()) == []


def test_limits_are_inclusive() -> None:
    c = AcceptanceCriteria()
    at_limit = Measurement(
        p95_latency_ms=c.max_p95_latency_ms,
        model_size_mb=c.max_model_size_mb,
        peak_rss_mb=c.max_peak_rss_mb,
        macro_f1_drop_pp=c.max_macro_f1_drop_pp,
        worst_class_recall_drop_pp=c.max_class_recall_drop_pp,
        critical_recall_drop_pp=c.max_critical_recall_drop_pp,
    )
    assert failures(at_limit, c) == []


@pytest.mark.parametrize(
    ("field", "value", "name"),
    [
        ("p95_latency_ms", 201, "latency"),
        ("model_size_mb", 501, "model size"),
        ("peak_rss_mb", 1001, "peak memory"),
        ("macro_f1_drop_pp", 2.1, "macro-F1"),
        ("worst_class_recall_drop_pp", 5.1, "per-class recall"),
        ("critical_recall_drop_pp", 1.1, "critical recall"),
    ],
)
def test_each_criterion_rejects_on_its_own(field: str, value: float, name: str) -> None:
    m = dataclasses.replace(PASSING, **{field: value})
    assert failures(m, AcceptanceCriteria()) == [name]


def test_criteria_are_frozen() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        AcceptanceCriteria().max_p95_latency_ms = 999  # type: ignore[misc]


def test_non_positive_limit_is_rejected() -> None:
    with pytest.raises(InvalidConfiguration):
        AcceptanceCriteria(max_model_size_mb=0)


def test_critical_classes_cannot_be_looser_than_the_rest() -> None:
    with pytest.raises(InvalidConfiguration):
        AcceptanceCriteria(max_class_recall_drop_pp=1, max_critical_recall_drop_pp=2)
