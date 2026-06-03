"""Multi-task fine-tuning for AENet on CelebA-Spoof semantic auxiliary labels.

This is the *only* model trained with auxiliary supervision: it tests the thesis
that a specialised architecture (AENet) which exploits CelebA-Spoof's extra labels
becomes more robust to presentation attacks than a generic CNN trained on the
binary live/spoof signal alone. EfficientNet-B0 and DeepPixBiS deliberately stay
binary (via the generic ``fsd.train.train_model``); that contrast is the point.

We implement the **semantic-only** variant, AENet_C,S:

    L = L_live + λ1·L_attack_type + λ2·L_illumination + λ3·L_attributes

  * L_live         CrossEntropy over live/spoof          (label[43], 2 classes)   -> fc_live
  * L_attack_type  CrossEntropy over spoof type          (label[40], 11 classes)  -> fc_attack
  * L_illumination CrossEntropy over illumination        (label[41], 5 classes)   -> fc_light
  * L_attributes   BCE over 40 binary face attributes    (label[0:40])            -> fc_live_attribute

The geometry heads (depth/reflection maps) are NOT trained: CelebA-Spoof ships no
depth/reflection ground truth, so generating it is out of scope. Hence "_C,S"
(semantic Context cues only), explicitly logged in the output.

Masking (verified empirically on the train split, see thesis_experiment notes):
  * spoof_type[40] and illumination[41] are DEFINED FOR EVERY IMAGE -- bona-fide
    faces carry an explicit "Live" class 0 (live -> 0; spoof -> 1..N). They are not
    missing values, so their CE losses run on the full batch (matches official AENet).
  * the 40 attributes[0:40] are annotated ONLY on live images; every spoof image has
    an all-zero placeholder. So L_attributes is MASKED to live images only -- training
    on the zero placeholders would teach the model that spoof faces have no attributes,
    which is meaningless. If a batch has no live samples, L_attributes contributes 0.

Inference is unchanged: the saved checkpoint is a plain AENet, scored through fc_live
exactly like the binary AENet, so evaluation stays identical across all models.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

from fsd.dataset.celeba_spoof import LabelEntry, LabelIndex, load_labels
from fsd.detectors._torch_base import IMAGENET_MEAN, IMAGENET_STD, pick_device
from fsd.eval.compare import sample_entries
from fsd.utils.image import read_image_rgb

# Default auxiliary loss weights. Main task = 1.0; auxiliaries kept in the
# user-recommended 0.1..0.5 range so they enrich the gradient without overpowering
# the live/spoof objective. Attributes use the smallest weight because BCE over 40
# dims accumulates a larger raw magnitude than a single CrossEntropy term.
DEFAULT_LAMBDAS = {"attack_type": 0.5, "illumination": 0.5, "attributes": 0.1}

# AENet input pipeline: Resize(224) + ToTensor + ImageNet normalize (matches the
# binary AENet wrapper and the official client.py, so train/eval agree).
_INPUT_SIZE = 224


class MultiTaskDataset(Dataset):
    """Yields (image_tensor, live, attack_type, illumination, attributes[40])."""

    def __init__(self, entries: list[LabelEntry], data_root: str | Path):
        self.entries = entries
        self.data_root = Path(data_root)
        self.transform = transforms.Compose([
            transforms.Resize((_INPUT_SIZE, _INPUT_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ])

    def __len__(self) -> int:
        return len(self.entries)

    def __getitem__(self, idx: int):
        e = self.entries[idx]
        try:
            img = read_image_rgb(self.data_root / e.path, crop=True)
        except FileNotFoundError:
            img = np.zeros((_INPUT_SIZE, _INPUT_SIZE, 3), dtype=np.uint8)
        x = self.transform(Image.fromarray(img))
        live = int(e.raw[LabelIndex.LIVE_SPOOF])             # 0 live / 1 spoof
        attack_type = int(e.raw[LabelIndex.SPOOF_TYPE])      # 0..10
        illum = int(e.raw[LabelIndex.ILLUMINATION])          # 0..4
        attrs = torch.tensor(e.raw[:40], dtype=torch.float32)  # 40 x {0,1}
        return x, live, attack_type, illum, attrs


def train_aenet_multitask(
    *,
    labels: str,
    data_root: str,
    epochs: int = 6,
    batch_size: int = 32,
    lr: float = 1e-4,
    limit: int | None = 40000,
    device: str | None = None,
    out_dir: str = "runs",
    lambdas: dict[str, float] | None = None,
    num_workers: int = 4,
) -> str:
    """Train AENet with the masked multi-task loss; save a plain-AENet checkpoint."""
    from fsd.detectors.registry import build_detector

    dev = pick_device(device)
    lam = {**DEFAULT_LAMBDAS, **(lambdas or {})}

    # Same subset selection as fsd.train.train_model (seed=0) so the binary AENet and
    # this multi-task AENet train on the IDENTICAL images -- a controlled comparison.
    entries = sample_entries(load_labels(labels), limit=limit, seed=0)
    ds = MultiTaskDataset(entries, data_root)
    loader = DataLoader(ds, batch_size=batch_size, shuffle=True,
                        num_workers=num_workers, pin_memory=True)

    # ImageNet-warm-started AENet (same starting point as the binary AENet).
    model = build_detector("aenet", weights=None, device="cpu").model.to(dev).train()

    optim = torch.optim.AdamW(model.parameters(), lr=lr)
    ce = nn.CrossEntropyLoss()
    bce = nn.BCEWithLogitsLoss(reduction="none")  # per-element, so we can mask

    n_live = sum(1 for e in entries if not e.is_spoof)
    print(f"[aenet_mt] AENet_C,S multi-task  |  {len(entries)} imgs "
          f"(live={n_live}, spoof={len(entries) - n_live})")
    print(f"[aenet_mt] loss = L_live + {lam['attack_type']}*L_type "
          f"+ {lam['illumination']}*L_light + {lam['attributes']}*L_attr  "
          f"(attributes masked to live only)")

    for epoch in range(epochs):
        # Track each task's loss separately -> proves the aux heads get gradients.
        agg = {"live": 0.0, "type": 0.0, "light": 0.0, "attr": 0.0, "total": 0.0}
        seen = 0
        for x, live, atk, ill, attrs in loader:
            x = x.to(dev)
            live = live.to(dev)
            atk = atk.to(dev)
            ill = ill.to(dev)
            attrs = attrs.to(dev)

            live_logits, atk_logits, ill_logits, attr_logits = model.forward_multitask(x)

            l_live = ce(live_logits, live)
            l_type = ce(atk_logits, atk)          # all images (live = class 0)
            l_light = ce(ill_logits, ill)         # all images (live = class 0)

            # Attributes: mask BCE to live images (spoof rows are zero placeholders).
            live_mask = live == 0
            if live_mask.any():
                attr_elem = bce(attr_logits, attrs)          # (B, 40)
                l_attr = attr_elem[live_mask].mean()         # avg over live rows*40
            else:
                l_attr = torch.zeros((), device=dev)

            loss = (l_live
                    + lam["attack_type"] * l_type
                    + lam["illumination"] * l_light
                    + lam["attributes"] * l_attr)

            optim.zero_grad()
            loss.backward()
            optim.step()

            bs = x.size(0)
            seen += bs
            agg["live"] += l_live.item() * bs
            agg["type"] += l_type.item() * bs
            agg["light"] += l_light.item() * bs
            agg["attr"] += float(l_attr) * bs
            agg["total"] += loss.item() * bs

        d = {k: v / max(seen, 1) for k, v in agg.items()}
        print(f"epoch {epoch + 1}/{epochs}  total={d['total']:.4f}  "
              f"live={d['live']:.4f}  type={d['type']:.4f}  "
              f"light={d['light']:.4f}  attr={d['attr']:.4f}")

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    # Save under "aenet_mt" name but as a plain AENet state_dict, so build_detector(
    # "aenet", weights=...) loads + scores it identically to the binary AENet.
    path = out / "aenet_mt.pth"
    torch.save({"state_dict": model.state_dict(), "model": "aenet",
                "multitask": True, "lambdas": lam}, path)
    return str(path)
