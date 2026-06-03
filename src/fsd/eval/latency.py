"""Inference-latency / throughput measurement, identical across all models.

Every model is timed the same way: end-to-end ``predict_batch`` (preprocess +
forward + softmax) on a single synthetic RGB frame, after warm-up, averaged over
several runs. This is the deployment-relevant single-image cost and lets ViT/CDCN
report latency even when they are not part of the accuracy comparison.
"""

from __future__ import annotations

import time

import numpy as np


def measure_latency(
    detector,
    *,
    input_size: int = 224,
    runs: int = 30,
    warmup: int = 5,
    batch_size: int = 1,
    seed: int = 0,
) -> dict:
    """Return ``{latency_ms, fps, batch_size, device}`` for one detector.

    ``latency_ms`` is per-image wall-clock milliseconds; ``fps`` is its reciprocal.
    CUDA is synchronised around the timed region so the number is honest on GPU.
    """
    import torch

    rng = np.random.default_rng(seed)
    frame = rng.integers(0, 256, (input_size, input_size, 3), dtype=np.uint8)
    imgs = [frame] * batch_size

    for _ in range(warmup):
        detector.predict_batch(imgs)
    if torch.cuda.is_available():
        torch.cuda.synchronize()

    t0 = time.perf_counter()
    for _ in range(runs):
        detector.predict_batch(imgs)
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    per_batch = (time.perf_counter() - t0) / runs

    latency_ms = per_batch * 1000.0 / batch_size
    return {
        "latency_ms": round(latency_ms, 4),
        "fps": round(1000.0 / latency_ms, 2),
        "batch_size": batch_size,
        "device": str(getattr(detector, "device", "cpu")),
    }
