"""Merge attributes from clustered records into canonical entities."""

from collections import Counter

import networkx as nx

from ..logging import get_logger
from ..schemas.entities import CanonicalPhysician
from .confidence import calculate_entity_confidence
from .ids import _generate_canonical_id

logger = get_logger("canonicalization.merge")

# Source reliability for attribute selection
SOURCE_PRIORITY = {
    "cms": 4,
    "license": 3,
    "hospital": 2,
    "publication": 1,
}


def merge_cluster_attributes(
    G: nx.Graph,
    cluster: set[str],
) -> CanonicalPhysician:
    """
    Combine attributes from all records in cluster into a canonical entity.

    Selection strategies:
    - NPI: Most common (should be only one after pruning)
    - Name: Longest/most complete, prefer higher-priority sources
    - Specialty: Most common, prefer CMS
    - Location: Most recent or most frequent facility
    """
    canonical_id = _generate_canonical_id(G, cluster)
    confidence = calculate_entity_confidence(G, cluster)

    # Collect all attributes
    npis = []
    names = []
    specialties = []
    facilities = []
    cities = []
    states = []

    for node in cluster:
        attrs = G.nodes[node]
        source = attrs.get("source", "unknown")
        priority = SOURCE_PRIORITY.get(source, 0)

        if attrs.get("npi"):
            npis.append(attrs["npi"])

        if attrs.get("name_raw"):
            names.append((attrs["name_raw"], priority, attrs.get("name_last", "")))

        if attrs.get("specialty"):
            specialties.append((attrs["specialty"], priority))

        if attrs.get("facility_name"):
            facilities.append((attrs["facility_name"], priority))

        if attrs.get("facility_city"):
            cities.append(attrs["facility_city"])

        if attrs.get("facility_state"):
            states.append(attrs["facility_state"])

    # Select best attributes
    npi = _select_npi(npis)
    name = _select_name(names)
    specialty = _select_specialty(specialties)
    primary_facility = _select_facility(facilities)
    city = _select_most_common(cities)
    state = _select_most_common(states)

    # Get all unique facilities
    all_facilities = list(set(f[0] for f in facilities))

    return CanonicalPhysician(
        canonical_id=canonical_id,
        confidence=confidence,
        npi=npi,
        name=name,
        specialty=specialty,
        primary_facility=primary_facility,
        city=city,
        state=state,
        all_facilities=all_facilities,
        source_records=list(cluster),
        source_count=len(cluster),
    )


def _select_npi(npis: list[str]) -> str | None:
    """Select NPI - should be only one after pruning."""
    if not npis:
        return None

    # Filter valid NPIs
    valid_npis = [n for n in npis if len(n) == 10 and n.isdigit()]
    if not valid_npis:
        return None

    # Most common
    counts = Counter(valid_npis)
    return counts.most_common(1)[0][0]


def _select_name(names: list[tuple[str, int, str]]) -> str | None:
    """
    Select best name.

    Prefer:
    1. Higher priority source
    2. Longer/more complete name
    """
    if not names:
        return None

    # Sort by priority (desc), then by length (desc)
    sorted_names = sorted(names, key=lambda x: (x[1], len(x[0])), reverse=True)
    return sorted_names[0][0]


def _select_specialty(specialties: list[tuple[str, int]]) -> str | None:
    """Select specialty - prefer higher priority source, then most common."""
    if not specialties:
        return None

    # Group by normalized specialty
    normalized: dict[str, list[tuple[str, int]]] = {}
    for spec, priority in specialties:
        key = spec.upper().strip()
        if key not in normalized:
            normalized[key] = []
        normalized[key].append((spec, priority))

    # Find most common
    most_common_key = max(normalized.keys(), key=lambda k: len(normalized[k]))

    # From most common, pick highest priority version
    versions = normalized[most_common_key]
    best = max(versions, key=lambda x: x[1])
    return best[0]


def _select_facility(facilities: list[tuple[str, int]]) -> str | None:
    """Select primary facility - most common, then highest priority."""
    if not facilities:
        return None

    # Count occurrences
    counts: dict[str, int] = {}
    priorities: dict[str, int] = {}

    for facility, priority in facilities:
        normalized = facility.strip()
        counts[normalized] = counts.get(normalized, 0) + 1
        priorities[normalized] = max(priorities.get(normalized, 0), priority)

    # Sort by count (desc), then priority (desc)
    sorted_facilities = sorted(
        counts.keys(),
        key=lambda f: (counts[f], priorities[f]),
        reverse=True,
    )

    return sorted_facilities[0]


def _select_most_common(values: list[str]) -> str | None:
    """Select most common value."""
    if not values:
        return None

    counts = Counter(v.strip() for v in values if v)
    if not counts:
        return None

    return counts.most_common(1)[0][0]


def merge_all_clusters(
    G: nx.Graph,
    clusters: list[set[str]],
) -> list[CanonicalPhysician]:
    """Merge all clusters into canonical physicians."""
    physicians = []

    for cluster in clusters:
        physician = merge_cluster_attributes(G, cluster)
        physicians.append(physician)

    logger.info(f"Created {len(physicians)} canonical physicians")

    # Log some stats
    with_npi = sum(1 for p in physicians if p.npi)
    avg_sources = sum(p.source_count for p in physicians) / len(physicians) if physicians else 0

    logger.info(f"  {with_npi} with NPI ({100*with_npi/len(physicians):.1f}%)")
    logger.info(f"  Average {avg_sources:.1f} source records per physician")

    return physicians
