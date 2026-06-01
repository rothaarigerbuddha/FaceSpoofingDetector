"""Common interface every spoof detector implements.

A detector maps an RGB face image (uint8, HxWxC, already BB-cropped) to a spoof
probability in [0, 1] where higher means "more likely a presentation attack".
This mirrors the official CelebA-Spoof ``detector.py`` contract so results stay
comparable with the published benchmark.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class SpoofDetector(ABC):
    name: str = "base"

    @abstractmethod
    def predict(self, image: np.ndarray) -> float:
        """Return spoof probability in [0, 1] for one RGB uint8 image (H, W, 3)."""
        raise NotImplementedError

    def predict_batch(self, images: list[np.ndarray]) -> list[float]:
        """Default: per-image loop. Torch models override for batched inference."""
        return [self.predict(img) for img in images]
