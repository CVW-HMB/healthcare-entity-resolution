"""Influence scoring and colleague detection."""

from collections import defaultdict

import networkx as nx
import pandas as pd

from ..logging import get_logger
from ..schemas.entities import CanonicalPhysician

logger = get_logger("network.influence")


def calculate_influence_scores(
    referral_graph: nx.DiGraph,
    weight_key: str = "referral_count",
) -> dict[str, float]:
    """
    Calculate PageRank-style influence scores.

    High-influence physicians:
    - Receive many referrals
    - Receive referrals from other high-influence physicians

    This helps identify "key opinion leaders" (KOLs).

    Args:
        referral_graph: Directed graph of referrals
        weight_key: Edge attribute to use as weight

    Returns:
        Dict mapping canonical_id -> influence score (0-1)
    """
    if referral_graph.number_of_nodes() == 0:
        return {}

    try:
        scores = nx.pagerank(
            referral_graph,
            weight=weight_key,
            alpha=0.85,  # Damping factor
            max_iter=100,
        )
    except nx.PowerIterationFailedConvergence:
        logger.warning("PageRank failed to converge, using unweighted")
        scores = nx.pagerank(referral_graph, alpha=0.85, max_iter=100)

    logger.info(f"Calculated influence scores for {len(scores)} physicians")

    return scores


def get_top_influencers(
    influence_scores: dict[str, float],
    n: int = 20,
) -> list[tuple[str, float]]:
    """Get top N physicians by influence score."""
    sorted_scores = sorted(influence_scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_scores[:n]


def calculate_referral_metrics(
    referral_graph: nx.DiGraph,
) -> dict[str, dict[str, int]]:
    """
    Calculate referral metrics for each physician.

    Returns dict with:
    - referral_in_count: number of unique referrers
    - referral_out_count: number of unique recipients
    - total_referrals_in: total patients referred to them
    - total_referrals_out: total patients they referred
    """
    metrics: dict[str, dict[str, int]] = {}

    for node in referral_graph.nodes():
        in_edges = referral_graph.in_edges(node, data=True)
        out_edges = referral_graph.out_edges(node, data=True)

        metrics[node] = {
            "referral_in_count": referral_graph.in_degree(node),
            "referral_out_count": referral_graph.out_degree(node),
            "total_referrals_in": sum(d.get("referral_count", 1) for _, _, d in in_edges),
            "total_referrals_out": sum(d.get("referral_count", 1) for _, _, d in out_edges),
        }

    return metrics


def find_colleagues(
    canonical_physicians: list[CanonicalPhysician],
    publications_df: pd.DataFrame | None = None,
) -> list[tuple[str, str, str, float]]:
    """
    Find colleague relationships from:
    1. Same facility
    2. Co-authorship (if publications provided)
    3. Same medical school + graduation year (residency classmates)

    Returns: List of (physician_id_1, physician_id_2, relationship_type, strength)
    """
    colleagues: list[tuple[str, str, str, float]] = []

    # Index physicians by facility
    facility_physicians: dict[str, list[str]] = defaultdict(list)
    for phys in canonical_physicians:
        if phys.primary_facility:
            facility_key = phys.primary_facility.upper().strip()[:50]
            facility_physicians[facility_key].append(phys.canonical_id)

    # Same facility colleagues
    for facility, phys_ids in facility_physicians.items():
        if len(phys_ids) > 1 and len(phys_ids) < 100:  # Skip very large facilities
            for i, id1 in enumerate(phys_ids):
                for id2 in phys_ids[i + 1 :]:
                    colleagues.append((id1, id2, "same_facility", 0.6))

    # Co-authorship (if publications available)
    if publications_df is not None and not publications_df.empty:
        coauthor_pairs = _find_coauthors(publications_df, canonical_physicians)
        colleagues.extend(coauthor_pairs)

    logger.info(f"Found {len(colleagues)} colleague relationships")

    return colleagues


def _find_coauthors(
    publications_df: pd.DataFrame,
    canonical_physicians: list[CanonicalPhysician],
) -> list[tuple[str, str, str, float]]:
    """Find co-authorship relationships from publications."""
    # This would require matching publication authors to canonical physicians
    # For now, return empty - would need author name matching
    return []


def build_colleague_graph(
    colleagues: list[tuple[str, str, str, float]],
) -> nx.Graph:
    """Build undirected graph of colleague relationships."""
    G = nx.Graph()

    for id1, id2, rel_type, strength in colleagues:
        if G.has_edge(id1, id2):
            # Combine relationship types
            existing = G[id1][id2]
            existing["strength"] = max(existing["strength"], strength)
            existing["relationship_types"].add(rel_type)
        else:
            G.add_edge(
                id1,
                id2,
                strength=strength,
                relationship_types={rel_type},
            )

    logger.info(
        f"Built colleague graph: {G.number_of_nodes()} physicians, "
        f"{G.number_of_edges()} relationships"
    )

    return G


def get_physician_network(
    physician_id: str,
    referral_graph: nx.DiGraph,
    colleague_graph: nx.Graph | None = None,
    depth: int = 1,
) -> dict:
    """
    Get the network around a specific physician.

    Returns:
        - referrers: who refers to this physician
        - recipients: who this physician refers to
        - colleagues: (if colleague_graph provided)
    """
    result = {
        "physician_id": physician_id,
        "referrers": [],
        "recipients": [],
        "colleagues": [],
    }

    # Incoming referrals
    if referral_graph.has_node(physician_id):
        for pred in referral_graph.predecessors(physician_id):
            edge_data = referral_graph[pred][physician_id]
            result["referrers"].append(
                {
                    "physician_id": pred,
                    "referral_count": edge_data.get("referral_count", 0),
                }
            )

        # Outgoing referrals
        for succ in referral_graph.successors(physician_id):
            edge_data = referral_graph[physician_id][succ]
            result["recipients"].append(
                {
                    "physician_id": succ,
                    "referral_count": edge_data.get("referral_count", 0),
                }
            )

    # Colleagues
    if colleague_graph and colleague_graph.has_node(physician_id):
        for neighbor in colleague_graph.neighbors(physician_id):
            edge_data = colleague_graph[physician_id][neighbor]
            result["colleagues"].append(
                {
                    "physician_id": neighbor,
                    "relationship_types": list(edge_data.get("relationship_types", set())),
                    "strength": edge_data.get("strength", 0),
                }
            )

    return result
