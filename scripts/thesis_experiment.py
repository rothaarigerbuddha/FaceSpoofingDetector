"""Thesis experiment: does semantic auxiliary supervision make AENet more robust?

Hypothesis under test
---------------------
"Auxiliary information improves robustness to presentation attacks." We test it
honestly by giving ONLY AENet its architectural advantage -- multi-task semantic
supervision (AENet_C,S) -- while EfficientNet-B0 and DeepPixBiS stay plain binary
classifiers. All models share one budget, seed and test subset; the only thing
that changes for AENet is whether the auxiliary heads are supervised.

What it trains (same budget for every trained model: --n-train / --epochs)
    efficientnet     binary live/spoof          (general CNN control)
    deeppixbis       binary live/spoof          (general CNN control)
    aenet_binary     binary live/spoof          (AENet ablation control)
    aenet_multitask  L_live + λ_a·L_attack + λ_l·L_light + λ_t·L_attr   (AENet_C,S)

Reference (not trained here)
    aenet_pretrained official ckpt_iter.pth.tar via --aenet-ckpt (the prior
                     binary AENet result, ACER ~= 0.075) -- kept so the table can
                     show "AENet binary vs AENet multi-task".

Evaluation is identical for everyone: scoring uses ONLY fc_live, and
APCER/BPCER/ACER@EER, AUC, EER, latency and FPS are computed the same way.
ViT and CDCN are reported for latency only (no accuracy), per the brief.

Geometry ("G": depth / reflection maps) is intentionally NOT implemented --
CelebA-Spoof ships no such maps, so this is strictly the semantic variant.

Run (full, on a GPU box with the dataset on disk):

    python scripts/thesis_experiment.py \
        --data-root /data/celeba-spoof \
        --train-labels /data/celeba-spoof/metas/intra_test/train_label.json \
        --test-labels  /data/celeba-spoof/metas/intra_test/test_label.json \
        --aenet-ckpt weights/ckpt_iter.pth.tar \
        --n-train 40000 --n-test 4000 --epochs 6 --device cuda --out runs/thesis

Smoke (CPU, synthetic mini-dataset, no real data needed):

    python scripts/thesis_experiment.py --smoke --out runs/smoke
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

SEED = 0
BATCH = 64
LR = 1e-4

# Auxiliary loss weights for AENet_C,S (main task L_live is fixed at 1.0).
LAMBDA_ATTACK = 0.5   # spoof-type CE  -- most spoofing-relevant semantic
LAMBDA_LIGHT = 0.25   # illumination CE
LAMBDA_ATTR = 0.10    # 40-attribute BCE (kept small so the high-dim term can't dominate)

# Models reported for latency only (built untrained, no accuracy).
LATENCY_ONLY = ("vit", "cdcn")


# --------------------------------------------------------------------------- #
# synthetic mini-dataset for --smoke (lets the whole pipeline run on CPU)
# --------------------------------------------------------------------------- #
def make_smoke_dataset(root: Path, n: int = 64) -> tuple[str, str]:
    """Write a tiny synthetic CelebA-Spoof-shaped dataset and return label paths."""
    import random

    import numpy as np
    from PIL import Image

    rng = random.Random(SEED)
    (root / "Data" / "live").mkdir(parents=True, exist_ok=True)
    (root / "Data" / "spoof").mkdir(parents=True, exist_ok=True)
    labels: dict[str, list[int]] = {}
    for i in range(n):
        is_spoof = i % 2
        rel = f"Data/{'spoof' if is_spoof else 'live'}/{i}.png"
        arr = np.random.default_rng(i).integers(0, 256, (96, 96, 3), dtype="uint8")
        Image.fromarray(arr).save(root / rel)
        vec = [0] * 44
        if is_spoof:
            vec[40] = rng.randint(1, 10)   # spoof type 1..10
            vec[41] = rng.randint(1, 4)    # illumination 1..4
            vec[42] = rng.randint(1, 2)    # environment 1..2
            vec[43] = 1
        else:
            vec[:40] = [rng.randint(0, 1) for _ in range(40)]  # attributes (live only)
            vec[43] = 0
        labels[rel] = vec
    train_p = root / "train_label.json"
    test_p = root / "test_label.json"
    train_p.write_text(json.dumps(labels), encoding="utf-8")
    test_p.write_text(json.dumps(labels), encoding="utf-8")
    return str(train_p), str(test_p)


# --------------------------------------------------------------------------- #
# experiment
# --------------------------------------------------------------------------- #
def run(args: argparse.Namespace) -> dict:
    import torch

    from fsd.dataset.celeba_spoof import load_labels
    from fsd.detectors.registry import build_detector
    from fsd.eval.compare import sample_entries, score_detector
    from fsd.eval.latency import measure_latency
    from fsd.eval.metrics import evaluate
    from fsd.multitask import AuxWeights
    from fsd.train import train_model

    torch.manual_seed(SEED)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    aux = AuxWeights(attack=args.lambda_attack, light=args.lambda_light, attribute=args.lambda_attr)

    common = dict(
        labels=args.train_labels, data_root=args.data_root, epochs=args.epochs,
        batch_size=args.batch_size, lr=args.lr, limit=args.n_train,
        device=args.device, out_dir=str(out),
    )

    binary_models = [m.strip() for m in args.binary_models.split(",") if m.strip()]
    weights: dict[str, str] = {}
    # 1) General-CNN controls: plain binary.
    for name in binary_models:
        print(f"\n=== train {name} (binary) ===")
        weights[name] = train_model(model_name=name, **common)
    # 2) AENet ablation: binary vs multi-task on the SAME budget.
    print("\n=== train aenet_binary (binary control) ===")
    weights["aenet_binary"] = train_model(model_name="aenet", out_name="aenet_binary", **common)
    print("\n=== train aenet_multitask (AENet_C,S) ===")
    weights["aenet_multitask"] = train_model(
        model_name="aenet", out_name="aenet_multitask", multitask=True, aux_weights=aux, **common
    )

    # Evaluation specs: (display name, builder arch, weights). Pretrained AENet is
    # added only when its checkpoint is supplied.
    specs = [(m, m, weights[m]) for m in binary_models]
    specs += [
        ("aenet_binary", "aenet", weights["aenet_binary"]),
        ("aenet_multitask", "aenet", weights["aenet_multitask"]),
    ]
    if args.aenet_ckpt:
        specs.append(("aenet_pretrained", "aenet", args.aenet_ckpt))

    test_entries = sample_entries(load_labels(args.test_labels), limit=args.n_test, seed=SEED + 1)
    print(f"\n[eval] {len(test_entries)} test images (seed {SEED + 1})")

    preproc = {"aenet": 224, "deeppixbis": 224, "efficientnet": 224, "vit": 224, "cdcn": 256}
    results: dict[str, dict] = {}
    for name, arch, w in specs:
        det = build_detector(arch, weights=w, device=args.device)
        scores, labels = score_detector(det, test_entries, args.data_root, batch_size=args.batch_size)
        metric = evaluate(scores, labels, threshold=args.threshold).to_dict()
        metric["latency"] = measure_latency(det, input_size=preproc.get(arch, 224))
        results[name] = metric
        print(f"  {name:<16} ACER={metric['acer']:.4f} AUC={metric['auc']:.4f} "
              f"EER={metric['eer']:.4f} {metric['latency']['latency_ms']:.2f}ms")

    # Latency-only models (no accuracy), built untrained.
    latency_only: dict[str, dict] = {}
    for name in LATENCY_ONLY:
        try:
            det = build_detector(name, weights=None, device=args.device)
            latency_only[name] = measure_latency(det, input_size=preproc.get(name, 224))
            print(f"  {name:<16} (latency only) {latency_only[name]['latency_ms']:.2f}ms")
        except Exception as e:  # keep going if a backbone download is unavailable
            print(f"  {name:<16} latency skipped: {e}")

    payload = {
        "config": {
            "variant": "AENet_C,S (semantic only; geometry 'G' intentionally omitted)",
            "seed": SEED, "n_train": args.n_train, "n_test": len(test_entries),
            "epochs": args.epochs, "batch_size": args.batch_size, "lr": args.lr,
            "aux_weights": aux.as_dict(), "threshold": args.threshold,
            "device": args.device or "auto",
        },
        "weights": weights,
        "results": results,
        "latency_only": latency_only,
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    (out / "results.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\n[done] wrote {out / 'results.json'}")
    print_report(payload)
    return payload


def print_report(payload: dict) -> None:
    cfg = payload["config"]
    res = payload["results"]
    print("\n" + "=" * 78)
    print(f"THESIS RESULTS  |  variant: {cfg['variant']}")
    print(f"budget: n_train={cfg['n_train']} epochs={cfg['epochs']} seed={cfg['seed']} "
          f"n_test={cfg['n_test']}  aux_weights={cfg['aux_weights']}")
    print("=" * 78)
    header = (f"{'model':<18}{'APCER':>8}{'BPCER':>8}{'ACER':>8}{'AUC':>8}"
              f"{'EER':>8}{'lat_ms':>9}{'FPS':>9}")
    print(header)
    print("-" * len(header))
    for name, r in res.items():
        lat = r["latency"]
        print(f"{name:<18}{r['apcer']:>8.4f}{r['bpcer']:>8.4f}{r['acer']:>8.4f}"
              f"{r['auc']:>8.4f}{r['eer']:>8.4f}{lat['latency_ms']:>9.2f}{lat['fps']:>9.1f}")
    for name, lat in payload["latency_only"].items():
        print(f"{name + ' (lat only)':<18}{'-':>8}{'-':>8}{'-':>8}{'-':>8}{'-':>8}"
              f"{lat['latency_ms']:>9.2f}{lat['fps']:>9.1f}")

    if "aenet_binary" in res and "aenet_multitask" in res:
        b, m = res["aenet_binary"], res["aenet_multitask"]
        print("\nKey comparison -- AENet binary vs multi-task (same budget, same seed):")
        print(f"  {'metric':<10}{'binary':>12}{'multitask':>12}{'Δ (mt-bin)':>14}")
        for k in ("acer", "eer", "auc"):
            print(f"  {k:<10}{b[k]:>12.4f}{m[k]:>12.4f}{m[k] - b[k]:>+14.4f}")
        better = m["acer"] < b["acer"]
        verdict = ("multi-task LOWERS ACER -> auxiliary supervision helped"
                   if better else
                   "multi-task did NOT lower ACER -> no robustness gain on this budget (reported honestly)")
        print(f"  => {verdict}")
    if "aenet_pretrained" in res:
        print(f"  reference: official pretrained AENet ACER={res['aenet_pretrained']['acer']:.4f}")

    print("\nAuxiliary tasks & loss weights:")
    print("  L = L_live + λ_attack·L_attack + λ_light·L_light + λ_attr·L_attr")
    for k, v in cfg["aux_weights"].items():
        kind = {"live": "CE 2-way (MAIN)", "attack": "CE 11-way spoof-type",
                "light": "CE 5-way illumination", "attribute": "BCE 40 face attributes (live-masked)"}[k]
        print(f"    {k:<10} weight={v:<5} {kind}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data-root")
    p.add_argument("--train-labels")
    p.add_argument("--test-labels")
    p.add_argument("--aenet-ckpt", help="Official ckpt_iter.pth.tar for the pretrained-AENet reference row.")
    p.add_argument("--n-train", type=int, default=40000)
    p.add_argument("--n-test", type=int, default=4000)
    p.add_argument("--epochs", type=int, default=6)
    p.add_argument("--batch-size", type=int, default=BATCH)
    p.add_argument("--lr", type=float, default=LR)
    p.add_argument("--threshold", type=float, default=0.5)
    p.add_argument("--lambda-attack", type=float, default=LAMBDA_ATTACK)
    p.add_argument("--lambda-light", type=float, default=LAMBDA_LIGHT)
    p.add_argument("--lambda-attr", type=float, default=LAMBDA_ATTR)
    p.add_argument("--device")
    p.add_argument("--out", default="runs/thesis")
    p.add_argument("--binary-models", default="efficientnet,deeppixbis",
                   help="General-CNN controls trained binary (comma-separated).")
    p.add_argument("--smoke", action="store_true",
                   help="CPU dry-run on a synthetic mini-dataset (overrides data paths + shrinks budget).")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.smoke:
        smoke_root = Path(args.out) / "_smoke_data"
        args.train_labels, args.test_labels = make_smoke_dataset(smoke_root)
        args.data_root = str(smoke_root)
        args.n_train, args.n_test, args.epochs = 48, 24, 2
        args.batch_size, args.device = 16, "cpu"
        args.aenet_ckpt = None
        # AENet is defined locally (no pretrained download); external backbones
        # (efficientnet/deeppixbis/vit/cdcn) need network weights, so the smoke
        # run exercises only the AENet binary-vs-multitask path.
        args.binary_models = ""
        print("[smoke] synthetic mini-dataset, CPU, tiny budget -- AENet plumbing check only")
    else:
        missing = [k for k in ("data_root", "train_labels", "test_labels") if not getattr(args, k)]
        if missing:
            raise SystemExit(f"missing required args for a real run: {missing} (or use --smoke)")
    run(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
