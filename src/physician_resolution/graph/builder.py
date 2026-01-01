"""Build identity graph from match results."""

import networkx as nx

from ..logging import get_logger
from ..schemas.records import PhysicianRecord

logger = get_logger("graph.builder")


def build_identity_graph(
    records: list[PhysicianRecord],
    matches: list[tuple[str, str, float]],
) -> nx.Graph:
    """
    Build identity graph from records and matches.

    Nodes: source_id (unique identifier from each source)
    Edges: match relationships with confidence weights

    Args:
        records: List of normalized physician records
        matches: List of (source_id_1, source_id_2, confidence) tuples

    Returns:
        NetworkX graph with nodes and weighted edges
    """
    G = nx.Graph()

    # Create lookup for records
    record_lookup = {r.source_id: r for r in records}

    # Add nodes with attributes
    for record in records:
        G.add_node(
            record.source_id,
            source=record.source,
            npi=record.npi,
            name_raw=record.name_raw,
            name_first=record.name_first,
            name_last=record.name_last,
            specialty=record.specialty,
            facility_name=record.facility_name,
            facility_state=record.facility_state,
        )

    logger.info(f"Added {G.number_of_nodes()} nodes to graph")

    # Add edges
    for source_id_1, source_id_2, confidence in matches:
        if source_id_1 in G and source_id_2 in G:
            # Determine match type for edge attributes
            rec1 = record_lookup.get(source_id_1)
            rec2 = record_lookup.get(source_id_2)

            match_type = _determine_edge_type(rec1, rec2, confidence)

            G.add_edge(
                source_id_1,
                source_id_2,
                weight=confidence,
                match_type=match_type,
                sources=f"{rec1.source}|{rec2.source}" if rec1 and rec2 else "unknown",
            )

    logger.info(f"Added {G.number_of_edges()} edges to graph")

    return G


def _determine_edge_type(
    rec1: PhysicianRecord | None,
    rec2: PhysicianRecord | None,
    confidence: float,
) -> str:
    """Determine the type of edge based on what matched."""
    if not rec1 or not rec2:
        return "unknown"

    # NPI match
    if rec1.npi and rec2.npi and rec1.npi == rec2.npi:
        return "npi_exact"

    # High confidence name match
    if confidence >= 0.85:
        return "name_strong"

    # Medium confidence
    if confidence >= 0.6:
        return "name_moderate"

    return "weak"


def add_edge_weights(
    G: nx.Graph,
    record_lookup: dict[str, PhysicianRecord],
) -> nx.Graph:
    """
    Recalculate edge weights based on record attributes.

    Weight factors:
    - Match type strength
    - Source reliability
    - Cross-source bonus (matches across different sources are more valuable)
    """
    source_reliability = {
        "cms": 1.0,  # CMS has NPI, most reliable
        "license": 0.9,  # State licenses are authoritative
        "hospital": 0.8,  # Hospital directories vary in quality
        "publication": 0.6,  # Publications have abbreviated names
    }

    for u, v, data in G.edges(data=True):
        rec1 = record_lookup.get(u)
        rec2 = record_lookup.get(v)

        if not rec1 or not rec2:
            continue

        base_weight = data.get("weight", 0.5)

        # Source reliability multiplier
        rel1 = source_reliability.get(rec1.source, 0.5)
        rel2 = source_reliability.get(rec2.source, 0.5)
        source_mult = (rel1 + rel2) / 2

        # Cross-source bonus
        cross_source_mult = 1.1 if rec1.source != rec2.source else 1.0

        # Calculate final weight
        final_weight = base_weight * source_mult * cross_source_mult
        final_weight = min(final_weight, 0.99)  # Cap at 0.99

        G[u][v]["weight"] = final_weight

    return G


def get_graph_stats(G: nx.Graph) -> dict:
    """Get summary statistics for the graph."""
    return {
        "num_nodes": G.number_of_nodes(),
        "num_edges": G.number_of_edges(),
        "num_components": nx.number_connected_components(G),
        "density": nx.density(G),
        "avg_degree": sum(dict(G.degree()).values()) / G.number_of_nodes()
        if G.number_of_nodes() > 0
        else 0,
    }
