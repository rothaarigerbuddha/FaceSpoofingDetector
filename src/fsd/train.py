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
from fsd.utils.image import read_image_rgb


class CelebASpoofDataset(Dataset):
    def __init__(self, entries: list[LabelEntry], data_root: str | Path, input_size: int, normalize: bool):
        self.entries = entries
        self.data_root = Path(data_root)
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
        y = int(e.raw[LabelIndex.LIVE_SPOOF])
        return x, y


# input_size / normalize per model, matching each wrapper's inference transform.
# AENet now uses ImageNet normalize (matches the official client.py and the
# ImageNet trunk warm-start in detectors/aenet.py), so train and eval agree.
_MODEL_PREPROC = {
    "aenet": (224, True),
    "cdcn": (256, True),
    "deeppixbis": (224, True),
    "efficientnet": (224, True),
    "vit": (224, True),
}


def _bare_model(name: str) -> nn.Module:
    """Build the underlying nn.Module (pretrained backbone where available)."""
    from fsd.detectors.registry import build_detector

    return build_detector(name, weights=None, device="cpu").model


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
) -> str:
    dev = pick_device(device)
    input_size, normalize = _MODEL_PREPROC.get(model_name, (224, True))

    entries = sample_entries(load_labels(labels), limit=limit, seed=0)
    ds = CelebASpoofDataset(entries, data_root, input_size, normalize)
    loader = DataLoader(ds, batch_size=batch_size, shuffle=True, num_workers=num_workers, pin_memory=True)

    model = _bare_model(model_name).to(dev).train()
    optim = torch.optim.AdamW(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    for epoch in range(epochs):
        running = 0.0
        seen = 0
        for x, y in loader:
            x, y = x.to(dev), y.to(dev)
            optim.zero_grad()
            logits = model(x)
            if isinstance(logits, (tuple, list)):
                logits = logits[0]
            loss = criterion(logits, y)
            loss.backward()
            optim.step()
            running += loss.item() * x.size(0)
            seen += x.size(0)
        print(f"epoch {epoch + 1}/{epochs}  loss={running / max(seen, 1):.4f}")

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{model_name}.pth"
    torch.save({"state_dict": model.state_dict(), "model": model_name}, path)
    return str(path)
