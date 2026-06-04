"""MobileNetV3-Large transfer-learning baseline.

An ImageNet-pretrained MobileNetV3-Large (mobilenetv3_large_100) with a 2-class
head, fine-tuned on the live/spoof split. Represents the *mobile/edge* end of the
design space: far fewer FLOPs than EfficientNet/ViT, so it anchors the speed axis
of the comparison while staying a strong, pragmatic "fine-tune a good backbone"
baseline. Same recipe as the EfficientNet wrapper (224px, ImageNet normalize).
"""

from __future__ import annotations

import torch

from fsd.detectors._torch_base import TorchSpoofDetector
from fsd.detectors.registry import register


def _create_timm(model_name: str, num_classes: int, pretrained: bool):
    import timm

    return timm.create_model(model_name, pretrained=pretrained, num_classes=num_classes)


@register("mobilenetv3")
def build_mobilenetv3(weights: str | None = None, device: str | None = None, **_) -> TorchSpoofDetector:
    model = _create_timm("mobilenetv3_large_100", num_classes=2, pretrained=weights is None)
    if weights:
        state = torch.load(weights, map_location="cpu", weights_only=False)
        model.load_state_dict(state.get("state_dict", state))
    return TorchSpoofDetector(model, input_size=224, normalize=True, device=device)
