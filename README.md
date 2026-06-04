# FaceSpoofingDetector

A tool to **analyze the [CelebA-Spoof](https://github.com/ZhangYuanhan-AI/CelebA-Spoof) dataset** and **detect face-spoofing images**, comparing five face anti-spoofing (FAS) models on the same split.

CelebA-Spoof is a large-scale **single-frame RGB** face anti-spoofing dataset (625,537 images, 10,177 subjects). Each image has a sibling `*_BB.txt` face bounding box, and labels live in a JSON file mapping each image to a 44-value vector (index `[43]` is live/spoof).

## Why these five models

All five suit single-image RGB presentation-attack detection and span the design space:

| Model | Approach | Notes |
|-------|----------|-------|
| **AENet** | ResNet-18 multi-task (semantic + depth/reflection aux) | Official CelebA-Spoof baseline; the **only one with released weights** |
| **CDCN** | Central-difference convolutions, depth-supervised | Captures fine print/replay micro-texture |
| **DeepPixBiS** | DenseNet + pixel-wise binary supervision | Lightweight, dense supervision |
| **EfficientNet-B0** | ImageNet transfer → binary head | Strong pragmatic baseline |
| **ViT-B/16** | Vision Transformer fine-tuned | Global self-attention cues |

Each model exposes a uniform 2-logit live/spoof head for scoring; CDCN/DeepPixBiS keep their characteristic map heads for auxiliary supervision during training.

## Install

> **Python 3.10–3.12** for the deep-learning models — PyTorch has no 3.14 wheels yet.

```bash
python -m venv .venv && .venv\Scripts\activate     # Windows
pip install -e .            # core (analysis + CLI), torch-free
pip install -e ".[torch]"   # + torch/timm for detect/compare/train
# install torch matching your CUDA from https://pytorch.org
```

## Get the dataset

Download the Kaggle mirror `attentionlayer241/celeba-spoof-for-face-antispoofing` to `D:\projects\celeba-spoof`:

- **Preferred:** via the Kaggle MCP server (configured in the client; authenticate with `/mcp`).
- **Fallback:** `python scripts/download_dataset.py` (needs the `kaggle` CLI + API token).

## Usage

```bash
# Dataset statistics + on-disk integrity (no torch needed)
fsd analyze --labels D:\projects\celeba-spoof\metas\intra_test\test_label.json \
            --data-root D:\projects\celeba-spoof --check-files

# List models
fsd models

# Score one image
fsd detect --model aenet --weights weights\ckpt_iter.pth.tar --image path\to\face.png

# Fine-tune a model on the live/spoof split
fsd train --model efficientnet --labels ...\train_label.json \
          --data-root D:\projects\celeba-spoof --epochs 3 --limit 20000

# Compare several models on a labelled split
fsd compare --labels ...\test_label.json --data-root D:\projects\celeba-spoof \
            --models aenet,efficientnet,vit \
            --weights aenet=weights\ckpt_iter.pth.tar efficientnet=weights\efficientnet.pth \
            --limit 5000
```

Metrics reported: **AUC, EER, APCER/BPCER/ACER, and TPR@FPR** (the dataset's headline metric).

> **Note:** none of the five models ship with CelebA-Spoof weights here. AENet's
> official `ckpt_iter.pth.tar` is not bundled; if you do not pass one, AENet's
> ResNet-18 trunk is **ImageNet warm-started** (see `detectors/aenet.py`) so that
> training it from scratch is fair against EfficientNet/DeepPixBiS/ViT, which also
> start from ImageNet backbones. Train any model with `fsd train`/`fsd benchmark`
> (or the thesis script below) before the comparison numbers are meaningful.

## Reproducible thesis comparison (`scripts/thesis_experiment.py`)

One self-contained, fixed-seed script that trains **AENet, EfficientNet-B0,
DeepPixBiS, MobileNetV3-Large, ResNet-50 and ViT-B/16 identically** on one balanced
CelebA-Spoof subset (intra_test), evaluates them, and measures inference speed —
the experiment used in the thesis:

```bash
python scripts/thesis_experiment.py \
  --data-root ~/datasets/celeba-spoof/CelebA_Spoof_/CelebA_Spoof \
  --n-train 40000 --n-test 4000 --epochs 6 --batch-size 32 --seed 42 \
  --out runs/thesis_full
```

It reports, per ISO/IEC 30107-3, **APCER / BPCER / ACER at the EER threshold**, plus
**AUC** and **EER**, and the **inference latency** (ms/image at batch 1) and
**throughput** (FPS at batch 32) measured on the GPU with warm-up + CUDA
synchronisation. Output: one summary table on stdout + `runs/<out>/results.csv`.

Practical knobs:

* **Per-model batch size** — ViT-B/16 trains at batch 16 (8 GB VRAM); the rest at
  `--batch-size`. Any model OOMs auto-fall back to a smaller batch.
* **Per-model resume** — a model whose `<out>/<name>.pth` already exists is reused,
  not retrained. Seed `<out>` with weights from an earlier identical-subset/seed run
  and only the new models train. `--force-retrain a,b` (or `all`) overrides; `--models
  a,b` runs a subset (used for the low-data ablation below).
* **CDCN is latency-only** — its canonical training is *depth-supervised* (it regresses
  a pseudo-depth map) and CelebA-Spoof ships no depth ground truth, so training it as a
  plain binary classifier would misrepresent the architecture. We report only its
  architectural latency, for context.

### Multi-task AENet (`aenet_mt`) — does auxiliary supervision help?

The script also trains **`aenet_mt`**: the *same* AENet, on the *same* subset and
budget, but with CelebA-Spoof's semantic auxiliary labels (the **AENet_C,S** variant):

```
L = L_live + 0.5·L_attack_type + 0.5·L_illumination + 0.1·L_attributes
```

CrossEntropy for live/spoof, spoof-type (11 cls) and illumination (5 cls); BCE for
the 40 binary face attributes. **Masking** (verified on the data): spoof-type and
illumination are defined for every image (bona-fide = explicit class 0), so their
losses run on the full batch; the 40 attributes are annotated only on live images
(all-zero placeholder on spoof), so `L_attributes` is **masked to live images**.
EfficientNet-B0 and DeepPixBiS stay binary on purpose — the contrast (specialised
architecture exploiting side information vs. generic CNNs) is the experiment.
Inference is identical for every model (the `fc_live` head). The geometry variant
(depth/reflection maps, “G”) is **not** implemented — CelebA-Spoof ships no such
ground truth. The script prints an `aenet` vs `aenet_mt` ablation so the contribution
of the auxiliary information is read off directly.

The same ablation at a smaller budget (`--models aenet,aenet_mt --n-train 5000`) is
the low-data control:

```bash
python scripts/thesis_experiment.py --data-root <root> \
  --models aenet,aenet_mt --n-train 5000 --n-test 4000 --epochs 6 \
  --seed 42 --out runs/thesis_lowdata
```

> **Finding — it depends on the data budget (AENet binary vs AENet_C,S, ACER@EER):**
>
> | Train images | binary | multi-task | verdict |
> |---|---|---|---|
> | 40 000 | **0.028** | 0.051 | aux **hurts** (~3.7σ) — saturated |
> | 5 000  | 0.094 | **0.051** | aux **helps** (~5.2σ) |
>
> The auxiliary heads train normally and training is stable, so both directions are
> genuine. The telling detail: **`aenet_mt` is almost flat across the 8× data cut**
> (0.0505 → 0.0510), while **binary AENet collapses** (0.028 → 0.094). The semantic
> auxiliary tasks act as a regulariser that compensates for data scarcity: they pay
> off when labels are few, but on a saturated *intra-domain* split the binary signal
> already suffices and the extra objectives mainly compete for capacity. Cross-domain
> evaluation is the natural next test.

## Train on another machine (local GPU)

Two portable ways to train on a local copy of the dataset — ideal for moving to a GPU box:

**A. One command — train several models + evaluate all (`fsd benchmark`).** The local equivalent of the Kaggle notebook:

```bash
# On the GPU machine, with the dataset at /data/celeba-spoof:
pip install -e ".[torch]"     # + a CUDA torch build from https://pytorch.org

fsd benchmark \
  --data-root /data/celeba-spoof \
  --train-labels /data/celeba-spoof/metas/intra_test/train_label.json \
  --test-labels  /data/celeba-spoof/metas/intra_test/test_label.json \
  --models efficientnet,vit,deeppixbis,cdcn,aenet \
  --pretrained aenet=weights/ckpt_iter.pth.tar \
  --n-train 10000 --n-test 4000 --epochs 3 \
  --device cuda --out runs/exp1
```

Trains every `--models` entry not listed in `--pretrained`, evaluates all of them on the test split, and writes `runs/exp1/<model>.pth` + `runs/exp1/results.json`. `--device` auto-detects CUDA if omitted; `--n-train 0` uses the full set.

**B. Cloud GPU — Kaggle notebook (`scripts/kaggle_train.py`).** Self-contained (only needs torch/timm/opencv, no install); runs on Kaggle's free GPU with the dataset mounted and writes `weights/*.pth` + `results.json` to the notebook output. Edit the `N_TRAIN/EPOCHS` constants at the top to taste.

Both produce the same `results.json` schema, so weights are interchangeable with `fsd compare`/`fsd detect`.

## Layout

```
src/fsd/
  dataset/celeba_spoof.py   # label schema, parsing, stats, integrity
  utils/image.py            # BB face-crop (matches official client.py)
  detectors/                # base + registry + aenet/cdcn/deeppixbis/efficientnet/vit
  eval/metrics.py           # TPR@FPR, AUC, EER, APCER/BPCER/ACER
  eval/compare.py           # multi-model evaluation
  train.py                  # shared fine-tuning loop
  benchmark.py              # train N models + evaluate all -> results.json
  cli.py                    # fsd analyze | models | detect | compare | train | benchmark
scripts/
  kaggle_train.py           # self-contained cloud-GPU training notebook
  download_dataset.py       # Kaggle CLI fallback downloader
```

## License / data

Code: MIT. The CelebA-Spoof dataset is for **non-commercial research only** — see the original repo's terms.
