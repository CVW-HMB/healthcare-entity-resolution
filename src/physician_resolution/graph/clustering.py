"""Cluster detection using connected components."""

import networkx as nx

from ..logging import get_logger

logger = get_logger("graph.clustering")


def find_clusters(G: nx.Graph) -> list[set[str]]:
    """
    Find connected components in the graph.

    Each component represents a potential single physician entity.

    Returns:
        List of sets, where each set contains source_ids belonging to one cluster
    """
    clusters = list(nx.connected_components(G))

    # Sort by size (largest first) for consistent ordering
    clusters.sort(key=len, reverse=True)

    logger.info(f"Found {len(clusters)} clusters")

    # Log size distribution
    sizes = [len(c) for c in clusters]
    if sizes:
        logger.info(
            f"Cluster sizes: min={min(sizes)}, max={max(sizes)}, "
            f"avg={sum(sizes)/len(sizes):.1f}"
        )

    return clusters


def get_cluster_subgraph(G: nx.Graph, cluster: set[str]) -> nx.Graph:
    """Extract the subgraph for a specific cluster."""
    return G.subgraph(cluster).copy()


def get_cluster_for_node(G: nx.Graph, node_id: str) -> set[str] | None:
    """Find which cluster a node belongs to."""
    if node_id not in G:
        return None

    for component in nx.connected_components(G):
        if node_id in component:
            return component

    return None


def get_cluster_sizes(clusters: list[set[str]]) -> dict[str, int]:
    """Get size distribution of clusters."""
    size_counts: dict[int, int] = {}

    for cluster in clusters:
        size = len(cluster)
        size_counts[size] = size_counts.get(size, 0) + 1

    return {
        "total_clusters": len(clusters),
        "singleton_count": size_counts.get(1, 0),
        "pair_count": size_counts.get(2, 0),
        "small_count": sum(v for k, v in size_counts.items() if 3 <= k <= 5),
        "medium_count": sum(v for k, v in size_counts.items() if 6 <= k <= 10),
        "large_count": sum(v for k, v in size_counts.items() if k > 10),
        "size_distribution": dict(sorted(size_counts.items())),
    }


def assign_cluster_ids(clusters: list[set[str]]) -> dict[str, str]:
    """
    Assign a cluster ID to each node.

    Returns:
        Dict mapping source_id -> cluster_id
    """
    mapping = {}

    for idx, cluster in enumerate(clusters):
        cluster_id = f"CLUSTER_{idx:05d}"
        for node_id in cluster:
            mapping[node_id] = cluster_id

    return mapping
