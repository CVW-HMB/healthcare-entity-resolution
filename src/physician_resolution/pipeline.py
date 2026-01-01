"""Main pipeline orchestrating the entity resolution process."""

import json
from pathlib import Path

from .analysis import (
    generate_cluster_report,
    generate_data_quality_report,
    generate_match_quality_report,
)
from .canonicalization import assign_canonical_ids, merge_all_clusters
from .config import PipelineConfig, get_run_output_dir
from .etl import load_all_sources, normalize_all
from .graph import build_identity_graph, find_clusters, full_pruning_pipeline
from .logging import get_logger, setup_logging
from .matching import find_matches, get_confirmed_matches
from .network import build_referral_graph, calculate_influence_scores
from .schemas.entities import CanonicalPhysician

logger = get_logger("pipeline")


def run_pipeline(
    data_dir: Path | str,
    output_dir: Path | str | None = None,
    config: PipelineConfig | None = None,
) -> dict:
    """
    Run the complete entity resolution pipeline.

    Steps:
    1. Load source data
    2. Normalize schemas
    3. Run matching
    4. Build identity graph
    5. Prune and clean
    6. Detect clusters
    7. Canonicalize
    8. Build referral network
    9. Generate reports
    10. Export results

    Args:
        data_dir: Directory containing source CSV files
        output_dir: Directory for outputs (default: timestamped in outputs/runs/)
        config: Pipeline configuration

    Returns:
        Dict with pipeline results and metrics
    """
    setup_logging()
    config = config or PipelineConfig()
    data_dir = Path(data_dir)
    output_dir = Path(output_dir) if output_dir else get_run_output_dir()

    logger.info("=" * 60)
    logger.info("Starting Entity Resolution Pipeline")
    logger.info("=" * 60)

    results = {
        "status": "running",
        "output_dir": str(output_dir),
    }

    # Step 1: Load data
    logger.info("Step 1: Loading source data...")
    sources = load_all_sources(data_dir)
    results["source_counts"] = {k: len(v) for k, v in sources.items()}

    # Step 2: Normalize
    logger.info("Step 2: Normalizing records...")
    records = normalize_all(sources)
    results["total_records"] = len(records)

    # Step 3: Match
    logger.info("Step 3: Finding matches...")
    match_results = find_matches(records, config)
    matches = get_confirmed_matches(
        match_results, include_uncertain=config.include_uncertain_matches
    )
    results["match_count"] = len(matches)

    # Step 4: Build graph
    logger.info("Step 4: Building identity graph...")
    G = build_identity_graph(records, matches)
    results["graph_nodes"] = G.number_of_nodes()
    results["graph_edges"] = G.number_of_edges()

    # Step 5: Prune
    logger.info("Step 5: Pruning graph...")
    G = full_pruning_pipeline(
        G,
        min_edge_weight=config.min_edge_weight,
        max_cluster_size=config.max_cluster_size,
        prune_conflicts=config.prune_npi_conflicts,
    )
    results["pruned_edges"] = G.number_of_edges()

    # Step 6: Cluster
    logger.info("Step 6: Detecting clusters...")
    clusters = find_clusters(G)
    results["cluster_count"] = len(clusters)

    # Step 7: Canonicalize
    logger.info("Step 7: Canonicalizing entities...")
    canonical_mapping = assign_canonical_ids(G, clusters)
    canonical_physicians = merge_all_clusters(G, clusters)
    results["canonical_physician_count"] = len(canonical_physicians)

    # Step 8: Referral network
    logger.info("Step 8: Building referral network...")
    referrals_df = sources.get("referral")
    if referrals_df is not None and not referrals_df.empty:
        # Build NPI to canonical mapping
        npi_to_canonical = {}
        for record in records:
            if record.npi and record.source_id in canonical_mapping:
                npi_to_canonical[record.npi] = canonical_mapping[record.source_id]

        referral_graph = build_referral_graph(referrals_df, npi_to_canonical)
        influence_scores = calculate_influence_scores(referral_graph)
        results["referral_edges"] = referral_graph.number_of_edges()
    else:
        referral_graph = None
        influence_scores = {}
        results["referral_edges"] = 0

    # Step 9: Generate reports
    logger.info("Step 9: Generating reports...")
    reports = {
        "data_quality": generate_data_quality_report(records, sources),
        "match_quality": generate_match_quality_report(match_results),
        "cluster_report": generate_cluster_report(G, clusters, canonical_physicians),
    }

    # Step 10: Export
    logger.info("Step 10: Exporting results...")
    _export_results(
        output_dir=output_dir,
        canonical_physicians=canonical_physicians,
        canonical_mapping=canonical_mapping,
        influence_scores=influence_scores,
        reports=reports,
    )

    results["status"] = "complete"
    logger.info("=" * 60)
    logger.info("Pipeline complete!")
    logger.info(f"Output directory: {output_dir}")
    logger.info("=" * 60)

    return results


def _export_results(
    output_dir: Path,
    canonical_physicians: list[CanonicalPhysician],
    canonical_mapping: dict[str, str],
    influence_scores: dict[str, float],
    reports: dict,
) -> None:
    """Export all results to files."""
    exports_dir = output_dir / "exports"
    reports_dir = output_dir / "reports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Export canonical physicians
    import csv

    with open(exports_dir / "canonical_physicians.csv", "w", newline="") as f:
        fieldnames = [
            "canonical_id",
            "npi",
            "name",
            "specialty",
            "primary_facility",
            "city",
            "state",
            "confidence",
            "source_count",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for phys in canonical_physicians:
            writer.writerow(
                {
                    "canonical_id": phys.canonical_id,
                    "npi": phys.npi,
                    "name": phys.name,
                    "specialty": phys.specialty,
                    "primary_facility": phys.primary_facility,
                    "city": phys.city,
                    "state": phys.state,
                    "confidence": phys.confidence,
                    "source_count": phys.source_count,
                }
            )

    # Export mapping
    with open(exports_dir / "source_to_canonical_mapping.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["source_id", "canonical_id"])
        for source_id, canonical_id in canonical_mapping.items():
            writer.writerow([source_id, canonical_id])

    # Export influence scores
    if influence_scores:
        with open(exports_dir / "influence_scores.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["canonical_id", "influence_score"])
            for phys_id, score in sorted(
                influence_scores.items(), key=lambda x: x[1], reverse=True
            ):
                writer.writerow([phys_id, score])

    # Export reports
    for report_name, report_data in reports.items():
        with open(reports_dir / f"{report_name}.json", "w") as f:
            json.dump(report_data, f, indent=2, default=str)

    logger.info(f"Exported results to {output_dir}")
