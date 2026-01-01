"""Assign canonical IDs to resolved clusters."""

import uuid
from collections import Counter

import networkx as nx

from ..logging import get_logger

logger = get_logger("canonicalization.ids")


def assign_canonical_ids(
    G: nx.Graph,
    clusters: list[set[str]],
) -> dict[str, str]:
    """
    Assign a canonical_physician_id to each cluster.

    Strategy:
    1. If cluster has NPI(s), use most common NPI
    2. Else, generate UUID

    Format: "PHY_{npi}" or "PHY_{uuid}"

    Returns:
        Dict mapping source_id -> canonical_id
    """
    mapping: dict[str, str] = {}

    for cluster in clusters:
        canonical_id = _generate_canonical_id(G, cluster)

        for source_id in cluster:
            mapping[source_id] = canonical_id

    logger.info(f"Assigned canonical IDs to {len(clusters)} clusters")

    return mapping


def _generate_canonical_id(G: nx.Graph, cluster: set[str]) -> str:
    """Generate canonical ID for a cluster."""
    # Collect all NPIs in cluster
    npis = []
    for node in cluster:
        npi = G.nodes[node].get("npi")
        if npi and len(npi) == 10 and npi.isdigit():
            npis.append(npi)

    if npis:
        # Use most common NPI
        npi_counts = Counter(npis)
        most_common_npi = npi_counts.most_common(1)[0][0]
        return f"PHY_{most_common_npi}"
    else:
        # Generate UUID
        return f"PHY_{uuid.uuid4().hex[:12]}"


def get_canonical_id_stats(mapping: dict[str, str]) -> dict:
    """Get statistics about canonical ID assignment."""
    canonical_ids = set(mapping.values())
    npi_based = sum(1 for cid in canonical_ids if not cid.startswith("PHY_") or len(cid) == 14)
    uuid_based = len(canonical_ids) - npi_based

    # Actually check properly
    npi_based = sum(1 for cid in canonical_ids if len(cid) == 14 and cid[4:].isdigit())
    uuid_based = len(canonical_ids) - npi_based

    return {
        "total_canonical_ids": len(canonical_ids),
        "npi_based_ids": npi_based,
        "uuid_based_ids": uuid_based,
        "total_source_records": len(mapping),
        "avg_records_per_entity": len(mapping) / len(canonical_ids) if canonical_ids else 0,
    }
