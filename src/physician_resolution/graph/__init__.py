"""Graph module for identity resolution."""

from .builder import build_identity_graph, get_graph_stats
from .clustering import (
    assign_cluster_ids,
    find_clusters,
    get_cluster_for_node,
    get_cluster_sizes,
    get_cluster_subgraph,
)
from .overmatching import (
    detect_overmatching,
    find_articulation_points,
    find_weak_bridges,
    get_cluster_cohesion,
    suggest_cluster_splits,
)
from .pruning import (
    full_pruning_pipeline,
    prune_low_confidence_edges,
    prune_npi_conflicts,
    prune_oversized_clusters,
    prune_weak_bridges,
)
from .quality import (
    assess_cluster_quality,
    get_quality_summary,
)

__all__ = [
    # Builder
    "build_identity_graph",
    "get_graph_stats",
    # Clustering
    "find_clusters",
    "get_cluster_subgraph",
    "get_cluster_for_node",
    "get_cluster_sizes",
    "assign_cluster_ids",
    # Quality
    "assess_cluster_quality",
    "get_quality_summary",
    # Overmatching
    "detect_overmatching",
    "find_weak_bridges",
    "find_articulation_points",
    "suggest_cluster_splits",
    "get_cluster_cohesion",
    # Pruning
    "prune_low_confidence_edges",
    "prune_npi_conflicts",
    "prune_oversized_clusters",
    "prune_weak_bridges",
    "full_pruning_pipeline",
]
