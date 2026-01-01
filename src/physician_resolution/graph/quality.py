"""Cluster quality assessment."""

import networkx as nx

from ..logging import get_logger
from ..schemas.clusters import ClusterQuality

logger = get_logger("graph.quality")


def assess_cluster_quality(
    G: nx.Graph,
    cluster: set[str],
    cluster_id: str = "",
) -> ClusterQuality:
    """
    Evaluate whether a cluster looks like one real physician.

    Good cluster signals:
    - All records share same NPI (if available)
    - High average edge weight
    - Single specialty
    - Locations within reasonable distance

    Bad cluster signals (overmatching):
    - Multiple different NPIs
    - Very large cluster
    - Multiple specialties
    - Locations in different states
    """
    subgraph = G.subgraph(cluster)
    warnings = []

    # Size
    size = len(cluster)

    # Edge weight statistics
    edge_weights = [d["weight"] for _, _, d in subgraph.edges(data=True)]
    avg_edge_weight = sum(edge_weights) / len(edge_weights) if edge_weights else 0.0
    min_edge_weight = min(edge_weights) if edge_weights else 0.0

    # Density
    max_edges = size * (size - 1) / 2
    density = len(edge_weights) / max_edges if max_edges > 0 else 1.0

    # NPI analysis
    npis = [G.nodes[n].get("npi") for n in cluster if G.nodes[n].get("npi")]
    unique_npis = set(npis)
    npi_count = len(unique_npis)
    npi_conflict = npi_count > 1

    if npi_conflict:
        warnings.append(f"NPI conflict: {npi_count} different NPIs found: {unique_npis}")

    # State analysis
    states = [G.nodes[n].get("facility_state") for n in cluster if G.nodes[n].get("facility_state")]
    unique_states = set(states)
    state_count = len(unique_states)

    if state_count > 3:
        warnings.append(f"Geographic spread: records in {state_count} states: {unique_states}")

    # Specialty analysis
    specialties = [G.nodes[n].get("specialty") for n in cluster if G.nodes[n].get("specialty")]
    unique_specialties = set(specialties)
    specialty_count = len(unique_specialties)

    # Check for conflicting specialties (not just variations)
    if specialty_count > 3:
        warnings.append(f"Multiple specialties: {specialty_count} found")

    # Size warning
    if size > 20:
        warnings.append(f"Large cluster: {size} records")

    # Calculate overall quality score
    quality_score = _calculate_quality_score(
        size=size,
        avg_edge_weight=avg_edge_weight,
        min_edge_weight=min_edge_weight,
        density=density,
        npi_conflict=npi_conflict,
        state_count=state_count,
        specialty_count=specialty_count,
    )

    return ClusterQuality(
        cluster_id=cluster_id,
        size=size,
        avg_edge_weight=avg_edge_weight,
        min_edge_weight=min_edge_weight,
        density=density,
        npi_count=npi_count,
        npi_conflict=npi_conflict,
        state_count=state_count,
        specialty_count=specialty_count,
        quality_score=quality_score,
        warnings=warnings,
    )


def _calculate_quality_score(
    size: int,
    avg_edge_weight: float,
    min_edge_weight: float,
    density: float,
    npi_conflict: bool,
    state_count: int,
    specialty_count: int,
) -> float:
    """Calculate overall quality score (0-1)."""
    # NPI conflict is critical
    if npi_conflict:
        return 0.1

    score = 1.0

    # Edge weight factor
    score *= avg_edge_weight * 0.4 + min_edge_weight * 0.2 + 0.4

    # Density factor (higher is better for small clusters)
    if size <= 5:
        score *= density * 0.3 + 0.7

    # State spread penalty
    if state_count > 1:
        score *= max(0.5, 1.0 - (state_count - 1) * 0.15)

    # Specialty diversity penalty
    if specialty_count > 2:
        score *= max(0.5, 1.0 - (specialty_count - 2) * 0.1)

    # Size penalty for very large clusters
    if size > 10:
        score *= max(0.5, 1.0 - (size - 10) * 0.02)

    return max(0.0, min(1.0, score))


def get_quality_summary(qualities: list[ClusterQuality]) -> dict:
    """Summarize quality metrics across all clusters."""
    if not qualities:
        return {}

    scores = [q.quality_score for q in qualities]
    conflict_count = sum(1 for q in qualities if q.npi_conflict)
    warning_count = sum(1 for q in qualities if q.warnings)

    return {
        "total_clusters": len(qualities),
        "avg_quality_score": sum(scores) / len(scores),
        "min_quality_score": min(scores),
        "max_quality_score": max(scores),
        "npi_conflict_count": conflict_count,
        "clusters_with_warnings": warning_count,
        "high_quality_count": sum(1 for s in scores if s >= 0.8),
        "medium_quality_count": sum(1 for s in scores if 0.5 <= s < 0.8),
        "low_quality_count": sum(1 for s in scores if s < 0.5),
    }
