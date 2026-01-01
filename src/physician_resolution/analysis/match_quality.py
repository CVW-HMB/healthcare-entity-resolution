"""Match quality analysis."""

from collections import Counter

from ..logging import get_logger
from ..schemas.matches import MatchDecision, MatchResult

logger = get_logger("analysis.match_quality")


def analyze_match_results(results: list[MatchResult]) -> dict:
    """Analyze match classification results."""
    if not results:
        return {"error": "No match results provided"}

    total = len(results)

    # Decision counts
    decision_counts = Counter(r.decision for r in results)

    # Match type breakdown
    match_type_counts = Counter(r.match_type for r in results if r.decision == MatchDecision.MATCH)

    # Score distributions
    match_scores = [r.scores.overall_score for r in results if r.decision == MatchDecision.MATCH]
    non_match_scores = [
        r.scores.overall_score for r in results if r.decision == MatchDecision.NON_MATCH
    ]
    uncertain_scores = [
        r.scores.overall_score for r in results if r.decision == MatchDecision.UNCERTAIN
    ]

    report = {
        "total_comparisons": total,
        "decisions": {
            "match": decision_counts.get(MatchDecision.MATCH, 0),
            "non_match": decision_counts.get(MatchDecision.NON_MATCH, 0),
            "uncertain": decision_counts.get(MatchDecision.UNCERTAIN, 0),
        },
        "match_rate": decision_counts.get(MatchDecision.MATCH, 0) / total if total else 0,
        "match_types": dict(match_type_counts),
        "score_stats": {
            "match": _score_stats(match_scores),
            "non_match": _score_stats(non_match_scores),
            "uncertain": _score_stats(uncertain_scores),
        },
    }

    return report


def _score_stats(scores: list[float]) -> dict:
    """Calculate statistics for a list of scores."""
    if not scores:
        return {"count": 0}

    return {
        "count": len(scores),
        "min": min(scores),
        "max": max(scores),
        "mean": sum(scores) / len(scores),
        "median": sorted(scores)[len(scores) // 2],
    }


def analyze_match_confidence(results: list[MatchResult]) -> dict:
    """Analyze confidence levels of matches."""
    matches = [r for r in results if r.decision == MatchDecision.MATCH]

    if not matches:
        return {"error": "No matches found"}

    confidences = [r.confidence for r in matches]

    # Bucket by confidence
    high_conf = sum(1 for c in confidences if c >= 0.9)
    med_conf = sum(1 for c in confidences if 0.7 <= c < 0.9)
    low_conf = sum(1 for c in confidences if c < 0.7)

    return {
        "total_matches": len(matches),
        "confidence_distribution": {
            "high (>=0.9)": high_conf,
            "medium (0.7-0.9)": med_conf,
            "low (<0.7)": low_conf,
        },
        "confidence_stats": _score_stats(confidences),
    }


def analyze_npi_matches(results: list[MatchResult]) -> dict:
    """Analyze matches involving NPI comparisons."""
    npi_exact = []
    npi_conflict = []
    npi_missing = []

    for r in results:
        if r.scores.npi_match == 1.0:
            npi_exact.append(r)
        elif r.scores.npi_match == 0.0:
            npi_conflict.append(r)
        else:
            npi_missing.append(r)

    return {
        "npi_exact_matches": len(npi_exact),
        "npi_conflicts": len(npi_conflict),
        "npi_unavailable": len(npi_missing),
        "npi_match_rate": len(npi_exact) / len(results) if results else 0,
    }


def get_low_confidence_matches(
    results: list[MatchResult],
    threshold: float = 0.7,
    limit: int = 20,
) -> list[dict]:
    """Get matches with low confidence for review."""
    low_conf = [
        r for r in results if r.decision == MatchDecision.MATCH and r.confidence < threshold
    ]

    # Sort by confidence (lowest first)
    low_conf.sort(key=lambda r: r.confidence)

    return [
        {
            "source_id_1": r.source_id_1,
            "source_id_2": r.source_id_2,
            "confidence": r.confidence,
            "overall_score": r.scores.overall_score,
            "name_similarity": r.scores.name_similarity,
            "match_type": r.match_type,
        }
        for r in low_conf[:limit]
    ]


def generate_match_quality_report(results: list[MatchResult]) -> dict:
    """Generate comprehensive match quality report."""
    report = {
        "summary": analyze_match_results(results),
        "confidence_analysis": analyze_match_confidence(results),
        "npi_analysis": analyze_npi_matches(results),
        "low_confidence_matches": get_low_confidence_matches(results),
    }

    logger.info(f"Generated match quality report for {len(results)} comparisons")

    return report
