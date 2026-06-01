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
