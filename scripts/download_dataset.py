"""Download the CelebA-Spoof Kaggle mirror to D:\\projects\\celeba-spoof.

Primary path in this project is the Kaggle MCP server (configured in the client);
ask the assistant to download once it is authenticated. This script is the
standalone CLI fallback using the `kaggle` command-line tool.

Usage:
    python scripts/download_dataset.py [--dest D:\\projects\\celeba-spoof]

Requires the `kaggle` CLI and an API token (~/.kaggle/kaggle.json).
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

DATASET = "attentionlayer241/celeba-spoof-for-face-antispoofing"
DEFAULT_DEST = Path("D:/projects/celeba-spoof")


def main() -> int:
    ap = argparse.ArgumentParser(description="Download CelebA-Spoof from Kaggle.")
    ap.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    args = ap.parse_args()

    if shutil.which("kaggle") is None:
        print("kaggle CLI not found. Install with: pip install kaggle", file=sys.stderr)
        print("Then place your API token at ~/.kaggle/kaggle.json", file=sys.stderr)
        print("Or use the Kaggle MCP server (preferred in this project).", file=sys.stderr)
        return 1

    args.dest.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {DATASET} -> {args.dest}")
    cmd = ["kaggle", "datasets", "download", "-d", DATASET, "-p", str(args.dest), "--unzip"]
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
