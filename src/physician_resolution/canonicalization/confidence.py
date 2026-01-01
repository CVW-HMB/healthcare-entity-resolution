"""Confidence scoring for resolved entities."""

import networkx as nx

from ..logging import get_logger

logger = get_logger("canonicalization.confidence")


def calculate_entity_confidence(G: nx.Graph, cluster: set[str]) -> float:
    """
    Calculate confidence that this cluster represents a single real physician.

    Scoring factors:
    1. Edge weight statistics (mean, min)
    2. Cluster density
    3. NPI consistency
    4. Source diversity (matched across multiple sources = more confident)

    Returns: 0.0 to 1.0
    """
    if len(cluster) == 1:
        # Single record - confidence based on source reliability
        node = list(cluster)[0]
        source = G.nodes[node].get("source", "unknown")
        return _source_confidence(source)

    subgraph = G.subgraph(cluster)

    # Edge weight statistics
    weights = [d["weight"] for _, _, d in subgraph.edges(data=True)]
    if not weights:
        return 0.3  # No edges somehow

    avg_weight = sum(weights) / len(weights)
    min_weight = min(weights)

    # Density
    max_edges = len(cluster) * (len(cluster) - 1) / 2
    density = len(weights) / max_edges if max_edges > 0 else 0

    # NPI consistency
    npis = set()
    for node in cluster:
        npi = G.nodes[node].get("npi")
        if npi:
            npis.add(npi)

    npi_score = 1.0 if len(npis) <= 1 else 0.3  # Penalty for NPI conflict

    # Source diversity (more sources = more confident)
    sources = set()
    for node in cluster:
        source = G.nodes[node].get("source")
        if source:
            sources.add(source)

    source_diversity = min(len(sources) / 3.0, 1.0)  # Cap at 3 sources

    # Weighted combination
    confidence = (
        avg_weight * 0.30
        + min_weight * 0.15
        + density * 0.15
        + npi_score * 0.25
        + source_diversity * 0.15
    )

    return min(max(confidence, 0.0), 1.0)


def calculate_record_confidence(
    G: nx.Graph,
    source_id: str,
    cluster: set[str],
) -> float:
    """
    Calculate confidence that THIS SPECIFIC RECORD belongs in this cluster.

    A record weakly connected to the cluster should have lower confidence
    than one strongly connected.

    Approach: Average weight of edges connecting this record to cluster.
    """
    if source_id not in G:
        return 0.0

    if len(cluster) == 1:
        return 0.8  # Single record, no edges to evaluate

    # Get edges connecting this record to others in cluster
    edge_weights = []
    for other_id in cluster:
        if other_id != source_id and G.has_edge(source_id, other_id):
            weight = G[source_id][other_id].get("weight", 0.5)
            edge_weights.append(weight)

    if not edge_weights:
        # Not directly connected to any cluster member
        # Must be connected through intermediaries
        return 0.4

    avg_weight = sum(edge_weights) / len(edge_weights)
    max_weight = max(edge_weights)

    # Consider both average and best connection
    confidence = avg_weight * 0.6 + max_weight * 0.4

    return min(max(confidence, 0.0), 1.0)


def _source_confidence(source: str) -> float:
    """Base confidence by source type."""
    confidence_map = {
        "cms": 0.85,  # CMS has NPI, most reliable
        "license": 0.80,  # State licenses are authoritative
        "hospital": 0.70,  # Hospital directories vary
        "publication": 0.50,  # Publications have abbreviated names
    }
    return confidence_map.get(source, 0.5)


def calculate_all_confidences(
    G: nx.Graph,
    clusters: list[set[str]],
) -> tuple[dict[str, float], dict[str, float]]:
    """
    Calculate entity and record confidences for all clusters.

    Returns:
        (entity_confidences, record_confidences)
        - entity_confidences: canonical_id -> confidence
        - record_confidences: source_id -> confidence
    """
    from .ids import _generate_canonical_id

    entity_confidences: dict[str, float] = {}
    record_confidences: dict[str, float] = {}

    for cluster in clusters:
        canonical_id = _generate_canonical_id(G, cluster)

        # Entity confidence
        entity_conf = calculate_entity_confidence(G, cluster)
        entity_confidences[canonical_id] = entity_conf

        # Record confidences
        for source_id in cluster:
            record_conf = calculate_record_confidence(G, source_id, cluster)
            record_confidences[source_id] = record_conf

    logger.info(
        f"Calculated confidences for {len(entity_confidences)} entities, "
        f"{len(record_confidences)} records"
    )

    return entity_confidences, record_confidences
