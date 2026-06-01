"""CDCN: Central Difference Convolutional Network (Yu et al., CVPR 2020).

Central-difference convolutions blend a vanilla conv with an aggregated-difference
term, sharpening sensitivity to the fine print/replay texture that separates live
from spoof faces. The backbone produces a depth map (auxiliary supervision during
training) plus a uniform 2-logit live/spoof head used for scoring.
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

from fsd.detectors._torch_base import TorchSpoofDetector
from fsd.detectors.registry import register


class CDCConv2d(nn.Module):
    """Conv2d + theta * central-difference term."""

    def __init__(self, in_c, out_c, kernel_size=3, stride=1, padding=1, theta=0.7):
        super().__init__()
        self.conv = nn.Conv2d(in_c, out_c, kernel_size, stride, padding, bias=False)
        self.theta = theta

    def forward(self, x):
        out_normal = self.conv(x)
        if self.theta == 0:
            return out_normal
        kernel_diff = self.conv.weight.sum(dim=(2, 3), keepdim=True)
        out_diff = F.conv2d(x, kernel_diff, stride=self.conv.stride, padding=0)
        return out_normal - self.theta * out_diff


def _cdc_block(in_c, out_c, theta):
    return nn.Sequential(
        CDCConv2d(in_c, out_c, theta=theta),
        nn.BatchNorm2d(out_c),
        nn.ReLU(inplace=True),
    )


class CDCN(nn.Module):
    def __init__(self, theta: float = 0.7, num_classes: int = 2):
        super().__init__()
        self.stem = _cdc_block(3, 64, theta)
        self.block1 = nn.Sequential(_cdc_block(64, 128, theta), _cdc_block(128, 128, theta), nn.MaxPool2d(2))
        self.block2 = nn.Sequential(_cdc_block(128, 128, theta), _cdc_block(128, 128, theta), nn.MaxPool2d(2))
        self.block3 = nn.Sequential(_cdc_block(128, 128, theta), _cdc_block(128, 128, theta), nn.MaxPool2d(2))
        # Auxiliary depth-map head (single-channel, supervised during training).
        self.depth_head = nn.Sequential(
            _cdc_block(128, 64, theta), CDCConv2d(64, 1, theta=theta), nn.Sigmoid()
        )
        # Uniform live/spoof classification head.
        self.classifier = nn.Sequential(
            nn.AdaptiveAvgPool2d(1), nn.Flatten(), nn.Linear(128, num_classes)
        )

    def forward(self, x):
        x = self.stem(x)
        x = self.block1(x)
        x = self.block2(x)
        feat = self.block3(x)
        return self.classifier(feat)

    def forward_with_depth(self, x):
        x = self.stem(x)
        x = self.block1(x)
        x = self.block2(x)
        feat = self.block3(x)
        return self.classifier(feat), self.depth_head(feat)


@register("cdcn")
def build_cdcn(weights: str | None = None, device: str | None = None, theta: float = 0.7, **_) -> TorchSpoofDetector:
    model = CDCN(theta=theta, num_classes=2)
    if weights:
        state = torch.load(weights, map_location="cpu", weights_only=False)
        model.load_state_dict(state.get("state_dict", state))
    return TorchSpoofDetector(model, input_size=256, normalize=True, device=device)
