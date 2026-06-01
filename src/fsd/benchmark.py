"""End-to-end local benchmark: train N models on a local dataset, evaluate all, save.

This is the portable equivalent of the Kaggle notebook (scripts/kaggle_train.py):
run it on any machine that has the dataset on disk and ``pip install -e ".[torch]"``.
It trains each requested model (skipping any given pretrained weights), then scores
every model on the test split and writes a single ``results.json``.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from fsd.dataset.celeba_spoof import load_labels
from fsd.eval.compare import ModelSpec, compare_models, sample_entries


def run_benchmark(
    *,
    data_root: str,
    train_labels: str,
    test_labels: str,
    models: list[str],
    n_train: int | None,
    n_test: int | None,
    epochs: int,
    batch_size: int,
    lr: float,
    device: str | None,
    out_dir: str,
    pretrained: dict[str, str] | None = None,
) -> dict:
    """Train the non-pretrained models, evaluate all, and write results.json.

    pretrained: optional ``{model_name: weights_path}`` for models to evaluate
    as-is without training (e.g. ``{"aenet": "weights/ckpt_iter.pth.tar"}``).
    """
    from fsd.train import train_model  # lazy: torch only needed here

    pretrained = pretrained or {}
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    weights_map: dict[str, str] = dict(pretrained)

    # 1) Train every model that wasn't supplied as pretrained.
    for name in models:
        if name in pretrained:
            print(f"[skip-train] {name}: using pretrained {pretrained[name]}")
            continue
        print(f"[train] {name}: {n_train or 'all'} imgs, {epochs} epochs")
        t0 = time.time()
        path = train_model(
            model_name=name,
            labels=train_labels,
            data_root=data_root,
            epochs=epochs,
            batch_size=batch_size,
            lr=lr,
            limit=n_train,
            device=device,
            out_dir=out_dir,
        )
        weights_map[name] = path
        print(f"[train] {name}: done in {time.time() - t0:.0f}s -> {path}")

    # 2) Evaluate every model on the same test split.
    test_entries = sample_entries(load_labels(test_labels), limit=n_test, seed=1)
    print(f"[eval] {len(models)} models on {len(test_entries)} test images")
    specs = [ModelSpec(name=m, weights=weights_map.get(m)) for m in models]
    results = compare_models(specs, test_entries, data_root, batch_size=batch_size, device=device)

    payload = {
        "config": {
            "data_root": data_root,
            "n_train": n_train,
            "n_test": len(test_entries),
            "epochs": epochs,
            "batch_size": batch_size,
            "lr": lr,
            "models": models,
            "pretrained": pretrained,
        },
        "weights": weights_map,
        "results": {k: v.to_dict() for k, v in results.items()},
    }
    results_path = out / "results.json"
    results_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[done] wrote {results_path}")
    return payload
