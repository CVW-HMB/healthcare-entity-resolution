"""Overmatching detection for identifying incorrectly merged clusters."""

import networkx as nx

from ..logging import get_logger

logger = get_logger("graph.overmatching")


def detect_overmatching(G: nx.Graph, cluster: set[str]) -> list[str]:
    """
    Detect signs of overmatching in a cluster.

    Returns list of warning messages for suspicious clusters.

    Checks:
    1. NPI conflict: Multiple distinct NPIs
    2. Size anomaly: Cluster too large
    3. Specialty conflict: Unrelated specialties
    4. Geographic spread: Too many states
    5. Weak bridge: Cluster connected by single low-weight edge
    """
    warnings = []

    # 1. NPI conflict check
    npis = set()
    for node in cluster:
        npi = G.nodes[node].get("npi")
        if npi:
            npis.add(npi)

    if len(npis) > 1:
        warnings.append(f"CRITICAL: NPI conflict - {len(npis)} different NPIs: {npis}")

    # 2. Size anomaly
    if len(cluster) > 50:
        warnings.append(f"WARNING: Very large cluster with {len(cluster)} records")
    elif len(cluster) > 20:
        warnings.append(f"NOTICE: Large cluster with {len(cluster)} records")

    # 3. Specialty conflict
    specialties = set()
    for node in cluster:
        spec = G.nodes[node].get("specialty")
        if spec:
            # Normalize specialty for comparison
            specialties.add(spec.upper().strip())

    conflicting_pairs = _find_conflicting_specialties(specialties)
    if conflicting_pairs:
        warnings.append(f"WARNING: Conflicting specialties found: {conflicting_pairs}")

    # 4. Geographic spread
    states = set()
    for node in cluster:
        state = G.nodes[node].get("facility_state")
        if state:
            states.add(state.upper())

    if len(states) > 3:
        warnings.append(f"WARNING: Records span {len(states)} states: {states}")

    # 5. Weak bridge detection
    weak_bridges = find_weak_bridges(G, cluster, threshold=0.5)
    if weak_bridges:
        warnings.append(
            f"WARNING: Cluster connected by {len(weak_bridges)} weak edge(s) "
            f"that could be false positives"
        )

    return warnings


def _find_conflicting_specialties(specialties: set[str]) -> list[tuple[str, str]]:
    """Find specialty pairs that are unlikely to belong to same physician."""
    # Specialties that are incompatible (different training paths)
    incompatible_groups = [
        {"PEDIATRICS", "GERIATRICS"},
        {"OBSTETRICS", "UROLOGY"},
        {"DERMATOLOGY", "CARDIOLOGY"},
        {"PSYCHIATRY", "ORTHOPEDIC SURGERY"},
        {"OPHTHALMOLOGY", "GASTROENTEROLOGY"},
    ]

    conflicts = []
    specialty_list = list(specialties)

    for i, spec1 in enumerate(specialty_list):
        for spec2 in specialty_list[i + 1 :]:
            for group in incompatible_groups:
                # Check if both specialties match different items in an incompatible group
                matches1 = [g for g in group if g in spec1]
                matches2 = [g for g in group if g in spec2]
                if matches1 and matches2 and matches1 != matches2:
                    conflicts.append((spec1, spec2))

    return conflicts


def find_weak_bridges(
    G: nx.Graph,
    cluster: set[str],
    threshold: float = 0.5,
) -> list[tuple[str, str, float]]:
    """
    Find edges that, if removed, would split the cluster.

    These are "bridge" edges. If they have low weight, the cluster is suspect.

    Returns list of (node1, node2, weight) for weak bridges.
    """
    subgraph = G.subgraph(cluster).copy()
    weak_bridges = []

    # Find all bridges (edges whose removal disconnects the graph)
    bridges = list(nx.bridges(subgraph))

    for u, v in bridges:
        weight = subgraph[u][v].get("weight", 0.5)
        if weight < threshold:
            weak_bridges.append((u, v, weight))

    return weak_bridges


def find_articulation_points(G: nx.Graph, cluster: set[str]) -> list[str]:
    """
    Find nodes whose removal would disconnect the cluster.

    These are critical nodes - if they're low quality matches,
    the cluster might be incorrectly merged.
    """
    subgraph = G.subgraph(cluster)
    return list(nx.articulation_points(subgraph))


def suggest_cluster_splits(
    G: nx.Graph,
    cluster: set[str],
    threshold: float = 0.5,
) -> list[set[str]]:
    """
    Suggest how to split a problematic cluster.

    Removes weak bridges and returns resulting components.
    """
    subgraph = G.subgraph(cluster).copy()

    # Remove weak bridges
    weak_bridges = find_weak_bridges(G, cluster, threshold)
    for u, v, _ in weak_bridges:
        if subgraph.has_edge(u, v):
            subgraph.remove_edge(u, v)

    # Return new components
    return [set(c) for c in nx.connected_components(subgraph)]


def get_cluster_cohesion(G: nx.Graph, cluster: set[str]) -> float:
    """
    Calculate cluster cohesion score.

    Higher score = more tightly connected = more likely to be correct.
    """
    if len(cluster) <= 1:
        return 1.0

    subgraph = G.subgraph(cluster)

    # Average edge weight
    weights = [d["weight"] for _, _, d in subgraph.edges(data=True)]
    if not weights:
        return 0.0

    avg_weight = sum(weights) / len(weights)

    # Edge density
    max_edges = len(cluster) * (len(cluster) - 1) / 2
    density = len(weights) / max_edges if max_edges > 0 else 0

    # Cohesion = weighted combination
    cohesion = (avg_weight * 0.6) + (density * 0.4)

    return cohesion
