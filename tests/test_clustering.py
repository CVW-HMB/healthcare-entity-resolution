"""Tests for graph clustering."""

import networkx as nx

from physician_resolution.graph.builder import build_identity_graph
from physician_resolution.graph.clustering import (
    assign_cluster_ids,
    find_clusters,
    get_cluster_for_node,
    get_cluster_sizes,
    get_cluster_subgraph,
)
from physician_resolution.graph.pruning import (
    prune_low_confidence_edges,
    prune_npi_conflicts,
)
from physician_resolution.graph.quality import assess_cluster_quality


class TestBuildIdentityGraph:
    """Tests for graph building."""

    def test_builds_graph_with_nodes(self, sample_records, sample_matches):
        """Test graph has correct number of nodes."""
        G = build_identity_graph(sample_records, sample_matches)
        assert G.number_of_nodes() == len(sample_records)

    def test_builds_graph_with_edges(self, sample_records, sample_matches):
        """Test graph has correct number of edges."""
        G = build_identity_graph(sample_records, sample_matches)
        assert G.number_of_edges() == len(sample_matches)

    def test_node_attributes(self, sample_records, sample_matches):
        """Test nodes have correct attributes."""
        G = build_identity_graph(sample_records, sample_matches)
        node = G.nodes["cms_001"]
        assert node["source"] == "cms"
        assert node["npi"] == "1234567890"

    def test_edge_weights(self, sample_records, sample_matches):
        """Test edges have correct weights."""
        G = build_identity_graph(sample_records, sample_matches)
        weight = G["cms_001"]["lic_001"]["weight"]
        assert weight == 0.92


class TestFindClusters:
    """Tests for cluster detection."""

    def test_finds_correct_clusters(self, sample_records, sample_matches):
        """Test correct number of clusters found."""
        G = build_identity_graph(sample_records, sample_matches)
        clusters = find_clusters(G)
        # Should have 2 clusters: Smith (3 records) and Jones (2 records)
        assert len(clusters) == 2

    def test_cluster_sizes(self, sample_records, sample_matches):
        """Test cluster sizes are correct."""
        G = build_identity_graph(sample_records, sample_matches)
        clusters = find_clusters(G)
        sizes = sorted([len(c) for c in clusters], reverse=True)
        assert sizes == [3, 2]

    def test_empty_graph(self):
        """Test empty graph returns no clusters."""
        G = nx.Graph()
        clusters = find_clusters(G)
        assert len(clusters) == 0

    def test_isolated_nodes(self):
        """Test isolated nodes form singleton clusters."""
        G = nx.Graph()
        G.add_node("a")
        G.add_node("b")
        G.add_node("c")
        clusters = find_clusters(G)
        assert len(clusters) == 3
        assert all(len(c) == 1 for c in clusters)


class TestGetClusterSubgraph:
    """Tests for cluster subgraph extraction."""

    def test_subgraph_has_correct_nodes(self, sample_records, sample_matches):
        """Test subgraph contains correct nodes."""
        G = build_identity_graph(sample_records, sample_matches)
        clusters = find_clusters(G)

        for cluster in clusters:
            subgraph = get_cluster_subgraph(G, cluster)
            assert set(subgraph.nodes()) == cluster


class TestGetClusterForNode:
    """Tests for finding cluster by node."""

    def test_finds_correct_cluster(self, sample_records, sample_matches):
        """Test finds correct cluster for node."""
        G = build_identity_graph(sample_records, sample_matches)
        cluster = get_cluster_for_node(G, "cms_001")
        assert "cms_001" in cluster
        assert "lic_001" in cluster
        assert "hosp_001" in cluster

    def test_returns_none_for_missing_node(self, sample_records, sample_matches):
        """Test returns None for non-existent node."""
        G = build_identity_graph(sample_records, sample_matches)
        cluster = get_cluster_for_node(G, "nonexistent")
        assert cluster is None


