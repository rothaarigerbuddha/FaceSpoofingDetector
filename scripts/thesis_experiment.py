"""Thesis experiment: a fair, reproducible comparison of three face anti-spoofing
models on CelebA-Spoof (intra_test protocol), plus inference-speed measurements.

What it does, end to end:

  1. Picks ONE balanced subset of the train split and ONE balanced subset of the
     test split (fixed seed) and reuses them for every model -> fair comparison.
  2. Trains AENet, EfficientNet-B0 and DeepPixBiS *identically* (same subset, same
     epochs / batch size / learning rate). All three start from ImageNet-pretrained
     backbones (AENet's ResNet-18 trunk is ImageNet warm-started in detectors/aenet.py),
     so none has a data or initialisation advantage.
  3. Evaluates each trained model on the test subset and reports, per ISO/IEC
     30107-3, APCER / BPCER / ACER **at the EER threshold**, plus AUC and EER.
  4. Measures inference speed on the GPU with warm-up + CUDA synchronisation:
       - latency   = mean ms per image at batch=1
       - throughput = images/s (FPS) at batch=32
     for the three trained models AND, for context only, ViT-B/16 and CDCN
     (speed is an architectural property of the weights' *shapes*, so these two
     are measured untrained -- accuracy columns are left blank for them).
  5. Prints one summary table and writes it to CSV.

Why pretrained AENet was not used: this repo ships no CelebA-Spoof AENet checkpoint
(ckpt_iter.pth.tar). A randomly-initialised AENet scores at chance (~0.56 AUC), which
is exactly what `fsd compare` showed. Even the official checkpoint would be unfair
here -- it was trained on the *full* dataset, not this subset -- so for an honest
comparison we train AENet on the same data as the others and say so in the output.

Run:
    python scripts/thesis_experiment.py \
        --data-root ~/datasets/celeba-spoof/CelebA_Spoof_/CelebA_Spoof \
        --out runs/thesis

Everything is parameterised below; defaults match the thesis hardware (RTX 4060, 8 GB).
"""

from __future__ import annotations

import argparse
import csv
import os
import random
import sys
import time
from pathlib import Path

import numpy as np

# Make `fsd` importable when run as a plain script from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import torch  # noqa: E402

from fsd.dataset.celeba_spoof import load_labels  # noqa: E402
from fsd.detectors.registry import build_detector  # noqa: E402
from fsd.eval.compare import sample_entries, score_detector  # noqa: E402
from fsd.eval.metrics import apcer_bpcer_acer, auc_score, eer_score  # noqa: E402
from fsd.train import _MODEL_PREPROC, train_model  # noqa: E402
from fsd.train_multitask import DEFAULT_LAMBDAS, train_aenet_multitask  # noqa: E402

# Models we actually train + evaluate for accuracy (the thesis comparison).
#   aenet     -> binary live/spoof supervision only
#   aenet_mt  -> SAME AENet, but multi-task semantic supervision (AENet_C,S)
#   efficientnet / deeppixbis -> binary only (generic CNNs, the contrast)
TRAINED_MODELS = ["aenet", "aenet_mt", "efficientnet", "deeppixbis"]
# Extra models measured for inference latency only (no training, untrained weights).
LATENCY_ONLY_MODELS = ["vit", "cdcn"]


def arch_of(name: str) -> str:
    """Map a training config name to the registry architecture used for eval/latency.

    ``aenet_mt`` is a *training recipe*, not a new architecture: at inference it is a
    plain AENet scored through fc_live, identical to the binary ``aenet``.
    """
    return "aenet" if name == "aenet_mt" else name


# --------------------------------------------------------------------------- #
# Reproducibility
# --------------------------------------------------------------------------- #
def set_seed(seed: int) -> None:
    """Fix every RNG we touch so the run is reproducible (subset choice + init)."""
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


