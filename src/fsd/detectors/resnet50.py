"""ResNet-50 transfer-learning baseline.

An ImageNet-pretrained ResNet-50 with a 2-class head, fine-tuned on the live/spoof
split. The classic deep-CNN reference point: heavier than EfficientNet/MobileNet but
a familiar, well-understood backbone, so it grounds the comparison against the
ubiquitous baseline. Same recipe as the other timm wrappers (224px, ImageNet normalize).
"""

from __future__ import annotations

import torch

from fsd.detectors._torch_base import TorchSpoofDetector
from fsd.detectors.registry import register


def _create_timm(model_name: str, num_classes: int, pretrained: bool):
    import timm

    return timm.create_model(model_name, pretrained=pretrained, num_classes=num_classes)


@register("resnet50")
def build_resnet50(weights: str | None = None, device: str | None = None, **_) -> TorchSpoofDetector:
    model = _create_timm("resnet50", num_classes=2, pretrained=weights is None)
    if weights:
        state = torch.load(weights, map_location="cpu", weights_only=False)
        model.load_state_dict(state.get("state_dict", state))
    return TorchSpoofDetector(model, input_size=224, normalize=True, device=device)
