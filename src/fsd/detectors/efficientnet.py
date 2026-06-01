"""EfficientNet-B0 transfer-learning baseline.

An ImageNet-pretrained EfficientNet-B0 with a 2-class head, fine-tuned on the
live/spoof split. Represents the strong, pragmatic "fine-tune a good backbone"
approach that is often surprisingly competitive on CelebA-Spoof.
"""

from __future__ import annotations

import torch

from fsd.detectors._torch_base import TorchSpoofDetector
from fsd.detectors.registry import register


def _create_timm(model_name: str, num_classes: int, pretrained: bool):
    import timm

    return timm.create_model(model_name, pretrained=pretrained, num_classes=num_classes)


@register("efficientnet")
def build_efficientnet(weights: str | None = None, device: str | None = None, **_) -> TorchSpoofDetector:
    model = _create_timm("efficientnet_b0", num_classes=2, pretrained=weights is None)
    if weights:
        state = torch.load(weights, map_location="cpu", weights_only=False)
        model.load_state_dict(state.get("state_dict", state))
    return TorchSpoofDetector(model, input_size=224, normalize=True, device=device)
