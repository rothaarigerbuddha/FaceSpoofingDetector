"""DeepPixBiS: Deep Pixel-wise Binary Supervision (George & Marcel, ICB 2019).

A DenseNet-121 trunk feeds a 1x1 conv that predicts a per-pixel "liveness" map;
the map is also pooled to a uniform 2-logit live/spoof head for scoring. The
pixel map gives dense supervision during training (every spatial location labelled
live/spoof), which is cheap and robust for print/replay attacks.
"""

from __future__ import annotations

import torch
import torch.nn as nn

from fsd.detectors._torch_base import TorchSpoofDetector
from fsd.detectors.registry import register


class DeepPixBiS(nn.Module):
    def __init__(self, pretrained_backbone: bool = True, num_classes: int = 2):
        super().__init__()
        try:
            from torchvision.models import DenseNet121_Weights, densenet121

            weights = DenseNet121_Weights.IMAGENET1K_V1 if pretrained_backbone else None
            dense = densenet121(weights=weights)
        except Exception:  # offline / no weights cache
            from torchvision.models import densenet121

            dense = densenet121(weights=None)
        # Use feature blocks up to the 14x14 stage (through transition3).
        self.enc = nn.Sequential(*list(dense.features.children())[:10])
        # Infer channel count from a dummy forward (robust to backbone changes).
        with torch.no_grad():
            feat_c = self.enc(torch.zeros(1, 3, 224, 224)).shape[1]
        self.pixel_head = nn.Conv2d(feat_c, 1, kernel_size=1)
        self.sigmoid = nn.Sigmoid()
        # Uniform classification head over the pixel-map statistics.
        self.classifier = nn.Linear(feat_c, num_classes)
        self.pool = nn.AdaptiveAvgPool2d(1)

    def forward(self, x):
        feat = self.enc(x)
        return self.classifier(self.pool(feat).flatten(1))

    def forward_with_map(self, x):
        feat = self.enc(x)
        pix = self.sigmoid(self.pixel_head(feat))
        logits = self.classifier(self.pool(feat).flatten(1))
        return logits, pix


@register("deeppixbis")
def build_deeppixbis(weights: str | None = None, device: str | None = None, **_) -> TorchSpoofDetector:
    model = DeepPixBiS(pretrained_backbone=weights is None, num_classes=2)
    if weights:
        state = torch.load(weights, map_location="cpu", weights_only=False)
        model.load_state_dict(state.get("state_dict", state))
    return TorchSpoofDetector(model, input_size=224, normalize=True, device=device)
