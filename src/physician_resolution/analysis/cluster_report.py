"""Cluster analysis and reporting."""

from collections import Counter

import networkx as nx

from ..graph.quality import assess_cluster_quality, get_quality_summary
from ..logging import get_logger
from ..schemas.entities import CanonicalPhysician

logger = get_logger("analysis.cluster_report")


def analyze_cluster_sizes(clusters: list[set[str]]) -> dict:
    """Analyze distribution of cluster sizes."""
    if not clusters:
        return {"error": "No clusters provided"}

    sizes = [len(c) for c in clusters]
    size_counts = Counter(sizes)

    return {
        "total_clusters": len(clusters),
        "total_records": sum(sizes),
        "size_stats": {
            "min": min(sizes),
            "max": max(sizes),
            "mean": sum(sizes) / len(sizes),
            "median": sorted(sizes)[len(sizes) // 2],
        },
        "size_distribution": {
            "singletons (1)": size_counts.get(1, 0),
            "pairs (2)": size_counts.get(2, 0),
            "small (3-5)": sum(size_counts.get(s, 0) for s in range(3, 6)),
            "medium (6-10)": sum(size_counts.get(s, 0) for s in range(6, 11)),
            "large (11-20)": sum(size_counts.get(s, 0) for s in range(11, 21)),
            "very_large (>20)": sum(v for k, v in size_counts.items() if k > 20),
        },
        "detailed_distribution": dict(sorted(size_counts.items())),
    }


def analyze_cluster_quality(
    G: nx.Graph,
    clusters: list[set[str]],
) -> dict:
    """Analyze quality metrics across all clusters."""
    qualities = []

    for idx, cluster in enumerate(clusters):
        quality = assess_cluster_quality(G, cluster, f"CLUSTER_{idx:05d}")
        qualities.append(quality)

    summary = get_quality_summary(qualities)

    # Additional analysis
    problematic = [q for q in qualities if q.has_issues()]
    npi_conflicts = [q for q in qualities if q.npi_conflict]

    summary["problematic_clusters"] = len(problematic)
    summary["npi_conflict_clusters"] = len(npi_conflicts)

    # Sample problematic clusters for review
    summary["sample_issues"] = [
        {
            "cluster_id": q.cluster_id,
            "size": q.size,
            "quality_score": q.quality_score,
            "warnings": q.warnings,
        }
        for q in problematic[:10]
    ]

    return summary


def analyze_source_coverage(
    G: nx.Graph,
    clusters: list[set[str]],
) -> dict:
    """Analyze how well clusters span multiple sources."""
    source_coverage: dict[int, int] = Counter()

    for cluster in clusters:
        sources = set()
        for node in cluster:
            source = G.nodes[node].get("source")
            if source:
                sources.add(source)
        source_coverage[len(sources)] += 1

    return {
        "source_coverage_distribution": {
            f"{k}_sources": v for k, v in sorted(source_coverage.items())
        },
        "multi_source_clusters": sum(v for k, v in source_coverage.items() if k > 1),
        "single_source_clusters": source_coverage.get(1, 0),
    }


def analyze_canonical_physicians(physicians: list[CanonicalPhysician]) -> dict:
    """Analyze the final canonical physician entities."""
    if not physicians:
        return {"error": "No physicians provided"}

    total = len(physicians)

    # NPI coverage
    with_npi = sum(1 for p in physicians if p.npi)

    # Confidence distribution
    confidences = [p.confidence for p in physicians]
    high_conf = sum(1 for c in confidences if c >= 0.8)
    med_conf = sum(1 for c in confidences if 0.5 <= c < 0.8)
    low_conf = sum(1 for c in confidences if c < 0.5)

    # Source record counts
    source_counts = [p.source_count for p in physicians]

    # State distribution
    states = Counter(p.state for p in physicians if p.state)

    # Specialty distribution
    specialties = Counter(p.specialty for p in physicians if p.specialty)

    return {
        "total_physicians": total,
        "npi_coverage": with_npi / total if total else 0,
        "confidence_distribution": {
            "high (>=0.8)": high_conf,
            "medium (0.5-0.8)": med_conf,
            "low (<0.5)": low_conf,
        },
        "confidence_stats": {
            "min": min(confidences),
            "max": max(confidences),
            "mean": sum(confidences) / len(confidences),
        },
        "source_record_stats": {
            "min": min(source_counts),
            "max": max(source_counts),
            "mean": sum(source_counts) / len(source_counts),
        },
        "top_states": dict(states.most_common(10)),
        "top_specialties": dict(specialties.most_common(10)),
    }


def generate_cluster_report(
    G: nx.Graph,
    clusters: list[set[str]],
    canonical_physicians: list[CanonicalPhysician] | None = None,
) -> dict:
    """Generate comprehensive cluster analysis report."""
    report = {
        "size_analysis": analyze_cluster_sizes(clusters),
        "quality_analysis": analyze_cluster_quality(G, clusters),
        "source_coverage": analyze_source_coverage(G, clusters),
    }

    if canonical_physicians:
        report["physician_analysis"] = analyze_canonical_physicians(canonical_physicians)

    logger.info(f"Generated cluster report for {len(clusters)} clusters")

    return report
