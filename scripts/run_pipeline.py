#!/usr/bin/env python
"""Run the entity resolution pipeline."""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from physician_resolution.config import PipelineConfig
from physician_resolution.pipeline import run_pipeline


def main():
    parser = argparse.ArgumentParser(description="Run the physician entity resolution pipeline")
    parser.add_argument(
        "-d",
        "--data-dir",
        type=str,
        default="data/synthetic",
        help="Directory containing source CSV files (default: data/synthetic)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default=None,
        help="Output directory (default: timestamped in outputs/runs/)",
    )
    parser.add_argument(
        "--match-threshold",
        type=float,
        default=0.85,
        help="Threshold for classifying as match (default: 0.85)",
    )
    parser.add_argument(
        "--non-match-threshold",
        type=float,
        default=0.30,
        help="Threshold for classifying as non-match (default: 0.30)",
    )
    parser.add_argument(
        "--min-edge-weight",
        type=float,
        default=0.40,
        help="Minimum edge weight to keep (default: 0.40)",
    )
    parser.add_argument(
        "--max-cluster-size",
        type=int,
        default=100,
        help="Maximum cluster size before splitting (default: 100)",
    )
    parser.add_argument(
        "--include-uncertain",
        action="store_true",
        help="Include uncertain matches in graph",
    )
    parser.add_argument(
        "--no-soundex",
        action="store_true",
        help="Disable soundex blocking",
    )

    args = parser.parse_args()

    # Build config
    config = PipelineConfig(
        match_threshold=args.match_threshold,
        non_match_threshold=args.non_match_threshold,
        min_edge_weight=args.min_edge_weight,
        max_cluster_size=args.max_cluster_size,
        include_uncertain_matches=args.include_uncertain,
        use_soundex_blocking=not args.no_soundex,
    )

    # Run pipeline
    results = run_pipeline(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        config=config,
    )

    # Print summary
    print("\n" + "=" * 60)
    print("Pipeline Results Summary")
    print("=" * 60)
    print(f"Status: {results['status']}")
    print(f"Output: {results['output_dir']}")
    print(f"Source records: {results['total_records']}")
    print(f"Matches found: {results['match_count']}")
    print(f"Clusters: {results['cluster_count']}")
    print(f"Canonical physicians: {results['canonical_physician_count']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
