"""
Download the Olist Brazilian E-Commerce dataset from Kaggle via kagglehub.

Usage:
  python scripts/download_dataset.py
"""

import shutil
import sys
from pathlib import Path


def download_dataset():
    try:
        import kagglehub
    except ImportError:
        print("Installing kagglehub...")
        import subprocess

        subprocess.check_call([sys.executable, "-m", "pip", "install", "kagglehub"])
        import kagglehub

    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset = "olistbr/brazilian-ecommerce"
    print(f"Downloading dataset: {dataset}")
    print(f"Output directory:    {output_dir.absolute()}\n")

    cache_path = Path(kagglehub.dataset_download(dataset))
    print(f"Kaggle cache path:   {cache_path}\n")

    csv_files = sorted(cache_path.glob("*.csv"))
    if not csv_files:
        print("ERROR: No CSV files found in the downloaded dataset.")
        sys.exit(1)

    for src in csv_files:
        dst = output_dir / src.name
        if not dst.exists() or dst.stat().st_size != src.stat().st_size:
            shutil.copy2(src, dst)
        size_mb = dst.stat().st_size / (1024 * 1024)
        print(f"  {dst.name:<55} {size_mb:6.1f} MB")

    print(f"\n✅ Download complete — {len(csv_files)} CSV files in {output_dir.absolute()}")


if __name__ == "__main__":
    download_dataset()
