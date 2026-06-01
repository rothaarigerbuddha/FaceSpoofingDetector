"""Face anti-spoofing evaluation metrics (pure NumPy, no sklearn required).

Convention throughout:
    score  -> spoof probability in [0, 1]  (higher = more likely an attack)
    label  -> 1 = spoof (attack / positive), 0 = live (bona fide / negative)

Metrics:
    * TPR@FPR        - spoof recall at fixed false-accept rates (paper's headline metric)
    * AUC            - area under the ROC curve
    * EER            - equal error rate (+ the threshold where it occurs)
    * APCER/BPCER/ACER - ISO/IEC 30107-3 presentation-attack error rates at a threshold
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

DEFAULT_FPR_TARGETS = (1e-2, 5e-3, 1e-3)


def _as_arrays(scores, labels) -> tuple[np.ndarray, np.ndarray]:
    s = np.asarray(scores, dtype=np.float64).ravel()
    y = np.asarray(labels, dtype=np.int64).ravel()
    if s.shape != y.shape:
        raise ValueError(f"scores {s.shape} and labels {y.shape} length mismatch")
    if s.size == 0:
        raise ValueError("empty scores/labels")
    return s, y


def roc_curve(scores, labels) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (fpr, tpr, thresholds) sorted by descending threshold.

    Positive class = spoof (label 1). FPR is over live samples accepted as spoof.
    """
    s, y = _as_arrays(scores, labels)
    order = np.argsort(-s, kind="mergesort")
    s, y = s[order], y[order]

    distinct = np.where(np.diff(s))[0]
    threshold_idxs = np.r_[distinct, s.size - 1]

    tps = np.cumsum(y)[threshold_idxs]
    fps = np.cumsum(1 - y)[threshold_idxs]

    total_pos = tps[-1] if tps.size else 0
    total_neg = fps[-1] if fps.size else 0
    if total_pos == 0 or total_neg == 0:
        raise ValueError("ROC needs at least one live and one spoof sample")

    tpr = tps / total_pos
    fpr = fps / total_neg
    thr = s[threshold_idxs]

    # Prepend the (0, 0) origin point.
    fpr = np.r_[0.0, fpr]
    tpr = np.r_[0.0, tpr]
    thr = np.r_[thr[0] + 1.0, thr]
    return fpr, tpr, thr


def auc_score(scores, labels) -> float:
    fpr, tpr, _ = roc_curve(scores, labels)
    return float(np.trapezoid(tpr, fpr)) if hasattr(np, "trapezoid") else float(np.trapz(tpr, fpr))


def tpr_at_fpr(scores, labels, fpr_targets=DEFAULT_FPR_TARGETS) -> dict[float, float]:
    """Spoof recall (TPR) at each target false-positive rate, via interpolation."""
    fpr, tpr, _ = roc_curve(scores, labels)
    out: dict[float, float] = {}
    for target in fpr_targets:
        out[target] = float(np.interp(target, fpr, tpr))
    return out


def eer_score(scores, labels) -> tuple[float, float]:
    """Equal Error Rate and the threshold at which FPR ~= FNR."""
    fpr, tpr, thr = roc_curve(scores, labels)
    fnr = 1.0 - tpr
    idx = int(np.nanargmin(np.abs(fpr - fnr)))
    eer = float((fpr[idx] + fnr[idx]) / 2.0)
    return eer, float(thr[idx])


def apcer_bpcer_acer(scores, labels, threshold: float = 0.5) -> tuple[float, float, float]:
    """ISO/IEC 30107-3 error rates at a decision threshold (predict spoof if score>=thr).

    APCER = attacks accepted as bona fide / total attacks
    BPCER = bona fide rejected as attack   / total bona fide
    ACER  = (APCER + BPCER) / 2
    """
    s, y = _as_arrays(scores, labels)
    pred_spoof = s >= threshold
    attacks = y == 1
    bona = y == 0
    n_attack = int(attacks.sum())
    n_bona = int(bona.sum())
    apcer = float((attacks & ~pred_spoof).sum() / n_attack) if n_attack else 0.0
    bpcer = float((bona & pred_spoof).sum() / n_bona) if n_bona else 0.0
    return apcer, bpcer, (apcer + bpcer) / 2.0


@dataclass
class MetricResult:
    n: int
    n_live: int
    n_spoof: int
    auc: float
    eer: float
    eer_threshold: float
    tpr_at_fpr: dict[float, float] = field(default_factory=dict)
    apcer: float = 0.0
    bpcer: float = 0.0
    acer: float = 0.0
    threshold: float = 0.5

    def to_dict(self) -> dict:
        return {
            "n": self.n,
            "n_live": self.n_live,
            "n_spoof": self.n_spoof,
            "auc": round(self.auc, 6),
            "eer": round(self.eer, 6),
            "eer_threshold": round(self.eer_threshold, 6),
            "tpr_at_fpr": {f"{k:g}": round(v, 6) for k, v in self.tpr_at_fpr.items()},
            "apcer": round(self.apcer, 6),
            "bpcer": round(self.bpcer, 6),
            "acer": round(self.acer, 6),
            "threshold": self.threshold,
        }


def evaluate(
    scores,
    labels,
    *,
    threshold: float = 0.5,
    fpr_targets=DEFAULT_FPR_TARGETS,
) -> MetricResult:
    """Compute the full metric suite for one model's predictions."""
    s, y = _as_arrays(scores, labels)
    eer, eer_thr = eer_score(s, y)
    apcer, bpcer, acer = apcer_bpcer_acer(s, y, threshold)
    return MetricResult(
        n=int(s.size),
        n_live=int((y == 0).sum()),
        n_spoof=int((y == 1).sum()),
        auc=auc_score(s, y),
        eer=eer,
        eer_threshold=eer_thr,
        tpr_at_fpr=tpr_at_fpr(s, y, fpr_targets),
        apcer=apcer,
        bpcer=bpcer,
        acer=acer,
        threshold=threshold,
    )
