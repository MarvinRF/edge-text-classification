# 0003. ONNX Runtime and the classifier port

- Status: accepted (16/11/2026)

## Context
The paths under comparison come from different libraries (PyTorch transformers, scikit-learn). If each one ran on its own stack, latency differences would mix model effects with runtime effects. The edge device should also not need the training stack installed.

## Decision
- Transformers, float32 and int8, are exported to ONNX and run with ONNX Runtime on CPU. The classical path runs with scikit-learn.
- `src/edgecls/ports.py` defines `Classifier` (`labels`, `predict(text)`). Each runtime has one adapter. `bench` and `guard` depend only on the port.
- On-device code (`bench`, `guard`, `ports`, `criteria`) never imports torch, transformers, datasets, `train`, or `export`. Only `data` and `train` reach the network. Both rules are enforced by `tests/smoke/test_layers.py`.

## Consequences
- The Raspberry Pi needs only onnxruntime, tokenizers, numpy, and scikit-learn.
- Every path is timed by the same code, including tokenization.
- A new runtime (e.g. TFLite) is a new adapter, not a change to the benchmark.

## Alternatives
- Benchmarking in PyTorch directly: simpler to start, but it is not what ships to the device, and int8 support on CPU differs from ONNX Runtime.
