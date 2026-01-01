#!/usr/bin/env python
"""Seed the database with pipeline results."""

import argparse
import csv
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from physician_resolution.db.models import (
    CanonicalPhysician,
    InfluenceScore,
)
from physician_resolution.db.session import create_tables, drop_tables, get_session
from physician_resolution.logging import get_logger, setup_logging

logger = get_logger("seed_db")


def seed_canonical_physicians(exports_dir: Path) -> int:
    """Load canonical physicians from CSV."""
    filepath = exports_dir / "canonical_physicians.csv"
    if not filepath.exists():
        logger.warning(f"File not found: {filepath}")
        return 0

    count = 0
    with get_session() as session:
        with open(filepath) as f:
            reader = csv.DictReader(f)
            for row in reader:
                phys = CanonicalPhysician(
                    id=row["canonical_id"],
                    npi=row["npi"] or None,
                    name=row["name"] or None,
                    specialty=row["specialty"] or None,
                    primary_facility=row["primary_facility"] or None,
                    city=row["city"] or None,
                    state=row["state"] or None,
                    confidence_score=float(row["confidence"]) if row["confidence"] else None,
                    source_count=int(row["source_count"]) if row["source_count"] else None,
                )
                session.add(phys)
                count += 1

        session.commit()

    logger.info(f"Loaded {count} canonical physicians")
    return count


def seed_influence_scores(exports_dir: Path) -> int:
    """Load influence scores from CSV."""
    filepath = exports_dir / "influence_scores.csv"
    if not filepath.exists():
        logger.warning(f"File not found: {filepath}")
        return 0

    count = 0
    with get_session() as session:
        with open(filepath) as f:
            reader = csv.DictReader(f)
            for row in reader:
                score = InfluenceScore(
                    physician_id=row["canonical_id"],
                    pagerank_score=float(row["influence_score"])
                    if row["influence_score"]
                    else None,
                )
                session.add(score)
                count += 1

        session.commit()

    logger.info(f"Loaded {count} influence scores")
    return count


def main():
    parser = argparse.ArgumentParser(description="Seed database with pipeline results")
    parser.add_argument(
        "-d",
        "--exports-dir",
        type=str,
        required=True,
        help="Directory containing exported CSV files",
    )
    parser.add_argument(
        "--drop-tables",
        action="store_true",
        help="Drop all tables before seeding",
    )
    parser.add_argument(
        "--create-tables",
        action="store_true",
        help="Create tables before seeding",
    )

    args = parser.parse_args()
    exports_dir = Path(args.exports_dir)

    setup_logging()

    if not exports_dir.exists():
        logger.error(f"Exports directory not found: {exports_dir}")
        sys.exit(1)

    if args.drop_tables:
        logger.info("Dropping tables...")
        drop_tables()

    if args.create_tables:
        logger.info("Creating tables...")
        create_tables()

    logger.info("Seeding database...")

    # Seed in order (respecting foreign keys)
    phys_count = seed_canonical_physicians(exports_dir)
    influence_count = seed_influence_scores(exports_dir)

    print("\n" + "=" * 60)
    print("Database Seeding Complete")
    print("=" * 60)
    print(f"Canonical physicians: {phys_count}")
    print(f"Influence scores: {influence_count}")
    print("=" * 60)


if __name__ == "__main__":
    main()
