#!/usr/bin/env python
"""Script to generate synthetic data."""

import argparse
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_generator.generate import generate_all


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic physician data")
    parser.add_argument(
        "-n",
        "--num-physicians",
        type=int,
        default=500,
        help="Number of physicians to generate (default: 500)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default="data/synthetic",
        help="Output directory (default: data/synthetic)",
    )
    parser.add_argument(
        "-s",
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)",
    )

    args = parser.parse_args()

    generate_all(
        num_physicians=args.num_physicians,
        output_dir=args.output_dir,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
