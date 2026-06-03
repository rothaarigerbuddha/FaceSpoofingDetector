"""fsd command-line interface: analyze | models | detect | compare | train.

``analyze`` and ``models`` work with zero deep-learning dependencies. ``detect``,
``compare`` and ``train`` import torch lazily and only when invoked.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from fsd import __version__


def _print(msg: str = "") -> None:
    sys.stdout.write(msg + "\n")


# --------------------------------------------------------------------------- #
# analyze
# --------------------------------------------------------------------------- #
def cmd_analyze(args: argparse.Namespace) -> int:
    from fsd.dataset.celeba_spoof import analyze_dataset, load_labels

    entries = load_labels(args.labels)
    stats = analyze_dataset(
        entries, data_root=args.data_root, check_files=args.check_files
    )
    data = stats.to_dict()

    if args.json:
        Path(args.json).write_text(json.dumps(data, indent=2), encoding="utf-8")
        _print(f"Wrote {args.json}")
        return 0

    _print(f"CelebA-Spoof analysis  ({args.labels})")
    _print("=" * 56)
    _print(f"Total images : {data['total']:,}")
    _print(f"  live       : {data['live']:,}")
    _print(f"  spoof      : {data['spoof']:,}  (ratio {data['spoof_ratio']:.3f})")
    _print(f"Subjects     : {data['subjects']:,}")
    _print("\nSpoof type distribution:")
    for k, v in data["spoof_type"].items():
        _print(f"  {k:<16} {v:>9,}")
    _print("\nIllumination:")
    for k, v in data["illumination"].items():
        _print(f"  {k:<16} {v:>9,}")
    _print("\nEnvironment:")
    for k, v in data["environment"].items():
        _print(f"  {k:<16} {v:>9,}")
    if data["integrity"]["checked"]:
        _print("\nIntegrity:")
        _print(f"  missing images : {data['integrity']['missing_images']:,}")
        _print(f"  missing bbox   : {data['integrity']['missing_bbox']:,}")
    return 0


# --------------------------------------------------------------------------- #
# models
# --------------------------------------------------------------------------- #
def cmd_models(_args: argparse.Namespace) -> int:
    from fsd.detectors.registry import MODEL_INFO, available_models

    _print("Available models:")
    for name in available_models():
        _print(f"  {name:<14} {MODEL_INFO[name]}")
    return 0


# --------------------------------------------------------------------------- #
# detect
# --------------------------------------------------------------------------- #
def cmd_detect(args: argparse.Namespace) -> int:
    from fsd.detectors.registry import build_detector
    from fsd.utils.image import read_image_rgb

    detector = build_detector(args.model, weights=args.weights, device=args.device)
    img = read_image_rgb(args.image, crop=not args.no_crop)
    prob = detector.predict(img)
    verdict = "SPOOF" if prob >= args.threshold else "LIVE"
    if args.json:
        _print(json.dumps({"image": args.image, "model": args.model,
                           "spoof_probability": prob, "verdict": verdict}))
    else:
        _print(f"{args.image}")
        _print(f"  model={args.model}  spoof_prob={prob:.4f}  ->  {verdict}")
    return 0


# --------------------------------------------------------------------------- #
# compare
# --------------------------------------------------------------------------- #
def _parse_weights(items: list[str] | None) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in items or []:
        if "=" not in item:
            raise SystemExit(f"--weights expects name=path, got '{item}'")
        name, path = item.split("=", 1)
        out[name.strip()] = path.strip()
    return out


def cmd_compare(args: argparse.Namespace) -> int:
    from fsd.dataset.celeba_spoof import load_labels
    from fsd.eval.compare import ModelSpec, compare_models, sample_entries

    weights = _parse_weights(args.weights)
    model_names = [m.strip() for m in args.models.split(",") if m.strip()]
    specs = [ModelSpec(name=m, weights=weights.get(m)) for m in model_names]

    entries = sample_entries(load_labels(args.labels), limit=args.limit, seed=args.seed)
    _print(f"Comparing {len(specs)} model(s) on {len(entries):,} images...")
    results = compare_models(
        specs, entries, args.data_root,
        batch_size=args.batch_size, threshold=args.threshold, device=args.device,
    )

    if args.json:
        Path(args.json).write_text(
            json.dumps({k: v.to_dict() for k, v in results.items()}, indent=2),
            encoding="utf-8",
        )
        _print(f"Wrote {args.json}")
        return 0

    header = f"{'model':<14}{'AUC':>8}{'EER':>8}{'ACER':>8}{'TPR@1e-2':>10}{'TPR@1e-3':>10}"
    _print(header)
    _print("-" * len(header))
    for name, r in results.items():
        d = r.to_dict()
        t = d["tpr_at_fpr"]
        _print(f"{name:<14}{d['auc']:>8.4f}{d['eer']:>8.4f}{d['acer']:>8.4f}"
               f"{t.get('0.01', 0):>10.4f}{t.get('0.001', 0):>10.4f}")
    return 0


# --------------------------------------------------------------------------- #
# train
# --------------------------------------------------------------------------- #
def cmd_train(args: argparse.Namespace) -> int:
    from fsd.multitask import AuxWeights
    from fsd.train import train_model

    aux_weights = AuxWeights(
        attack=args.lambda_attack, light=args.lambda_light, attribute=args.lambda_attr
    )
    out = train_model(
        model_name=args.model,
        labels=args.labels,
        data_root=args.data_root,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        limit=args.limit,
        device=args.device,
        out_dir=args.out,
        multitask=args.multitask,
        aux_weights=aux_weights,
        out_name=args.out_name,
    )
    _print(f"Saved weights to {out}")
    return 0


# --------------------------------------------------------------------------- #
# benchmark (train several models on a local dataset + evaluate all)
# --------------------------------------------------------------------------- #
def cmd_benchmark(args: argparse.Namespace) -> int:
    from fsd.benchmark import run_benchmark

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    pretrained = _parse_weights(args.pretrained)
    payload = run_benchmark(
        data_root=args.data_root,
        train_labels=args.train_labels,
        test_labels=args.test_labels,
        models=models,
        n_train=args.n_train or None,
        n_test=args.n_test or None,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        device=args.device,
        out_dir=args.out,
        pretrained=pretrained,
    )

    header = f"{'model':<14}{'AUC':>8}{'EER':>8}{'ACER':>8}{'TPR@1e-2':>10}"
    _print(header)
    _print("-" * len(header))
    for name, r in payload["results"].items():
        t = r["tpr_at_fpr"]
        _print(f"{name:<14}{r['auc']:>8.4f}{r['eer']:>8.4f}{r['acer']:>8.4f}{t.get('0.01', 0):>10.4f}")
    return 0


# --------------------------------------------------------------------------- #
# parser
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="fsd", description="CelebA-Spoof analysis & face anti-spoofing model comparison.")
    p.add_argument("--version", action="version", version=f"fsd {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("analyze", help="Dataset statistics + integrity checks.")
    a.add_argument("--labels", required=True, help="Path to the label JSON file.")
    a.add_argument("--data-root", help="Dataset root (required for --check-files).")
    a.add_argument("--check-files", action="store_true", help="Verify images + _BB.txt exist on disk.")
    a.add_argument("--json", help="Write the report to this JSON file instead of stdout.")
    a.set_defaults(func=cmd_analyze)

    m = sub.add_parser("models", help="List available anti-spoofing models.")
    m.set_defaults(func=cmd_models)

    d = sub.add_parser("detect", help="Score a single image with one model.")
    d.add_argument("--model", required=True)
    d.add_argument("--image", required=True)
    d.add_argument("--weights", help="Path to model checkpoint.")
    d.add_argument("--threshold", type=float, default=0.5)
    d.add_argument("--device", help="cpu | cuda | cuda:0 ...")
    d.add_argument("--no-crop", action="store_true", help="Skip BB face crop.")
    d.add_argument("--json", action="store_true")
    d.set_defaults(func=cmd_detect)

    c = sub.add_parser("compare", help="Evaluate + compare several models on a labelled split.")
    c.add_argument("--labels", required=True)
    c.add_argument("--data-root", required=True)
    c.add_argument("--models", required=True, help="Comma-separated model names.")
    c.add_argument("--weights", nargs="*", help="Per-model weights as name=path.")
    c.add_argument("--limit", type=int, help="Max images to evaluate (balanced sample).")
    c.add_argument("--batch-size", type=int, default=64)
    c.add_argument("--threshold", type=float, default=0.5)
    c.add_argument("--seed", type=int, default=0)
    c.add_argument("--device")
    c.add_argument("--json")
    c.set_defaults(func=cmd_compare)

    t = sub.add_parser("train", help="Fine-tune a model on the live/spoof split.")
    t.add_argument("--model", required=True)
    t.add_argument("--labels", required=True)
    t.add_argument("--data-root", required=True)
    t.add_argument("--epochs", type=int, default=3)
    t.add_argument("--batch-size", type=int, default=64)
    t.add_argument("--lr", type=float, default=1e-4)
    t.add_argument("--limit", type=int, help="Cap training images (for quick runs).")
    t.add_argument("--device")
    t.add_argument("--out", default="weights")
    t.add_argument("--out-name", help="Override the weights filename stem (default: model name).")
    t.add_argument("--multitask", action="store_true",
                   help="AENet only: add semantic auxiliary supervision (AENet_C,S).")
    t.add_argument("--lambda-attack", type=float, default=0.5, help="Weight for the spoof-type loss.")
    t.add_argument("--lambda-light", type=float, default=0.25, help="Weight for the illumination loss.")
    t.add_argument("--lambda-attr", type=float, default=0.1, help="Weight for the 40-attribute BCE loss.")
    t.set_defaults(func=cmd_train)

    b = sub.add_parser("benchmark", help="Train several models on a local dataset and evaluate all.")
    b.add_argument("--data-root", required=True)
    b.add_argument("--train-labels", required=True, help="Training label JSON.")
    b.add_argument("--test-labels", required=True, help="Test label JSON for evaluation.")
    b.add_argument("--models", default="efficientnet,vit,deeppixbis,cdcn,aenet",
                   help="Comma-separated models to include.")
    b.add_argument("--pretrained", nargs="*",
                   help="Models to evaluate without training, as name=weights_path "
                        "(e.g. aenet=weights/ckpt_iter.pth.tar).")
    b.add_argument("--n-train", type=int, default=10000, help="Balanced training images (0/None = all).")
    b.add_argument("--n-test", type=int, default=4000, help="Balanced test images for eval.")
    b.add_argument("--epochs", type=int, default=3)
    b.add_argument("--batch-size", type=int, default=64)
    b.add_argument("--lr", type=float, default=1e-4)
    b.add_argument("--device", help="cpu | cuda | cuda:0 ... (auto-detected if omitted).")
    b.add_argument("--out", default="runs", help="Output dir for weights + results.json.")
    b.set_defaults(func=cmd_benchmark)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
