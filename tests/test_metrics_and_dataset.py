"""Smoke tests for the torch-free core: metrics + dataset analysis.

Run with:  python -m pytest tests/ -q   (needs numpy only)
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from fsd.dataset.celeba_spoof import LABEL_VECTOR_LEN, analyze_dataset, load_labels
from fsd.eval.metrics import auc_score, eer_score, evaluate, tpr_at_fpr


def _make_vec(live_spoof: int, spoof_type: int = 0, illum: int = 1, env: int = 1):
    vec = [0] * LABEL_VECTOR_LEN
    vec[40] = spoof_type
    vec[41] = illum
    vec[42] = env
    vec[43] = live_spoof
    return vec


def test_metrics_perfect_separation():
    # spoof scores high (1), live scores low (0) -> perfect AUC, zero EER.
    scores = [0.0, 0.1, 0.2, 0.8, 0.9, 1.0]
    labels = [0, 0, 0, 1, 1, 1]
    assert auc_score(scores, labels) == 1.0
    eer, _ = eer_score(scores, labels)
    assert eer == 0.0
    tpr = tpr_at_fpr(scores, labels, [0.001])
    assert tpr[0.001] == 1.0


def test_metrics_random_is_midrange():
    rng = np.random.default_rng(0)
    n = 2000
    labels = rng.integers(0, 2, n)
    scores = rng.random(n)  # uncorrelated with labels
    res = evaluate(scores, labels)
    assert 0.4 < res.auc < 0.6
    assert 0.0 <= res.acer <= 1.0


def test_dataset_analysis(tmp_path: Path):
    labels = {
        "Data/train/1/live/a.png": _make_vec(0, spoof_type=0),
        "Data/train/1/spoof/b.png": _make_vec(1, spoof_type=3),
        "Data/train/2/spoof/c.png": _make_vec(1, spoof_type=9),
    }
    p = tmp_path / "labels.json"
    p.write_text(json.dumps(labels), encoding="utf-8")

    entries = load_labels(p)
    assert len(entries) == 3
    stats = analyze_dataset(entries)
    d = stats.to_dict()
    assert d["total"] == 3
    assert d["live"] == 1
    assert d["spoof"] == 2
    assert d["subjects"] == 2
    assert d["spoof_type"]["A4"] == 1
    assert d["spoof_type"]["Phone"] == 1
