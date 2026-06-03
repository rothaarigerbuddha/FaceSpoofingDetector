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

> **Note:** only AENet has CelebA-Spoof pretrained weights. The other four start from ImageNet backbones with a randomly-initialised head — train them with `fsd train`/`fsd benchmark` before the comparison numbers are meaningful.

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

## Thesis experiment — does auxiliary information improve robustness? (AENet_C,S)

We test the thesis *"semantic auxiliary information improves robustness to
presentation attacks"* honestly: **only AENet** gets its architectural advantage
— multi-task semantic supervision — while EfficientNet-B0 and DeepPixBiS stay
plain binary classifiers. That contrast is the point: a specialised architecture
(AENet) can exploit auxiliary labels; generic CNNs cannot. All models share one
budget, seed and test subset; **inference and evaluation are identical** — every
model is scored from its `fc_live`/binary head only, so APCER/BPCER/ACER/AUC/EER
are computed the same way. The auxiliary heads exist **only during AENet training**.

**Multi-task loss (AENet only).** Using CelebA-Spoof's existing semantic labels:

```
L = L_live + λ_attack·L_attack + λ_light·L_light + λ_attr·L_attr
```

| Term | Loss | Label (44-vector index) | Weight | Masking |
|------|------|--------------------------|--------|---------|
| `L_live` | CrossEntropy, 2-way | `[43]` live/spoof | **1.0** (main) | none |
| `L_attack` | CrossEntropy, 11-way | `[40]` spoof type (0=Live, 1–10 attacks) | 0.5 | none — head has a "Live" class, so live→0 is valid |
| `L_light` | CrossEntropy, 5-way | `[41]` illumination (0=Live, 1–4) | 0.25 | none — same sentinel-0 reasoning |
| `L_attr` | BCE, 40 attributes | `[0:40]` face attributes | 0.1 | **live-only** — attributes are annotated for live images; spoof rows are masked out |

Head dimensions match the AENet checkpoint exactly: `fc_live`→2, `fc_attack`→11,
`fc_light`→5, `fc_live_attribute`→40 (`src/fsd/detectors/aenet.py`). The masking is
derived from the parser contract in `src/fsd/dataset/celeba_spoof.py` (attributes
are *"live images only"*; spoof-type/illumination use 0 as the "Live" sentinel).
Weights live in the recommended 0.1–0.5 band with the most spoofing-relevant
signal (attack type) highest and the high-dim attribute BCE smallest so it can't
dominate; lower them (`--lambda-*`) if the live head destabilises.

**Geometry ("G") is intentionally not implemented:** CelebA-Spoof ships no depth
or reflection maps, so this is strictly the **semantic** variant **AENet_C,S**.

**Reproduce** (GPU box with the dataset on disk):

```bash
python scripts/thesis_experiment.py \
  --data-root /data/celeba-spoof \
  --train-labels /data/celeba-spoof/metas/intra_test/train_label.json \
  --test-labels  /data/celeba-spoof/metas/intra_test/test_label.json \
  --aenet-ckpt weights/ckpt_iter.pth.tar \
  --n-train 40000 --n-test 4000 --epochs 6 --device cuda --out runs/thesis
```

This trains `efficientnet`/`deeppixbis` (binary), `aenet_binary` and
`aenet_multitask` on the **same** 40k/6-epoch budget, loads the official
pretrained AENet as a reference row (the prior binary result, ACER≈0.075),
evaluates all on the same test subset, measures latency/FPS (ViT/CDCN reported
latency-only), and prints the summary table **plus the AENet binary-vs-multitask
comparison** — the headline ablation. A single-task `fsd train --model aenet
--multitask` is also available. Smoke-test the plumbing with no dataset/GPU:

```bash
python scripts/thesis_experiment.py --smoke --out runs/smoke   # CPU, synthetic mini-set
```

> The verdict is reported **honestly**: if multi-task does not lower ACER on the
> budget, the script says so rather than hiding it.

## Layout

```
src/fsd/
  dataset/celeba_spoof.py   # label schema, parsing, stats, integrity
  utils/image.py            # BB face-crop (matches official client.py)
  detectors/                # base + registry + aenet/cdcn/deeppixbis/efficientnet/vit
  eval/metrics.py           # TPR@FPR, AUC, EER, APCER/BPCER/ACER
  eval/compare.py           # multi-model evaluation
  eval/latency.py           # uniform inference latency / FPS measurement
  multitask.py              # AENet_C,S auxiliary loss + label masking
  train.py                  # shared fine-tuning loop (+ --multitask for AENet)
  benchmark.py              # train N models + evaluate all -> results.json
  cli.py                    # fsd analyze | models | detect | compare | train | benchmark
scripts/
  thesis_experiment.py      # AENet binary-vs-multitask experiment (+ --smoke)
  kaggle_train.py           # self-contained cloud-GPU training notebook
  download_dataset.py       # Kaggle CLI fallback downloader
```

## License / data

Code: MIT. The CelebA-Spoof dataset is for **non-commercial research only** — see the original repo's terms.
