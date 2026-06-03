"""Compact fine-tuning loop for the live/spoof head of any registered model.

Trains the uniform 2-logit classification head (and backbone) on the CelebA-Spoof
split using cross-entropy. Auxiliary depth/pixel-map heads are left to their
defaults here; this keeps the trainer model-agnostic so all five wrappers share
one path. Torch is imported lazily by the caller (the `fsd train` subcommand).
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
from fsd.multitask import AuxWeights, aux_targets, multitask_loss
from fsd.utils.image import read_image_rgb


class CelebASpoofDataset(Dataset):
    """Live/spoof crops for training.

    With ``multitask=True`` each item also carries the semantic auxiliary targets
    (spoof type, illumination, 40 face attributes + a live-only attribute mask)
    used by AENet's multi-task heads; otherwise only the live/spoof label is
    returned, exactly as before.
    """

    def __init__(
        self,
        entries: list[LabelEntry],
        data_root: str | Path,
        input_size: int,
        normalize: bool,
        *,
        multitask: bool = False,
    ):
        self.entries = entries
        self.data_root = Path(data_root)
        self.multitask = multitask
        tfm = [transforms.Resize((input_size, input_size)), transforms.ToTensor()]
        if normalize:
            tfm.append(transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD))
        self.transform = transforms.Compose(tfm)

    def __len__(self) -> int:
        return len(self.entries)

    def __getitem__(self, idx: int):
        e = self.entries[idx]
        try:
            img = read_image_rgb(self.data_root / e.path, crop=True)
        except FileNotFoundError:
            img = np.zeros((self.transform.transforms[0].size[0],) * 2 + (3,), dtype=np.uint8)
        x = self.transform(Image.fromarray(img))
        if self.multitask:
            return x, aux_targets(e)
        return x, int(e.raw[LabelIndex.LIVE_SPOOF])


# input_size / normalize per model, matching each wrapper's inference transform.
_MODEL_PREPROC = {
    "aenet": (224, False),
    "cdcn": (256, True),
    "deeppixbis": (224, True),
    "efficientnet": (224, True),
    "vit": (224, True),
}


def _bare_model(name: str) -> nn.Module:
    """Build the underlying nn.Module (pretrained backbone where available)."""
    from fsd.detectors.registry import build_detector

    return build_detector(name, weights=None, device="cpu").model


def _to_device(target, dev):
    """Move a label batch (a tensor, or the multitask dict of tensors) to ``dev``."""
    if isinstance(target, dict):
        return {k: v.to(dev) for k, v in target.items()}
    return target.to(dev)


def train_model(
    *,
    model_name: str,
    labels: str,
    data_root: str,
    epochs: int = 3,
    batch_size: int = 64,
    lr: float = 1e-4,
    limit: int | None = None,
    device: str | None = None,
    out_dir: str = "weights",
    num_workers: int = 4,
    multitask: bool = False,
    aux_weights: AuxWeights | None = None,
    out_name: str | None = None,
) -> str:
    """Fine-tune the live/spoof head (and backbone) of ``model_name``.

    ``multitask=True`` (AENet only) additionally supervises the spoof-type,
    illumination and face-attribute heads with the weighted loss in
    ``fsd.multitask``; the saved checkpoint and inference path are unchanged.
    ``out_name`` overrides the weights filename stem (useful to keep the binary
    and multi-task AENet checkpoints side by side).
    """
    dev = pick_device(device)
    input_size, normalize = _MODEL_PREPROC.get(model_name, (224, True))

    if multitask and model_name != "aenet":
        raise ValueError(
            f"multitask training is only supported for 'aenet' (its heads carry the "
            f"semantic labels), not '{model_name}'."
        )
    aux_weights = aux_weights or AuxWeights()

    entries = sample_entries(load_labels(labels), limit=limit, seed=0)
    ds = CelebASpoofDataset(entries, data_root, input_size, normalize, multitask=multitask)
    loader = DataLoader(ds, batch_size=batch_size, shuffle=True, num_workers=num_workers, pin_memory=True)

    model = _bare_model(model_name).to(dev).train()
    optim = torch.optim.AdamW(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    if multitask:
        print(f"[multitask] AENet_C,S aux weights: {aux_weights.as_dict()}")

    for epoch in range(epochs):
        running = 0.0
        seen = 0
        head_sums: dict[str, float] = {}
        for x, target in loader:
            x = x.to(dev)
            target = _to_device(target, dev)
            optim.zero_grad()
            if multitask:
                heads = model.forward_multitask(x)
                loss, log = multitask_loss(heads, target, aux_weights)
                for k, v in log.items():
                    head_sums[k] = head_sums.get(k, 0.0) + v * x.size(0)
            else:
                logits = model(x)
                if isinstance(logits, (tuple, list)):
                    logits = logits[0]
                loss = criterion(logits, target)
            loss.backward()
            optim.step()
            running += loss.item() * x.size(0)
            seen += x.size(0)
        msg = f"epoch {epoch + 1}/{epochs}  loss={running / max(seen, 1):.4f}"
        if multitask:
            parts = "  ".join(f"{k}={head_sums[k] / max(seen, 1):.4f}" for k in ("live", "attack", "light", "attribute"))
            msg += f"  [{parts}]"
        print(msg)

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{out_name or model_name}.pth"
    torch.save({"state_dict": model.state_dict(), "model": model_name, "multitask": multitask}, path)
    return str(path)
