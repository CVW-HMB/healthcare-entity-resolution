"""Network visualization components using Pyvis."""

import tempfile

import streamlit as st
import streamlit.components.v1 as components


def render_network_pyvis(
    nodes: list[dict],
    edges: list[dict],
    height: int = 600,
    physics: bool = True,
) -> None:
    """
    Render a network graph using Pyvis.

    Args:
        nodes: List of dicts with 'id', 'label', 'size', 'color', 'title' keys
        edges: List of dicts with 'from', 'to', 'weight', 'title' keys
        height: Height in pixels
        physics: Enable physics simulation
    """
    try:
        from pyvis.network import Network
    except ImportError:
        st.error("Pyvis not installed. Run: pip install pyvis")
        return

    # Create network
    net = Network(
        height=f"{height}px",
        width="100%",
        bgcolor="#ffffff",
        font_color="#333333",
    )

    # Configure physics
    if physics:
        net.barnes_hut(
            gravity=-2000,
            central_gravity=0.3,
            spring_length=100,
            spring_strength=0.01,
        )
    else:
        net.toggle_physics(False)

    # Add nodes
    for node in nodes:
        net.add_node(
            node["id"],
            label=node.get("label", str(node["id"])),
            size=node.get("size", 10),
            color=node.get("color", "#97c2fc"),
            title=node.get("title", ""),
        )

    # Add edges
    for edge in edges:
        net.add_edge(
            edge["from"],
            edge["to"],
            weight=edge.get("weight", 1),
            title=edge.get("title", ""),
        )

    # Save to temp file and render
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as f:
        net.save_graph(f.name)
        with open(f.name) as html_file:
            html_content = html_file.read()
            components.html(html_content, height=height + 50)


def render_ego_network(
    center_id: str,
    center_label: str,
    neighbors: list[dict],
    height: int = 500,
) -> None:
    """
    Render an ego network (single node + its connections).

    Args:
        center_id: ID of the center node
        center_label: Label for center node
        neighbors: List of dicts with 'id', 'label', 'relationship', 'weight' keys
        height: Height in pixels
    """
    nodes = [
        {
            "id": center_id,
            "label": center_label,
            "size": 30,
            "color": "#ff6b6b",
            "title": "Selected physician",
        }
    ]

    edges = []

    for neighbor in neighbors:
        nodes.append(
            {
                "id": neighbor["id"],
                "label": neighbor.get("label", str(neighbor["id"])),
                "size": 15 + neighbor.get("weight", 1) * 2,
                "color": _get_relationship_color(neighbor.get("relationship", "unknown")),
                "title": f"Relationship: {neighbor.get('relationship', 'unknown')}",
            }
        )

        edges.append(
            {
                "from": center_id,
                "to": neighbor["id"],
                "weight": neighbor.get("weight", 1),
                "title": f"Weight: {neighbor.get('weight', 1)}",
            }
        )

    render_network_pyvis(nodes, edges, height=height)


def _get_relationship_color(relationship: str) -> str:
    """Get color based on relationship type."""
    colors = {
        "referral_in": "#4ecdc4",
        "referral_out": "#45b7d1",
        "colleague": "#96ceb4",
        "unknown": "#97c2fc",
    }
    return colors.get(relationship, "#97c2fc")


def create_influence_network(
    physicians_df,
    influence_scores: dict,
    top_n: int = 30,
) -> tuple[list[dict], list[dict]]:
    """
    Create nodes and edges for influence network visualization.

    Args:
        physicians_df: DataFrame with physician info
        influence_scores: Dict of canonical_id -> influence score
        top_n: Number of top physicians to include

    Returns:
        (nodes, edges) tuple
    """
    # Get top physicians by influence
    sorted_scores = sorted(influence_scores.items(), key=lambda x: x[1], reverse=True)
    top_physicians = sorted_scores[:top_n]

    nodes = []
    for phys_id, score in top_physicians:
        phys_data = physicians_df[physicians_df["canonical_id"] == phys_id]
        if len(phys_data) > 0:
            phys = phys_data.iloc[0]
            nodes.append(
                {
                    "id": phys_id,
                    "label": str(phys.get("name", phys_id))[:20],
                    "size": 10 + score * 1000,
                    "color": _get_specialty_color(phys.get("specialty", "")),
                    "title": f"{phys.get('name', 'Unknown')}\n{phys.get('specialty', 'Unknown')}\nInfluence: {score:.6f}",
                }
            )

    # For edges, we'd need the actual referral data
    # This is a placeholder - real implementation would load referral graph
    edges = []

    return nodes, edges


def _get_specialty_color(specialty: str) -> str:
    """Get color based on specialty."""
    if not specialty:
        return "#97c2fc"

    specialty = specialty.upper()

    if "CARDIO" in specialty:
        return "#ff6b6b"
    elif "SURGERY" in specialty or "ORTHO" in specialty:
        return "#4ecdc4"
    elif "MEDICINE" in specialty or "INTERNAL" in specialty:
        return "#45b7d1"
    elif "PEDIATRIC" in specialty:
        return "#96ceb4"
    elif "ONCOLOGY" in specialty:
        return "#dda0dd"
    else:
        return "#97c2fc"
