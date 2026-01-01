"""Analysis and reporting module."""

from .cluster_report import (
    analyze_canonical_physicians,
    analyze_cluster_quality,
    analyze_cluster_sizes,
    analyze_source_coverage,
    generate_cluster_report,
)
from .data_quality import (
    analyze_dataframe,
    analyze_source_records,
    find_duplicate_npis,
    generate_data_quality_report,
)
from .evaluation import (
    analyze_errors,
    evaluate_clustering,
    generate_evaluation_report,
    load_ground_truth,
)
from .match_quality import (
    analyze_match_confidence,
    analyze_match_results,
    analyze_npi_matches,
    generate_match_quality_report,
    get_low_confidence_matches,
)

__all__ = [
    # Data quality
    "analyze_source_records",
    "analyze_dataframe",
    "find_duplicate_npis",
    "generate_data_quality_report",
    # Match quality
    "analyze_match_results",
    "analyze_match_confidence",
    "analyze_npi_matches",
    "get_low_confidence_matches",
    "generate_match_quality_report",
    # Cluster report
    "analyze_cluster_sizes",
    "analyze_cluster_quality",
    "analyze_source_coverage",
    "analyze_canonical_physicians",
    "generate_cluster_report",
    # Evaluation
    "load_ground_truth",
    "evaluate_clustering",
    "analyze_errors",
    "generate_evaluation_report",
]
