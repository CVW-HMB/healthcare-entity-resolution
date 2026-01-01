"""Load source data files into DataFrames."""

from pathlib import Path

import pandas as pd

from ..config import SYNTHETIC_DIR
from ..logging import get_logger

logger = get_logger("etl.loaders")


def load_cms_claims(filepath: Path | None = None) -> pd.DataFrame:
    """Load CMS claims data."""
    filepath = filepath or SYNTHETIC_DIR / "cms_claims.csv"
    logger.info(f"Loading CMS claims from {filepath}")
    df = pd.read_csv(filepath, dtype=str)
    logger.info(f"Loaded {len(df)} CMS claim records")
    return df


def load_state_licenses(filepath: Path | None = None) -> pd.DataFrame:
    """Load state license data."""
    filepath = filepath or SYNTHETIC_DIR / "state_licenses.csv"
    logger.info(f"Loading state licenses from {filepath}")
    df = pd.read_csv(filepath, dtype=str)
    logger.info(f"Loaded {len(df)} state license records")
    return df


def load_hospital_affiliations(filepath: Path | None = None) -> pd.DataFrame:
    """Load hospital affiliation data."""
    filepath = filepath or SYNTHETIC_DIR / "hospital_affiliations.csv"
    logger.info(f"Loading hospital affiliations from {filepath}")
    df = pd.read_csv(filepath, dtype=str)
    logger.info(f"Loaded {len(df)} hospital affiliation records")
    return df


def load_publications(filepath: Path | None = None) -> pd.DataFrame:
    """Load publication data."""
    filepath = filepath or SYNTHETIC_DIR / "publications.csv"
    logger.info(f"Loading publications from {filepath}")
    df = pd.read_csv(filepath, dtype=str)
    logger.info(f"Loaded {len(df)} publication records")
    return df


def load_referrals(filepath: Path | None = None) -> pd.DataFrame:
    """Load referral data."""
    filepath = filepath or SYNTHETIC_DIR / "referrals.csv"
    logger.info(f"Loading referrals from {filepath}")
    df = pd.read_csv(filepath, dtype=str)
    logger.info(f"Loaded {len(df)} referral records")
    return df


def load_ground_truth(filepath: Path | None = None) -> pd.DataFrame:
    """Load ground truth mapping."""
    filepath = filepath or SYNTHETIC_DIR.parent / "ground_truth.csv"
    logger.info(f"Loading ground truth from {filepath}")
    df = pd.read_csv(filepath, dtype=str)
    logger.info(f"Loaded {len(df)} ground truth records")
    return df


def load_all_sources(data_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    """Load all source data files."""
    data_dir = data_dir or SYNTHETIC_DIR

    return {
        "cms": load_cms_claims(data_dir / "cms_claims.csv"),
        "license": load_state_licenses(data_dir / "state_licenses.csv"),
        "hospital": load_hospital_affiliations(data_dir / "hospital_affiliations.csv"),
        "publication": load_publications(data_dir / "publications.csv"),
        "referral": load_referrals(data_dir / "referrals.csv"),
    }
