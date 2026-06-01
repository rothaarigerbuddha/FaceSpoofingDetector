"""AENet: the official CelebA-Spoof baseline (ResNet-18 multi-task).

Architecture ported from the dataset repo's ``models.py`` so the released
``ckpt_iter.pth.tar`` checkpoint loads directly. Only the live/spoof head is used
for scoring; the auxiliary semantic/geometry heads remain for weight compatibility.
"""

from __future__ import annotations

import math
from pathlib import Path

import torch
import torch.nn as nn

from fsd.detectors._torch_base import TorchSpoofDetector
from fsd.detectors.registry import register


def _conv3x3(in_planes, out_planes, stride=1):
    return nn.Conv2d(in_planes, out_planes, kernel_size=3, stride=stride, padding=1, bias=False)


class BasicBlock(nn.Module):
    expansion = 1

    def __init__(self, inplanes, planes, stride=1, downsample=None):
        super().__init__()
        self.conv1 = _conv3x3(inplanes, planes, stride)
        self.bn1 = nn.BatchNorm2d(planes)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = _conv3x3(planes, planes)
        self.bn2 = nn.BatchNorm2d(planes)
        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        residual = x
        out = self.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        if self.downsample is not None:
            residual = self.downsample(x)
        out += residual
        return self.relu(out)


class AENet(nn.Module):
    def __init__(self, block=BasicBlock, layers=(2, 2, 2, 2), num_classes=2):
        super().__init__()
        self.inplanes = 64
        self.conv1 = nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3, bias=False)
        self.bn1 = nn.BatchNorm2d(64)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        self.layer1 = self._make_layer(block, 64, layers[0])
        self.layer2 = self._make_layer(block, 128, layers[1], stride=2)
        self.layer3 = self._make_layer(block, 256, layers[2], stride=2)
        self.layer4 = self._make_layer(block, 512, layers[3], stride=2)
        self.avgpool = nn.AvgPool2d(7, stride=1)

        exp = block.expansion
        # Auxiliary semantic heads (kept for checkpoint compatibility).
        self.fc_live_attribute = nn.Linear(512 * exp, 40)
        self.fc_attack = nn.Linear(512 * exp, 11)
        self.fc_light = nn.Linear(512 * exp, 5)
        # Live/Spoof head (the one we score with).
        self.fc_live = nn.Linear(512 * exp, num_classes)
        # Geometry embedding modules (kept for checkpoint compatibility).
        self.upsample14 = nn.Upsample((14, 14), mode="bilinear", align_corners=False)
        self.depth_final = nn.Conv2d(512, 1, kernel_size=3, stride=1, padding=1, bias=False)
        self.reflect_final = nn.Conv2d(512, 3, kernel_size=3, stride=1, padding=1, bias=False)
        self.sigmoid = nn.Sigmoid()

        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
                m.weight.data.normal_(0, math.sqrt(2.0 / n))
            elif isinstance(m, nn.BatchNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()

    def _make_layer(self, block, planes, blocks, stride=1):
        downsample = None
        if stride != 1 or self.inplanes != planes * block.expansion:
            downsample = nn.Sequential(
                nn.Conv2d(self.inplanes, planes * block.expansion, kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(planes * block.expansion),
            )
        layers = [block(self.inplanes, planes, stride, downsample)]
        self.inplanes = planes * block.expansion
        for _ in range(1, blocks):
            layers.append(block(self.inplanes, planes))
        return nn.Sequential(*layers)

    def forward(self, x):
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.maxpool(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        x = self.avgpool(x).flatten(1)
        return self.fc_live(x)


def _load_checkpoint(model: nn.Module, ckpt_path: str | Path) -> None:
    """Load a state dict, tolerating the ``module.`` DataParallel prefix and head shape gaps."""
    ckpt = torch.load(str(ckpt_path), map_location="cpu", weights_only=False)
    state = ckpt.get("state_dict", ckpt) if isinstance(ckpt, dict) else ckpt
    own = model.state_dict()
    loaded = 0
    for name, param in state.items():
        key = name.replace("module.", "")
        if key in own and own[key].shape == getattr(param, "shape", own[key].shape):
            own[key].copy_(param.data if hasattr(param, "data") else param)
            loaded += 1
    if loaded == 0:
        raise RuntimeError(f"No matching parameters loaded from {ckpt_path}")


@register("aenet")
def build_aenet(weights: str | None = None, device: str | None = None, **_) -> TorchSpoofDetector:
    model = AENet(num_classes=2)
    if weights:
        _load_checkpoint(model, weights)
    # AENet's published preprocessing is Resize(224) + ToTensor (no ImageNet normalize).
    return TorchSpoofDetector(model, input_size=224, normalize=False, device=device)
