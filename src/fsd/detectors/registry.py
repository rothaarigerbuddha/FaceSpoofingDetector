"""Model registry: name -> lazy factory.

Wrappers import torch only when their factory runs, so dataset analysis and the
registry listing stay usable in a torch-free environment.
"""

from __future__ import annotations

from typing import Callable

from fsd.detectors.base import SpoofDetector

# Short, human-facing description of each model for `fsd models`.
MODEL_INFO: dict[str, str] = {
    "aenet": "Official CelebA-Spoof baseline (ResNet-18 multi-task). Has pretrained weights.",
    "cdcn": "Central Difference Conv Network: fine-grained texture, depth-supervised.",
    "deeppixbis": "DenseNet + pixel-wise binary supervision. Lightweight.",
    "efficientnet": "EfficientNet-B0 transfer-learning binary classifier.",
    "mobilenetv3": "MobileNetV3-Large transfer-learning binary classifier. Mobile/edge baseline.",
    "resnet50": "ResNet-50 transfer-learning binary classifier. Classic deep-CNN baseline.",
    "vit": "ViT-B/16 transformer fine-tuned for live/spoof.",
}

_FACTORIES: dict[str, Callable[..., SpoofDetector]] = {}


def register(name: str):
    def deco(factory: Callable[..., SpoofDetector]):
        _FACTORIES[name] = factory
        return factory

    return deco


def available_models() -> list[str]:
    return sorted(MODEL_INFO)


def build_detector(name: str, **kwargs) -> SpoofDetector:
    name = name.lower()
    if name not in _FACTORIES:
        # Import wrappers on demand to populate factories.
        _ensure_loaded(name)
    if name not in _FACTORIES:
        raise KeyError(f"Unknown model '{name}'. Available: {available_models()}")
    return _FACTORIES[name](**kwargs)


def _ensure_loaded(name: str) -> None:
    import importlib

    module_for = {
        "aenet": "fsd.detectors.aenet",
        "cdcn": "fsd.detectors.cdcn",
        "deeppixbis": "fsd.detectors.deeppixbis",
        "efficientnet": "fsd.detectors.efficientnet",
        "mobilenetv3": "fsd.detectors.mobilenetv3",
        "resnet50": "fsd.detectors.resnet50",
        "vit": "fsd.detectors.vit",
    }
    if name in module_for:
        importlib.import_module(module_for[name])