class TestGetClusterSizes:
    """Tests for cluster size analysis."""

    def test_size_distribution(self, sample_records, sample_matches):
        """Test size distribution is calculated."""
        G = build_identity_graph(sample_records, sample_matches)
        clusters = find_clusters(G)
        sizes = get_cluster_sizes(clusters)

        assert sizes["total_clusters"] == 2
        assert sizes["pair_count"] == 1
        assert sizes["small_count"] == 1


class TestAssignClusterIds:
    """Tests for cluster ID assignment."""

    def test_assigns_ids_to_all_nodes(self, sample_records, sample_matches):
        """Test all nodes get cluster IDs."""
        G = build_identity_graph(sample_records, sample_matches)
        clusters = find_clusters(G)
        mapping = assign_cluster_ids(clusters)

        assert len(mapping) == len(sample_records)

    def test_same_cluster_same_id(self, sample_records, sample_matches):
        """Test nodes in same cluster get same ID."""
        G = build_identity_graph(sample_records, sample_matches)
        clusters = find_clusters(G)
        mapping = assign_cluster_ids(clusters)

        # Smith records should have same ID
        assert mapping["cms_001"] == mapping["lic_001"]
        assert mapping["cms_001"] == mapping["hosp_001"]

    def test_different_clusters_different_ids(self, sample_records, sample_matches):
        """Test nodes in different clusters get different IDs."""
        G = build_identity_graph(sample_records, sample_matches)
        clusters = find_clusters(G)
        mapping = assign_cluster_ids(clusters)

        # Smith and Jones should have different IDs
        assert mapping["cms_001"] != mapping["cms_002"]


class TestAssessClusterQuality:
    """Tests for cluster quality assessment."""

    def test_quality_score_in_range(self, sample_records, sample_matches):
        """Test quality score is between 0 and 1."""
        G = build_identity_graph(sample_records, sample_matches)
        clusters = find_clusters(G)

        for cluster in clusters:
            quality = assess_cluster_quality(G, cluster)
            assert 0 <= quality.quality_score <= 1

    def test_npi_conflict_detected(self):
        """Test NPI conflict is detected."""
        from physician_resolution.schemas.records import PhysicianRecord

        records = [
            PhysicianRecord(source="cms", source_id="a", npi="111", name_last="Smith"),
            PhysicianRecord(source="cms", source_id="b", npi="222", name_last="Smith"),
        ]
        matches = [("a", "b", 0.9)]

        G = build_identity_graph(records, matches)
        clusters = find_clusters(G)
        quality = assess_cluster_quality(G, clusters[0])

        assert quality.npi_conflict is True
        assert quality.quality_score < 0.5


class TestPruneLowConfidenceEdges:
    """Tests for edge pruning."""

    def test_removes_low_weight_edges(self):
        """Test low weight edges are removed."""
        G = nx.Graph()
        G.add_edge("a", "b", weight=0.8)
        G.add_edge("b", "c", weight=0.2)

        G = prune_low_confidence_edges(G, threshold=0.5)

        assert G.has_edge("a", "b")
        assert not G.has_edge("b", "c")

    def test_preserves_high_weight_edges(self):
        """Test high weight edges are preserved."""
        G = nx.Graph()
        G.add_edge("a", "b", weight=0.9)
        G.add_edge("b", "c", weight=0.85)

        G = prune_low_confidence_edges(G, threshold=0.5)

        assert G.number_of_edges() == 2


class TestPruneNPIConflicts:
    """Tests for NPI conflict resolution."""

    def test_resolves_npi_conflicts(self):
        """Test NPI conflicts are resolved by removing edges."""
        G = nx.Graph()
        G.add_node("a", npi="111")
        G.add_node("b", npi="222")
        G.add_node("c", npi="111")
        G.add_edge("a", "b", weight=0.5)
        G.add_edge("a", "c", weight=0.9)

        G = prune_npi_conflicts(G)

        # Should still have a-c edge (same NPI), not a-b
        clusters = find_clusters(G)
        for cluster in clusters:
            npis = set(G.nodes[n].get("npi") for n in cluster if G.nodes[n].get("npi"))
            assert len(npis) <= 1
