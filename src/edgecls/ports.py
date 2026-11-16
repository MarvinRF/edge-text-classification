"""The classifier port (ADR 0003): all that `bench` and `guard` know about a model.

One adapter per runtime (ONNX Runtime, scikit-learn) implements it. Benchmark
code never imports an adapter, so every deployment path is measured the same way.
"""

from typing import Protocol


class Classifier(Protocol):
    """Classifies one input at a time, as the device does in the field."""

    @property
    def labels(self) -> tuple[str, ...]: ...

    def predict(self, text: str) -> str: ...
