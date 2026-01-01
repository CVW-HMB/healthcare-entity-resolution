"""Match classification from similarity scores."""

from ..config import PipelineConfig
from ..logging import get_logger
from ..schemas.matches import MatchDecision, MatchResult, SimilarityScores
from ..schemas.records import PhysicianRecord
from .blocking import get_candidate_pairs
from .similarity import calculate_similarity

logger = get_logger("matching.classifier")


def classify_match(
    scores: SimilarityScores,
    config: PipelineConfig | None = None,
) -> tuple[MatchDecision, float]:
    """
    Classify a pair as match/non-match/uncertain based on similarity scores.

    Returns (decision, confidence).
    """
    config = config or PipelineConfig()

    overall = scores.overall_score

    # NPI conflict is always a non-match
    if scores.npi_match == 0.0:
        return MatchDecision.NON_MATCH, 1.0

    # NPI match is always a match
    if scores.npi_match == 1.0:
        return MatchDecision.MATCH, 0.95

    # Score-based classification
    if overall >= config.match_threshold:
        confidence = min(
            (overall - config.match_threshold) / (1.0 - config.match_threshold) + 0.7, 0.95
        )
        return MatchDecision.MATCH, confidence

    if overall <= config.non_match_threshold:
        confidence = min(
            (config.non_match_threshold - overall) / config.non_match_threshold + 0.7, 0.95
        )
        return MatchDecision.NON_MATCH, confidence

    # Uncertain zone
    # Confidence is lower the closer to the middle
    mid = (config.match_threshold + config.non_match_threshold) / 2
    distance_from_mid = abs(overall - mid)
    confidence = 0.3 + (distance_from_mid * 0.4)

    return MatchDecision.UNCERTAIN, confidence


def determine_match_type(
    record1: PhysicianRecord,
    record2: PhysicianRecord,
    scores: SimilarityScores,
) -> str:
    """Determine the type of match for audit purposes."""
    if scores.npi_match == 1.0:
        return "npi_exact"

    if scores.name_similarity >= 0.9:
        if scores.location_score >= 0.7:
            return "name_location_strong"
        elif scores.specialty_match and scores.specialty_match >= 0.9:
            return "name_specialty"
        else:
            return "name_strong"

    if scores.name_similarity >= 0.7:
        if scores.location_score >= 0.7:
            return "name_location"
        else:
            return "name_moderate"

    return "weak"


def find_matches(
    records: list[PhysicianRecord],
    config: PipelineConfig | None = None,
) -> list[MatchResult]:
    """
    Find all matches among a list of records.

    Uses blocking to reduce comparisons, then scores pairs.
    """
    config = config or PipelineConfig()

    # Get candidate pairs via blocking
    pairs = get_candidate_pairs(records, use_soundex=config.use_soundex_blocking)

    results: list[MatchResult] = []
    match_count = 0
    non_match_count = 0
    uncertain_count = 0

    for record1, record2 in pairs:
        # Calculate similarity
        scores = calculate_similarity(record1, record2)

        # Classify
        decision, confidence = classify_match(scores, config)

        # Determine match type
        match_type = determine_match_type(record1, record2, scores)

        result = MatchResult(
            source_id_1=record1.source_id,
            source_id_2=record2.source_id,
            scores=scores,
            decision=decision,
            confidence=confidence,
            match_type=match_type,
        )
        results.append(result)

        if decision == MatchDecision.MATCH:
            match_count += 1
        elif decision == MatchDecision.NON_MATCH:
            non_match_count += 1
        else:
            uncertain_count += 1

    logger.info(
        f"Classification complete: {match_count} matches, "
        f"{non_match_count} non-matches, {uncertain_count} uncertain"
    )

    return results


def get_confirmed_matches(
    results: list[MatchResult],
    include_uncertain: bool = False,
) -> list[tuple[str, str, float]]:
    """
    Extract confirmed matches as (source_id_1, source_id_2, confidence) tuples.

    Optionally include uncertain matches.
    """
    matches = []

    for result in results:
        if result.decision == MatchDecision.MATCH:
            matches.append(
                (
                    result.source_id_1,
                    result.source_id_2,
                    result.scores.overall_score,
                )
            )
        elif include_uncertain and result.decision == MatchDecision.UNCERTAIN:
            matches.append(
                (
                    result.source_id_1,
                    result.source_id_2,
                    result.scores.overall_score,
                )
            )

    logger.info(f"Extracted {len(matches)} confirmed matches")
    return matches
