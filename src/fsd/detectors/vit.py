"""ViT-B/16 transformer baseline.

An ImageNet-pretrained Vision Transformer with a 2-class head. Self-attention over
image patches captures global consistency cues (lighting, moiré, bezel context)
that complement the convolutional texture models, and tends to generalise well.
"""

from __future__ import annotations

import torch

from fsd.detectors._torch_base import TorchSpoofDetector
from fsd.detectors.registry import register


@register("vit")
def build_vit(weights: str | None = None, device: str | None = None, **_) -> TorchSpoofDetector:
    import timm

    model = timm.create_model("vit_base_patch16_224", pretrained=weights is None, num_classes=2)
    if weights:
        state = torch.load(weights, map_location="cpu", weights_only=False)
        model.load_state_dict(state.get("state_dict", state))
    return TorchSpoofDetector(model, input_size=224, normalize=True, device=device)
