"""Build referral network from claims data."""

from collections import defaultdict

import networkx as nx
import pandas as pd

from ..logging import get_logger

logger = get_logger("network.referrals")


def build_referral_graph(
    referrals_df: pd.DataFrame,
    canonical_mapping: dict[str, str],
) -> nx.DiGraph:
    """
    Build directed graph of referral relationships.

    Nodes: canonical_physician_id
    Edges: referral relationships
    Edge attributes:
        - referral_count: number of patients referred
        - last_referral_date: most recent referral

    Args:
        referrals_df: DataFrame with referring_npi, receiving_npi columns
        canonical_mapping: Dict mapping NPI -> canonical_id

    Returns:
        Directed graph of referral relationships
    """
    G = nx.DiGraph()

    # Aggregate referrals
    referral_counts: dict[tuple[str, str], int] = defaultdict(int)
    referral_dates: dict[tuple[str, str], str] = {}

    for _, row in referrals_df.iterrows():
        referring_npi = row.get("referring_npi")
        receiving_npi = row.get("receiving_npi")
        referral_date = row.get("referral_date", "")

        # Skip if NPIs are missing or invalid
        if not referring_npi or not receiving_npi:
            continue
        if pd.isna(referring_npi) or pd.isna(receiving_npi):
            continue

        # Map to canonical IDs
        referring_id = canonical_mapping.get(referring_npi)
        receiving_id = canonical_mapping.get(receiving_npi)

        # Skip if we can't resolve either physician
        if not referring_id or not receiving_id:
            continue

        # Skip self-referrals
        if referring_id == receiving_id:
            continue

        edge_key = (referring_id, receiving_id)
        referral_counts[edge_key] += 1

        # Track most recent date
        if referral_date:
            current_date = referral_dates.get(edge_key, "")
            if referral_date > current_date:
                referral_dates[edge_key] = referral_date

    # Build graph
    for (referring_id, receiving_id), count in referral_counts.items():
        G.add_edge(
            referring_id,
            receiving_id,
            referral_count=count,
            last_referral_date=referral_dates.get((referring_id, receiving_id), ""),
        )

    logger.info(
        f"Built referral graph: {G.number_of_nodes()} physicians, "
        f"{G.number_of_edges()} referral relationships"
    )

    return G


def build_npi_to_canonical_mapping(
    canonical_mapping: dict[str, str],
    records_by_npi: dict[str, str] | None = None,
) -> dict[str, str]:
    """
    Build mapping from NPI to canonical ID.

    If canonical_mapping is source_id -> canonical_id,
    we need to also build npi -> canonical_id.
    """
    # If the mapping is already NPI -> canonical, return as-is
    sample_key = next(iter(canonical_mapping.keys()), "")
    if len(sample_key) == 10 and sample_key.isdigit():
        return canonical_mapping

    # Otherwise, we need the records to build NPI mapping
    logger.warning("canonical_mapping appears to be source_id based, not NPI based")
    return canonical_mapping


def get_referral_stats(G: nx.DiGraph) -> dict:
    """Get summary statistics for the referral network."""
    if G.number_of_nodes() == 0:
        return {"error": "Empty graph"}

    in_degrees = dict(G.in_degree())
    out_degrees = dict(G.out_degree())

    # Referral volumes
    volumes = [d.get("referral_count", 0) for _, _, d in G.edges(data=True)]

    return {
        "num_physicians": G.number_of_nodes(),
        "num_relationships": G.number_of_edges(),
        "total_referrals": sum(volumes),
        "avg_referrals_per_edge": sum(volumes) / len(volumes) if volumes else 0,
        "max_in_degree": max(in_degrees.values()) if in_degrees else 0,
        "max_out_degree": max(out_degrees.values()) if out_degrees else 0,
        "avg_in_degree": sum(in_degrees.values()) / len(in_degrees) if in_degrees else 0,
        "avg_out_degree": sum(out_degrees.values()) / len(out_degrees) if out_degrees else 0,
    }


def get_top_referrers(G: nx.DiGraph, n: int = 10) -> list[tuple[str, int]]:
    """Get physicians with highest outgoing referral counts."""
    out_volumes: dict[str, int] = defaultdict(int)

    for u, v, data in G.edges(data=True):
        out_volumes[u] += data.get("referral_count", 1)

    sorted_referrers = sorted(out_volumes.items(), key=lambda x: x[1], reverse=True)
    return sorted_referrers[:n]


def get_top_receivers(G: nx.DiGraph, n: int = 10) -> list[tuple[str, int]]:
    """Get physicians with highest incoming referral counts."""
    in_volumes: dict[str, int] = defaultdict(int)

    for u, v, data in G.edges(data=True):
        in_volumes[v] += data.get("referral_count", 1)

    sorted_receivers = sorted(in_volumes.items(), key=lambda x: x[1], reverse=True)
    return sorted_receivers[:n]