# --------------------------------------------------------------------------- #
# Accuracy evaluation
# --------------------------------------------------------------------------- #
def evaluate_accuracy(model_name, weights, entries, data_root, *, batch_size, device):
    """Score one trained model on the shared test subset and return ISO metrics.

    APCER/BPCER/ACER are reported at the EER operating point (the threshold where
    false-accept rate == false-reject rate) -- the standard single-number operating
    point for face anti-spoofing, and one we can justify on defence.
    """
    detector = build_detector(arch_of(model_name), weights=weights, device=device)
    scores, labels = score_detector(detector, entries, data_root, batch_size=batch_size)

    auc = auc_score(scores, labels)
    eer, eer_threshold = eer_score(scores, labels)
    apcer, bpcer, acer = apcer_bpcer_acer(scores, labels, threshold=eer_threshold)
    return {
        "auc": auc,
        "eer": eer,
        "eer_threshold": eer_threshold,
        "apcer": apcer,
        "bpcer": bpcer,
        "acer": acer,
        "n_test": int(len(labels)),
    }


# --------------------------------------------------------------------------- #
# Inference-speed measurement
# --------------------------------------------------------------------------- #
@torch.no_grad()
def measure_speed(model_name, weights, *, device, warmup=15, iters_b1=80, iters_b32=40):
    """Measure pure forward-pass latency (batch=1) and throughput (batch=32) on GPU.

    We time the model forward on random input tensors of the correct size -- this
    isolates the *architecture's* compute cost from disk I/O and CPU preprocessing,
    and is why ViT/CDCN can be timed without trained weights. CUDA work is async, so
    we synchronise before/after every timed region; a warm-up absorbs cuDNN autotune
    and lazy CUDA-context/allocator costs so the first kernels don't skew the mean.
    """
    arch = arch_of(model_name)
    detector = build_detector(arch, weights=weights, device=device)
    model = detector.model.eval()
    dev = detector.device
    size = _MODEL_PREPROC.get(arch, (224, True))[0]  # 256 for CDCN, else 224
    is_cuda = dev.type == "cuda"

    def sync():
        if is_cuda:
            torch.cuda.synchronize(dev)

    def run(x, n):
        sync()
        t0 = time.perf_counter()
        for _ in range(n):
            out = model(x)
            if isinstance(out, (tuple, list)):  # some heads return (logits, map)
                out = out[0]
        sync()
        return time.perf_counter() - t0

    # --- batch = 1 : per-image latency ---
    x1 = torch.randn(1, 3, size, size, device=dev)
    run(x1, warmup)                       # warm-up (not timed)
    latency_ms = run(x1, iters_b1) / iters_b1 * 1000.0

    # --- batch = 32 : throughput / FPS ---
    x32 = torch.randn(32, 3, size, size, device=dev)
    run(x32, max(3, warmup // 3))         # warm-up
    fps = (32 * iters_b32) / run(x32, iters_b32)

    n_params = sum(p.numel() for p in model.parameters()) / 1e6  # millions
    return {"latency_ms_b1": latency_ms, "fps_b32": fps, "params_m": n_params, "input": size}


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #
def print_table(rows):
    head = (f"{'model':<14}{'trained':>8}{'APCER':>9}{'BPCER':>9}{'ACER':>9}"
            f"{'AUC':>9}{'EER':>9}{'lat_ms@1':>10}{'FPS@32':>9}{'params_M':>10}")
    print("\n" + head)
    print("-" * len(head))

    def f(v, w, p=4):
        return f"{v:>{w}.{p}f}" if isinstance(v, (int, float)) else f"{'-':>{w}}"

    for r in rows:
        print(f"{r['model']:<14}{('yes' if r['trained'] else 'no'):>8}"
              f"{f(r.get('apcer'), 9)}{f(r.get('bpcer'), 9)}{f(r.get('acer'), 9)}"
              f"{f(r.get('auc'), 9)}{f(r.get('eer'), 9)}"
              f"{f(r.get('latency_ms_b1'), 10, 3)}{f(r.get('fps_b32'), 9, 1)}"
              f"{f(r.get('params_m'), 10, 2)}")
    print()


def write_csv(rows, path):
    cols = ["model", "trained", "n_test", "apcer", "bpcer", "acer", "auc", "eer",
            "eer_threshold", "latency_ms_b1", "fps_b32", "params_m", "input"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})
    print(f"Wrote {path}")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-root", required=True, help="CelebA-Spoof root (holds Data/ and metas/).")
    ap.add_argument("--train-labels", help="Defaults to <root>/metas/intra_test/train_label.json")
    ap.add_argument("--test-labels", help="Defaults to <root>/metas/intra_test/test_label.json")
    ap.add_argument("--n-train", type=int, default=40000, help="Balanced training images.")
    ap.add_argument("--n-test", type=int, default=4000, help="Balanced test images for evaluation.")
    ap.add_argument("--epochs", type=int, default=6)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--device", default=None, help="cuda | cpu (auto if omitted).")
    ap.add_argument("--out", default="runs/thesis_mt", help="Output dir for weights + CSV.")
    ap.add_argument("--skip-train", action="store_true",
                    help="Reuse <out>/<model>.pth instead of training (faster re-runs).")
    args = ap.parse_args()

    root = Path(args.data_root).expanduser()
    train_labels = args.train_labels or str(root / "metas/intra_test/train_label.json")
    test_labels = args.test_labels or str(root / "metas/intra_test/test_label.json")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")

    set_seed(args.seed)
    print("=" * 78)
    print("THESIS EXPERIMENT - CelebA-Spoof anti-spoofing comparison (intra_test)")
    print("=" * 78)
    print(f"device={device}  seed={args.seed}  n_train={args.n_train}  n_test={args.n_test}")
    print(f"epochs={args.epochs}  batch_size={args.batch_size}  lr={args.lr}")
    print("NOTE: AENet has no shipped CelebA-Spoof checkpoint -> it is TRAINED here on")
    print("      the same subset as the others (ImageNet-warm-started trunk) for a")
    print("      fair comparison. APCER/BPCER/ACER are reported at the EER threshold.")
    print("MULTI-TASK: 'aenet_mt' = AENet_C,S, the SAME AENet trained with extra")
    print("      semantic supervision (spoof-type + illumination + 40 face attributes);")
    print(f"      aux loss weights {DEFAULT_LAMBDAS}. 'aenet' is the binary baseline.")
    print("      Both share the identical training subset & budget -> the only")
    print("      difference is supervision (the thesis variable). Evaluation is binary")
    print("      (fc_live) for every model. Geometry maps (variant G) are NOT used.")
    print("=" * 78)

    # The shared, balanced test subset -- identical for every model (fixed seed).
    test_entries = sample_entries(load_labels(test_labels), limit=args.n_test, seed=args.seed)
    print(f"Test subset: {len(test_entries)} images "
          f"(live={sum(1 for e in test_entries if not e.is_spoof)}, "
          f"spoof={sum(1 for e in test_entries if e.is_spoof)})")

    rows = []

    # ---- 1) train + evaluate the three comparison models ----
    for name in TRAINED_MODELS:
        print(f"\n{'#' * 70}\n# {name.upper()}\n{'#' * 70}")
        weights_path = out / f"{name}.pth"

        if args.skip_train and weights_path.exists():
            print(f"[train] skipped, using {weights_path}")
        else:
            bs = args.batch_size
            while True:
                try:
                    if name == "aenet_mt":
                        # AENet with masked multi-task semantic supervision (AENet_C,S).
                        saved = train_aenet_multitask(
                            labels=train_labels, data_root=str(root),
                            epochs=args.epochs, batch_size=bs, lr=args.lr,
                            limit=args.n_train, device=device, out_dir=str(out),
                        )
                    else:
                        # Generic binary live/spoof fine-tune (unchanged path).
                        saved = train_model(
                            model_name=name, labels=train_labels, data_root=str(root),
                            epochs=args.epochs, batch_size=bs, lr=args.lr,
                            limit=args.n_train, device=device, out_dir=str(out),
                        )
                    # both save as <out>/<name>.pth -> matches weights_path
                    print(f"[train] saved {saved}")
                    break
                except RuntimeError as ex:
                    # 8 GB VRAM safety net: halve the batch and retry once on OOM.
                    if "out of memory" in str(ex).lower() and bs > 8:
                        torch.cuda.empty_cache()
                        bs //= 2
                        print(f"[train] CUDA OOM -> retrying at batch_size={bs}")
                        continue
                    raise

        metrics = evaluate_accuracy(name, str(weights_path), test_entries, root,
                                    batch_size=args.batch_size, device=device)
        speed = measure_speed(name, str(weights_path), device=device)
        print(f"[eval] AUC={metrics['auc']:.4f} EER={metrics['eer']:.4f} "
              f"ACER={metrics['acer']:.4f} (thr={metrics['eer_threshold']:.4f}) "
              f"| {speed['latency_ms_b1']:.3f} ms/img, {speed['fps_b32']:.1f} FPS")
        rows.append({"model": name, "trained": True, **metrics, **speed})

    # ---- 2) latency-only context models (ViT-B/16, CDCN) ----
    for name in LATENCY_ONLY_MODELS:
        print(f"\n{'#' * 70}\n# {name.upper()} (latency only)\n{'#' * 70}")
        speed = measure_speed(name, None, device=device)
        print(f"[speed] {speed['latency_ms_b1']:.3f} ms/img, {speed['fps_b32']:.1f} FPS, "
              f"{speed['params_m']:.2f}M params")
        rows.append({"model": name, "trained": False, **speed})

    # ---- 3) report ----
    print_table(rows)
    write_csv(rows, out / "results.csv")
    print_aenet_ablation(rows)
    print("\nAuxiliary tasks trained on AENet_C,S (semantic variant; geometry omitted):")
    print(f"  L_attack_type  CE over spoof type (11 cls)   weight {DEFAULT_LAMBDAS['attack_type']}")
    print(f"  L_illumination CE over illumination (5 cls)  weight {DEFAULT_LAMBDAS['illumination']}")
    print(f"  L_attributes   BCE over 40 face attrs        weight {DEFAULT_LAMBDAS['attributes']}"
          "  (masked to LIVE images)")
    print("  L_live         CE over live/spoof (2 cls)     weight 1.0  (main task)")
    print("Done.")
    return 0


def print_aenet_ablation(rows):
    """Side-by-side: does multi-task semantic supervision help AENet (same budget)?"""
    by = {r["model"]: r for r in rows}
    base, mt = by.get("aenet"), by.get("aenet_mt")
    if not (base and mt and "acer" in base and "acer" in mt):
        return
    print("\n" + "=" * 64)
    print("ABLATION  -  AENet binary  vs  AENet_C,S multi-task (identical budget)")
    print("=" * 64)
    h = f"{'metric':<10}{'binary':>12}{'multi-task':>12}{'Δ (mt-bin)':>14}"
    print(h)
    print("-" * len(h))
    # APCER/BPCER/ACER/EER: lower is better; AUC: higher is better.
    for key, label in [("acer", "ACER"), ("apcer", "APCER"), ("bpcer", "BPCER"),
                       ("eer", "EER"), ("auc", "AUC")]:
        b, m = base[key], mt[key]
        better = (m > b) if key == "auc" else (m < b)
        mark = "  better" if better else ("  worse" if m != b else "  same")
        print(f"{label:<10}{b:>12.4f}{m:>12.4f}{m - b:>+14.4f}{mark}")
    print("\nLower is better for ACER/APCER/BPCER/EER; higher is better for AUC.")
    print("Interpretation: this delta is the *direct* contribution of CelebA-Spoof's")
    print("auxiliary semantic information to presentation-attack robustness.")


if __name__ == "__main__":
    raise SystemExit(main())
