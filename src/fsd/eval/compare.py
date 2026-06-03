"""Run one or more detectors over a labelled subset and compare their metrics."""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from fsd.dataset.celeba_spoof import LabelEntry, LabelIndex
from fsd.eval.metrics import MetricResult, evaluate
from fsd.utils.image import read_image_rgb


@dataclass
class ModelSpec:
    name: str
    weights: str | None = None
    arch: str | None = None  # registry builder to use; defaults to ``name``

    def key(self) -> str:
        return self.name

    def build_name(self) -> str:
        return self.arch or self.name


def sample_entries(
    entries: list[LabelEntry],
    *,
    limit: int | None = None,
    seed: int = 0,
    balanced: bool = True,
) -> list[LabelEntry]:
    """Optionally subsample entries, keeping a live/spoof balance when requested."""
    if limit is None or limit >= len(entries):
        return entries
    rng = random.Random(seed)
    if not balanced:
        return rng.sample(entries, limit)
    live = [e for e in entries if not e.is_spoof]
    spoof = [e for e in entries if e.is_spoof]
    half = limit // 2
    take_live = min(half, len(live))
    take_spoof = min(limit - take_live, len(spoof))
    picked = rng.sample(live, take_live) + rng.sample(spoof, take_spoof)
    rng.shuffle(picked)
    return picked


def _iter_images(entries, data_root: Path):
    """Yield (entry, rgb_image) skipping unreadable files."""
    for e in entries:
        try:
            yield e, read_image_rgb(data_root / e.path, crop=True)
        except FileNotFoundError:
            continue


def score_detector(detector, entries, data_root: Path, *, batch_size: int = 64) -> tuple[np.ndarray, np.ndarray]:
    """Return (scores, labels) arrays for a detector over the given entries."""
    scores: list[float] = []
    labels: list[int] = []
    batch_imgs: list[np.ndarray] = []
    batch_labels: list[int] = []

    def flush():
        if batch_imgs:
            scores.extend(detector.predict_batch(batch_imgs))
            labels.extend(batch_labels)
            batch_imgs.clear()
            batch_labels.clear()

    for e, img in _iter_images(entries, Path(data_root)):
        batch_imgs.append(img)
        batch_labels.append(e.raw[LabelIndex.LIVE_SPOOF])
        if len(batch_imgs) >= batch_size:
            flush()
    flush()
    return np.asarray(scores), np.asarray(labels)


def compare_models(
    specs: list[ModelSpec],
    entries: list[LabelEntry],
    data_root: str | Path,
    *,
    batch_size: int = 64,
    threshold: float = 0.5,
    device: str | None = None,
) -> dict[str, MetricResult]:
    """Build each detector, score it, and return name -> MetricResult."""
    from fsd.detectors.registry import build_detector  # lazy: torch only needed here

    data_root = Path(data_root)
    results: dict[str, MetricResult] = {}
    for spec in specs:
        detector = build_detector(spec.build_name(), weights=spec.weights, device=device)
        scores, labels = score_detector(detector, entries, data_root, batch_size=batch_size)
        results[spec.key()] = evaluate(scores, labels, threshold=threshold)
    return results
