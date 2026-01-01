import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass
class PipelineConfig:
    """Configuration for entity resolution pipeline."""

    match_threshold: float = 0.85
    non_match_threshold: float = 0.30
    min_edge_weight: float = 0.40
    max_cluster_size: int = 100
    prune_npi_conflicts: bool = True
    use_soundex_blocking: bool = True
    include_uncertain_matches: bool = False

    @classmethod
    def from_env(cls) -> "PipelineConfig":
        """Load config from environment variables."""
        return cls(
            match_threshold=float(os.getenv("MATCH_THRESHOLD", "0.85")),
            non_match_threshold=float(os.getenv("NON_MATCH_THRESHOLD", "0.30")),
            min_edge_weight=float(os.getenv("MIN_EDGE_WEIGHT", "0.40")),
            max_cluster_size=int(os.getenv("MAX_CLUSTER_SIZE", "100")),
        )


PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SYNTHETIC_DIR = DATA_DIR / "synthetic"
REFERENCE_DIR = DATA_DIR / "reference"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"


def get_run_output_dir() -> Path:
    """Create and return a timestamped output directory for this run."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_dir = OUTPUTS_DIR / "runs" / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "plots").mkdir()
    (run_dir / "reports").mkdir()
    (run_dir / "exports").mkdir()
    return run_dir


def get_database_url() -> str:
    """Get database URL from environment."""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL environment variable not set")
    return url
