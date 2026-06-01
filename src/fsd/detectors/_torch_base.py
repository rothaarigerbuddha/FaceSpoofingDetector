"""Shared base for torch-backed detectors: device handling, preprocessing, batching.

Torch is imported here (module import time), so this module is only loaded when a
torch model is actually built — keeping the dataset-analysis path torch-free.
"""

from __future__ import annotations

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms

from fsd.detectors.base import SpoofDetector

IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


def pick_device(prefer: str | None = None) -> "torch.device":
    if prefer:
        return torch.device(prefer)
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


class TorchSpoofDetector(SpoofDetector):
    """Base for single-image RGB detectors that output a 2-logit live/spoof head.

    Subclasses set ``self.model`` (an ``nn.Module`` returning [live, spoof] logits),
    ``self.input_size`` and call ``super().__init__``. ``spoof_index`` selects which
    softmax column is the attack probability (1 by convention).
    """

    spoof_index = 1

    def __init__(
        self,
        model: "torch.nn.Module",
        *,
        input_size: int = 224,
        normalize: bool = True,
        device: str | None = None,
    ):
        self.device = pick_device(device)
        self.model = model.to(self.device).eval()
        tfm = [transforms.Resize((input_size, input_size)), transforms.ToTensor()]
        if normalize:
            tfm.append(transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD))
        self.transform = transforms.Compose(tfm)

    def _to_tensor(self, image: np.ndarray) -> "torch.Tensor":
        return self.transform(Image.fromarray(image))

    @torch.no_grad()
    def predict_batch(self, images: list[np.ndarray]) -> list[float]:
        if not images:
            return []
        batch = torch.stack([self._to_tensor(im) for im in images]).to(self.device)
        logits = self.model(batch)
        if isinstance(logits, (tuple, list)):
            logits = logits[0]
        probs = F.softmax(logits, dim=1)[:, self.spoof_index]
        return probs.detach().cpu().numpy().astype(float).tolist()

    def predict(self, image: np.ndarray) -> float:
        return self.predict_batch([image])[0]
