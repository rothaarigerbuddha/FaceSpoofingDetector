"""Multi-task auxiliary supervision for AENet -- the semantic AENet_C,S variant.

AENet is the only model in this repo whose architecture already carries heads for
CelebA-Spoof's semantic auxiliary labels (``fc_attack``, ``fc_light``,
``fc_live_attribute``). This module switches those heads on *during training* so
the shared backbone is supervised by richer signal than a plain live/spoof head:

    L = L_live + λ_attack·L_attack + λ_light·L_light + λ_attr·L_attr

    L_live   : CrossEntropy over [live, spoof]          (label idx 43)  -- MAIN task
    L_attack : CrossEntropy over 11 spoof types         (label idx 40)  -- auxiliary
    L_light  : CrossEntropy over 5 illumination classes (label idx 41)  -- auxiliary
    L_attr   : BCE over 40 binary face attributes       (label idx 0..39) -- auxiliary

This is the SEMANTIC-ONLY variant. The geometric "G" heads (depth / reflection
maps) are intentionally NOT supervised: CelebA-Spoof ships no depth or reflection
maps, so generating them is out of scope. Hence the configuration is **AENet_C,S**
(Classification + Semantic), never AENet_C,S,G.

Label validity / masking -- verified against the parser contract in
``dataset/celeba_spoof.py`` (the ``LABEL_VECTOR_LEN``/``LabelIndex`` schema):

    * attack (idx 40) & light (idx 41): index value 0 is the "Live" sentinel for
      live images and 1.. for spoof images. The 11-/5-way heads INCLUDE that Live
      class, so the target is well-defined for *every* image -> no masking; the
      heads are trained on the full batch (live -> class 0).
    * attribute (idx 0..39): the 40 CelebA face attributes are annotated for LIVE
      images only (see the parser docstring). For spoof images they are undefined,
      so the attribute BCE is masked per-sample to live images via ``attr_valid``.

Inference is unchanged: scoring still uses only ``fc_live`` (see AENet.forward),
so APCER/BPCER/ACER/AUC/EER are computed identically to every other model.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn.functional as F

from fsd.dataset.celeba_spoof import LabelEntry, LabelIndex

N_ATTRIBUTES = 40


@dataclass(frozen=True)
class AuxWeights:
    """Loss weights for the auxiliary tasks. Main task (live) is fixed at 1.0.

    Defaults sit in the task's recommended 0.1-0.5 band, with the most
    spoofing-relevant signal (attack type) weighted highest and the high-dim
    40-way attribute BCE kept smallest so it cannot dominate the main objective.
    Lower these if multi-task training destabilises the live head.
    """

    attack: float = 0.5
    light: float = 0.25
    attribute: float = 0.1

    def as_dict(self) -> dict[str, float]:
        return {"live": 1.0, "attack": self.attack, "light": self.light, "attribute": self.attribute}


def aux_targets(entry: LabelEntry) -> dict:
    """Extract the per-image multi-task targets from a parsed LabelEntry.

    Returns python/tensor values that ``torch.utils.data.default_collate`` batches
    cleanly: ints for the CrossEntropy heads, a float32 (40,) vector for the
    attribute BCE, and a float ``attr_valid`` mask (1.0 for live, 0.0 for spoof).
    """
    raw = entry.raw
    is_spoof = int(raw[LabelIndex.LIVE_SPOOF]) == 1
    return {
        "live": int(raw[LabelIndex.LIVE_SPOOF]),
        "attack": int(raw[LabelIndex.SPOOF_TYPE]),
        "light": int(raw[LabelIndex.ILLUMINATION]),
        "attribute": torch.tensor(raw[:N_ATTRIBUTES], dtype=torch.float32),
        "attr_valid": 0.0 if is_spoof else 1.0,  # attributes annotated on live images only
    }


def multitask_loss(
    heads: dict[str, torch.Tensor],
    targets: dict[str, torch.Tensor],
    weights: AuxWeights,
) -> tuple[torch.Tensor, dict[str, float]]:
    """Combine the four head losses into the weighted total + a per-head log dict.

    ``heads``   : output of ``AENet.forward_multitask`` (raw logits per head).
    ``targets`` : a collated batch of ``aux_targets`` dicts (tensors on the device).
    """
    live_loss = F.cross_entropy(heads["live"], targets["live"])
    attack_loss = F.cross_entropy(heads["attack"], targets["attack"])
    light_loss = F.cross_entropy(heads["light"], targets["light"])

    # Masked BCE over the 40 attributes: per-sample mean, then average over the
    # live images only (spoof rows are zeroed out and excluded from the denominator).
    attr_mask = targets["attr_valid"].to(heads["attribute"].dtype)  # (B,)
    per_sample = F.binary_cross_entropy_with_logits(
        heads["attribute"], targets["attribute"], reduction="none"
    ).mean(dim=1)  # (B,)
    denom = attr_mask.sum().clamp_min(1.0)
    attr_loss = (per_sample * attr_mask).sum() / denom

    total = (
        live_loss
        + weights.attack * attack_loss
        + weights.light * light_loss
        + weights.attribute * attr_loss
    )
    log = {
        "live": float(live_loss.detach()),
        "attack": float(attack_loss.detach()),
        "light": float(light_loss.detach()),
        "attribute": float(attr_loss.detach()),
        "total": float(total.detach()),
    }
    return total, log
