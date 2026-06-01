"""CelebA-Spoof label schema, parsing, and dataset analysis.

The dataset ships a single JSON label file mapping each relative image path to a
list of 44 integer labels:

    [0:40]  -> 40 CelebA face attribute labels (live images only; 0/1 each)
    [40]    -> spoof type      (see SPOOF_TYPE)
    [41]    -> illumination    (see ILLUMINATION)
    [42]    -> environment     (see ENVIRONMENT)
    [43]    -> live/spoof      (0 = live, 1 = spoof)   <- the detection target

This module needs no deep-learning dependencies; it works on labels + files only.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Iterable


class LabelIndex(IntEnum):
    """Positions inside the 44-element label vector."""

    SPOOF_TYPE = 40
    ILLUMINATION = 41
    ENVIRONMENT = 42
    LIVE_SPOOF = 43


LABEL_VECTOR_LEN = 44

# Index -> human label, mirroring the dataset README annotation table.
SPOOF_TYPE: dict[int, str] = {
    0: "Live",
    1: "Photo",
    2: "Poster",
    3: "A4",
    4: "Face Mask",
    5: "Upper Body Mask",
    6: "Region Mask",
    7: "PC",
    8: "Pad",
    9: "Phone",
    10: "3D Mask",
}

ILLUMINATION: dict[int, str] = {
    0: "Live",
    1: "Normal",
    2: "Strong",
    3: "Back",
    4: "Dark",
}

ENVIRONMENT: dict[int, str] = {
    0: "Live",
    1: "Indoor",
    2: "Outdoor",
}

# The 40 CelebA face attributes, in canonical order (label indices 0..39).
CELEBA_ATTRIBUTES: tuple[str, ...] = (
    "5_o_Clock_Shadow", "Arched_Eyebrows", "Attractive", "Bags_Under_Eyes",
    "Bald", "Bangs", "Big_Lips", "Big_Nose", "Black_Hair", "Blond_Hair",
    "Blurry", "Brown_Hair", "Bushy_Eyebrows", "Chubby", "Double_Chin",
    "Eyeglasses", "Goatee", "Gray_Hair", "Heavy_Makeup", "High_Cheekbones",
    "Male", "Mouth_Slightly_Open", "Mustache", "Narrow_Eyes", "No_Beard",
    "Oval_Face", "Pale_Skin", "Pointy_Nose", "Receding_Hairline", "Rosy_Cheeks",
    "Sideburns", "Smiling", "Straight_Hair", "Wavy_Hair", "Wearing_Earrings",
    "Wearing_Hat", "Wearing_Lipstick", "Wearing_Necklace", "Wearing_Necktie",
    "Young",
)

LIVE = 0
SPOOF = 1


@dataclass(frozen=True)
class LabelEntry:
    """A single labelled image, parsed from the raw 44-int vector."""

    path: str
    raw: tuple[int, ...]

    @property
    def is_spoof(self) -> bool:
        return self.raw[LabelIndex.LIVE_SPOOF] == SPOOF

    @property
    def live_spoof(self) -> int:
        return self.raw[LabelIndex.LIVE_SPOOF]

    @property
    def spoof_type(self) -> int:
        return self.raw[LabelIndex.SPOOF_TYPE]

    @property
    def illumination(self) -> int:
        return self.raw[LabelIndex.ILLUMINATION]

    @property
    def environment(self) -> int:
        return self.raw[LabelIndex.ENVIRONMENT]

    @property
    def attributes(self) -> tuple[int, ...]:
        return self.raw[:40]


def load_labels(label_json: str | Path) -> list[LabelEntry]:
    """Load and validate the CelebA-Spoof label JSON into LabelEntry records."""
    label_json = Path(label_json)
    with label_json.open(encoding="utf-8") as f:
        raw: dict[str, list[int]] = json.load(f)

    entries: list[LabelEntry] = []
    for path, vec in raw.items():
        if len(vec) != LABEL_VECTOR_LEN:
            raise ValueError(
                f"{path}: expected {LABEL_VECTOR_LEN} labels, got {len(vec)}"
            )
        entries.append(LabelEntry(path=path.replace("\\", "/"), raw=tuple(int(v) for v in vec)))
    return entries


@dataclass
class DatasetStats:
    """Aggregate statistics + integrity findings for a labelled split."""

    total: int = 0
    live: int = 0
    spoof: int = 0
    spoof_type: Counter = field(default_factory=Counter)
    illumination: Counter = field(default_factory=Counter)
    environment: Counter = field(default_factory=Counter)
    subjects: int = 0
    # Integrity (only populated when check_files=True)
    checked_files: bool = False
    missing_images: list[str] = field(default_factory=list)
    missing_bbox: list[str] = field(default_factory=list)

    @property
    def spoof_ratio(self) -> float:
        return self.spoof / self.total if self.total else 0.0

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "live": self.live,
            "spoof": self.spoof,
            "spoof_ratio": round(self.spoof_ratio, 4),
            "subjects": self.subjects,
            "spoof_type": {SPOOF_TYPE.get(k, str(k)): v for k, v in sorted(self.spoof_type.items())},
            "illumination": {ILLUMINATION.get(k, str(k)): v for k, v in sorted(self.illumination.items())},
            "environment": {ENVIRONMENT.get(k, str(k)): v for k, v in sorted(self.environment.items())},
            "integrity": {
                "checked": self.checked_files,
                "missing_images": len(self.missing_images),
                "missing_bbox": len(self.missing_bbox),
            },
        }


def _subject_of(path: str) -> str | None:
    """Best-effort subject id: .../Data/<split>/<subject>/<live|spoof>/<file>."""
    parts = Path(path).parts
    for i, p in enumerate(parts):
        if p in ("live", "spoof") and i > 0:
            return parts[i - 1]
    return None


def analyze_dataset(
    entries: Iterable[LabelEntry],
    *,
    data_root: str | Path | None = None,
    check_files: bool = False,
) -> DatasetStats:
    """Compute distribution statistics and (optionally) on-disk integrity checks.

    When check_files=True and data_root is given, every image path is verified to
    exist along with its sibling ``<name>_BB.txt`` bounding-box file.
    """
    stats = DatasetStats()
    root = Path(data_root) if data_root is not None else None
    subjects: set[str] = set()

    for e in entries:
        stats.total += 1
        if e.is_spoof:
            stats.spoof += 1
        else:
            stats.live += 1
        stats.spoof_type[e.spoof_type] += 1
        stats.illumination[e.illumination] += 1
        stats.environment[e.environment] += 1

        subj = _subject_of(e.path)
        if subj is not None:
            subjects.add(subj)

        if check_files and root is not None:
            img = root / e.path
            if not img.exists():
                stats.missing_images.append(e.path)
            bb = img.with_name(img.stem + "_BB.txt")
            if not bb.exists():
                stats.missing_bbox.append(e.path)

    stats.subjects = len(subjects)
    stats.checked_files = check_files and root is not None
    return stats
