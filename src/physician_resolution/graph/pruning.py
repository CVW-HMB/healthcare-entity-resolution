"""Graph pruning to remove weak edges and resolve conflicts."""

import networkx as nx

from ..logging import get_logger
from .clustering import find_clusters

logger = get_logger("graph.pruning")


def prune_low_confidence_edges(G: nx.Graph, threshold: float = 0.4) -> nx.Graph:
    """
    Remove edges below confidence threshold.

    This may split clusters (which is often correct).
    """
    edges_to_remove = [(u, v) for u, v, d in G.edges(data=True) if d.get("weight", 0) < threshold]

    G.remove_edges_from(edges_to_remove)
    logger.info(f"Removed {len(edges_to_remove)} low-confidence edges (threshold={threshold})")

    return G


def prune_npi_conflicts(G: nx.Graph) -> nx.Graph:
    """
    For clusters with NPI conflicts, remove lowest-weight edges until resolved.

    NPI conflicts indicate overmatching - two different physicians merged.
    """
    conflicts_resolved = 0

    # Keep iterating until no conflicts remain
    while True:
        clusters = find_clusters(G)
        conflict_found = False

        for cluster in clusters:
            npis = {}  # npi -> list of nodes
            for node in cluster:
                npi = G.nodes[node].get("npi")
                if npi:
                    if npi not in npis:
                        npis[npi] = []
                    npis[npi].append(node)

            # Check for conflict
            if len(npis) > 1:
                conflict_found = True
                # Find the weakest edge connecting nodes with different NPIs
                weakest_edge = _find_weakest_cross_npi_edge(G, cluster, npis)
                if weakest_edge:
                    G.remove_edge(*weakest_edge)
                    conflicts_resolved += 1
                    logger.debug(f"Removed edge {weakest_edge} to resolve NPI conflict")
                break  # Restart cluster detection

        if not conflict_found:
            break

    if conflicts_resolved > 0:
        logger.info(f"Resolved NPI conflicts by removing {conflicts_resolved} edges")

    return G


def _find_weakest_cross_npi_edge(
    G: nx.Graph,
    cluster: set[str],
    npis: dict[str, list[str]],
) -> tuple[str, str] | None:
    """Find the weakest edge connecting nodes with different NPIs."""
    subgraph = G.subgraph(cluster)
    weakest_edge = None
    weakest_weight = float("inf")

    for u, v, data in subgraph.edges(data=True):
        u_npi = G.nodes[u].get("npi")
        v_npi = G.nodes[v].get("npi")

        # Check if edge crosses NPI groups
        if u_npi and v_npi and u_npi != v_npi:
            weight = data.get("weight", 0.5)
            if weight < weakest_weight:
                weakest_weight = weight
                weakest_edge = (u, v)

        # Also check edges between NPI-having and non-NPI nodes that bridge groups
        elif u_npi or v_npi:
            # This edge might be bridging two NPI groups through a non-NPI node
            weight = data.get("weight", 0.5)
            if weight < weakest_weight:
                weakest_weight = weight
                weakest_edge = (u, v)

    return weakest_edge


def prune_oversized_clusters(G: nx.Graph, max_size: int = 100) -> nx.Graph:
    """
    For clusters exceeding max_size, iteratively remove lowest-weight edges.

    Very large clusters are usually overmatched.
    """
    iterations = 0
    max_iterations = 1000  # Safety limit

    while iterations < max_iterations:
        clusters = find_clusters(G)
        oversized = [c for c in clusters if len(c) > max_size]

        if not oversized:
            break

        for cluster in oversized:
            # Find and remove weakest edge
            subgraph = G.subgraph(cluster)
            weakest_edge = None
            weakest_weight = float("inf")

            for u, v, data in subgraph.edges(data=True):
                weight = data.get("weight", 0.5)
                if weight < weakest_weight:
                    weakest_weight = weight
                    weakest_edge = (u, v)

            if weakest_edge:
                G.remove_edge(*weakest_edge)
                logger.debug(f"Removed edge {weakest_edge} from oversized cluster")

        iterations += 1

    if iterations > 0:
        logger.info(f"Pruned oversized clusters in {iterations} iterations")

    return G


def prune_weak_bridges(G: nx.Graph, threshold: float = 0.5) -> nx.Graph:
    """
    Remove weak bridge edges that are the only connection between cluster parts.

    These are often false positive matches.
    """
    edges_removed = 0

    for cluster in find_clusters(G):
        if len(cluster) <= 2:
            continue

        subgraph = G.subgraph(cluster).copy()

        # Find bridges
        try:
            bridges = list(nx.bridges(subgraph))
        except nx.NetworkXError:
            continue

        for u, v in bridges:
            weight = G[u][v].get("weight", 0.5)
            if weight < threshold:
                G.remove_edge(u, v)
                edges_removed += 1
                logger.debug(f"Removed weak bridge ({u}, {v}) with weight {weight}")

    if edges_removed > 0:
        logger.info(f"Removed {edges_removed} weak bridge edges")

    return G


def full_pruning_pipeline(
    G: nx.Graph,
    min_edge_weight: float = 0.4,
    max_cluster_size: int = 100,
    prune_conflicts: bool = True,
) -> nx.Graph:
    """
    Run full pruning pipeline.

    Order matters:
    1. Remove very low weight edges
    2. Resolve NPI conflicts
    3. Split oversized clusters
    4. Remove weak bridges
    """
    logger.info("Starting pruning pipeline...")

    initial_edges = G.number_of_edges()

    # Step 1: Remove low confidence edges
    G = prune_low_confidence_edges(G, threshold=min_edge_weight * 0.75)

    # Step 2: Resolve NPI conflicts
    if prune_conflicts:
        G = prune_npi_conflicts(G)

    # Step 3: Handle oversized clusters
    G = prune_oversized_clusters(G, max_size=max_cluster_size)

    # Step 4: Remove weak bridges
    G = prune_weak_bridges(G, threshold=min_edge_weight)

    final_edges = G.number_of_edges()
    logger.info(
        f"Pruning complete: {initial_edges} -> {final_edges} edges "
        f"({initial_edges - final_edges} removed)"
    )

    return G
