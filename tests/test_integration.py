"""Integration tests for the full pipeline."""

from physician_resolution.canonicalization import assign_canonical_ids, merge_all_clusters
from physician_resolution.config import PipelineConfig
from physician_resolution.graph import build_identity_graph, find_clusters, full_pruning_pipeline
from physician_resolution.matching import find_matches, get_confirmed_matches


class TestETLIntegration:
    """Integration tests for ETL pipeline."""

    def test_normalize_all_sources(self, sample_records):
        """Test that normalization produces valid records."""
        for record in sample_records:
            assert record.source is not None
            assert record.source_id is not None
            assert record.name_last is not None

    def test_records_have_required_fields(self, sample_records):
        """Test all records have required fields for matching."""
        for record in sample_records:
            # Must have source info
            assert record.source in ["cms", "license", "hospital", "publication"]
            # Must have name
            assert record.name_last


class TestMatchingIntegration:
    """Integration tests for matching pipeline."""

    def test_find_matches_returns_results(self, sample_records):
        """Test matching produces results."""
        config = PipelineConfig(match_threshold=0.7)
        results = find_matches(sample_records, config)
        assert len(results) > 0

    def test_npi_matches_are_high_confidence(self, sample_records):
        """Test NPI matches have high confidence."""
        config = PipelineConfig()
        results = find_matches(sample_records, config)

        for result in results:
            if result.scores.npi_match == 1.0:
                assert result.scores.overall_score >= 0.9

    def test_npi_conflicts_are_non_matches(self, sample_records):
        """Test NPI conflicts result in non-matches."""
        from physician_resolution.schemas.matches import MatchDecision

        config = PipelineConfig()
        results = find_matches(sample_records, config)

        for result in results:
            if result.scores.npi_match == 0.0:
                assert result.decision == MatchDecision.NON_MATCH


class TestGraphIntegration:
    """Integration tests for graph pipeline."""

    def test_full_graph_pipeline(self, sample_records, sample_matches):
        """Test full graph pipeline produces valid clusters."""
        # Build graph
        G = build_identity_graph(sample_records, sample_matches)
        assert G.number_of_nodes() == len(sample_records)

        # Prune
        G = full_pruning_pipeline(G, min_edge_weight=0.3)

        # Find clusters
        clusters = find_clusters(G)
        assert len(clusters) > 0

        # All nodes should be in exactly one cluster
        all_nodes = set()
        for cluster in clusters:
            for node in cluster:
                assert node not in all_nodes
                all_nodes.add(node)

    def test_pruning_removes_weak_edges(self, sample_records):
        """Test pruning removes weak edges."""
        # Create matches with varying confidence
        matches = [
            ("cms_001", "lic_001", 0.9),
            ("lic_001", "hosp_001", 0.2),  # Weak edge
        ]

        G = build_identity_graph(sample_records[:3], matches)
        initial_edges = G.number_of_edges()

        G = full_pruning_pipeline(G, min_edge_weight=0.5)

        assert G.number_of_edges() < initial_edges


class TestCanonicalizationIntegration:
    """Integration tests for canonicalization."""

    def test_assign_canonical_ids(self, sample_records, sample_matches):
        """Test canonical ID assignment."""
        G = build_identity_graph(sample_records, sample_matches)
        clusters = find_clusters(G)

        mapping = assign_canonical_ids(G, clusters)

        # All records should have canonical IDs
        assert len(mapping) == len(sample_records)

        # IDs should be properly formatted
        for source_id, canonical_id in mapping.items():
            assert canonical_id.startswith("PHY_")

    def test_merge_clusters(self, sample_records, sample_matches):
        """Test cluster merging produces valid physicians."""
        G = build_identity_graph(sample_records, sample_matches)
        clusters = find_clusters(G)

        physicians = merge_all_clusters(G, clusters)

        assert len(physicians) == len(clusters)

        for phys in physicians:
            assert phys.canonical_id is not None
            assert 0 <= phys.confidence <= 1
            assert phys.source_count > 0


class TestEndToEndPipeline:
    """End-to-end pipeline tests."""

    def test_mini_pipeline(self, sample_records):
        """Test complete mini pipeline."""
        config = PipelineConfig(
            match_threshold=0.7,
            non_match_threshold=0.3,
            min_edge_weight=0.3,
        )

        # Step 1: Match
        match_results = find_matches(sample_records, config)
        matches = get_confirmed_matches(match_results)

        # Step 2: Build graph
        G = build_identity_graph(sample_records, matches)

        # Step 3: Prune
        G = full_pruning_pipeline(G, min_edge_weight=config.min_edge_weight)

        # Step 4: Cluster
        clusters = find_clusters(G)

        # Step 5: Canonicalize
        canonical_mapping = assign_canonical_ids(G, clusters)
        physicians = merge_all_clusters(G, clusters)

        # Assertions
        assert len(physicians) > 0
        assert len(canonical_mapping) == len(sample_records)

        # Each cluster should have consistent data
        for phys in physicians:
            assert phys.canonical_id.startswith("PHY_")

    def test_pipeline_with_npi_conflicts(self):
        """Test pipeline handles NPI conflicts correctly."""
        from physician_resolution.schemas.records import PhysicianRecord

        # Create records that would match on name but have different NPIs
        records = [
            PhysicianRecord(
                source="cms",
                source_id="a",
                npi="1111111111",
                name_last="SMITH",
                name_first="JOHN",
                facility_state="MA",
            ),
            PhysicianRecord(
                source="cms",
                source_id="b",
                npi="2222222222",
                name_last="SMITH",
                name_first="JOHN",
                facility_state="MA",
            ),
        ]

        config = PipelineConfig(match_threshold=0.5)
        match_results = find_matches(records, config)

        # Should not match due to NPI conflict
        matches = get_confirmed_matches(match_results)

        # Build and process graph
        G = build_identity_graph(records, matches)
        G = full_pruning_pipeline(G)
        clusters = find_clusters(G)

        # Should be 2 separate clusters
        assert len(clusters) == 2

    def test_pipeline_merges_same_physician(self):
        """Test pipeline correctly merges same physician records."""
        from physician_resolution.schemas.records import PhysicianRecord

        # Create records for same physician
        records = [
            PhysicianRecord(
                source="cms",
                source_id="a",
                npi="1234567890",
                name_last="SMITH",
                name_first="JOHN",
                specialty="Internal Medicine",
                facility_state="MA",
            ),
            PhysicianRecord(
                source="license",
                source_id="b",
                npi=None,
                name_last="Smith",
                name_first="John",
                specialty="Internal Med",
                facility_state="MA",
            ),
            PhysicianRecord(
                source="hospital",
                source_id="c",
                npi="1234567890",
                name_last="Smith",
                name_first="John",
                specialty="Internal Medicine",
                facility_state="MA",
            ),
        ]

        config = PipelineConfig(match_threshold=0.7)
        match_results = find_matches(records, config)
        matches = get_confirmed_matches(match_results)

        G = build_identity_graph(records, matches)
        clusters = find_clusters(G)
        physicians = merge_all_clusters(G, clusters)

        # Should be 1 cluster/physician
        assert len(physicians) == 1
        assert physicians[0].source_count == 3
        assert physicians[0].npi == "1234567890"
