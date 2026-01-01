"""Blocking strategies to reduce pairwise comparison space."""

from collections import defaultdict

import jellyfish

from ..logging import get_logger
from ..schemas.records import PhysicianRecord

logger = get_logger("matching.blocking")


def block_by_npi(records: list[PhysicianRecord]) -> dict[str, list[PhysicianRecord]]:
    """
    Group records that share an NPI.

    This is the strongest blocking key - NPI is unique per physician.
    """
    blocks: dict[str, list[PhysicianRecord]] = defaultdict(list)

    for record in records:
        if record.npi:
            blocks[record.npi].append(record)

    # Filter to blocks with 2+ records
    blocks = {k: v for k, v in blocks.items() if len(v) >= 2}

    logger.info(f"NPI blocking: {len(blocks)} blocks from {len(records)} records")
    return blocks


def block_by_last_name_state(records: list[PhysicianRecord]) -> dict[str, list[PhysicianRecord]]:
    """
    Group by (last_name, state).

    For records without NPI, this is a reasonable blocking key.
    """
    blocks: dict[str, list[PhysicianRecord]] = defaultdict(list)

    for record in records:
        if record.name_last:
            last = record.name_last.upper().strip()
            state = (record.facility_state or "XX").upper()
            key = f"{last}|{state}"
            blocks[key].append(record)

    # Filter to blocks with 2+ records
    blocks = {k: v for k, v in blocks.items() if len(v) >= 2}

    logger.info(f"Last name + state blocking: {len(blocks)} blocks")
    return blocks


def block_by_soundex_state(records: list[PhysicianRecord]) -> dict[str, list[PhysicianRecord]]:
    """
    Phonetic blocking using Soundex.

    Groups records where last names sound similar (SMITH and SMYTH).
    """
    blocks: dict[str, list[PhysicianRecord]] = defaultdict(list)

    for record in records:
        if record.name_last:
            try:
                soundex = jellyfish.soundex(record.name_last)
                state = (record.facility_state or "XX").upper()
                key = f"{soundex}|{state}"
                blocks[key].append(record)
            except Exception:
                # Skip records where soundex fails
                pass

    # Filter to blocks with 2+ records
    blocks = {k: v for k, v in blocks.items() if len(v) >= 2}

    logger.info(f"Soundex + state blocking: {len(blocks)} blocks")
    return blocks


def block_by_last_name_first_initial(
    records: list[PhysicianRecord],
) -> dict[str, list[PhysicianRecord]]:
    """
    Group by (last_name, first_initial).

    More restrictive than just last name, reduces false positives.
    """
    blocks: dict[str, list[PhysicianRecord]] = defaultdict(list)

    for record in records:
        if record.name_last and record.name_first:
            last = record.name_last.upper().strip()
            first_initial = record.name_first[0].upper()
            key = f"{last}|{first_initial}"
            blocks[key].append(record)

    blocks = {k: v for k, v in blocks.items() if len(v) >= 2}

    logger.info(f"Last name + first initial blocking: {len(blocks)} blocks")
    return blocks


def get_candidate_pairs(
    records: list[PhysicianRecord],
    use_soundex: bool = True,
) -> list[tuple[PhysicianRecord, PhysicianRecord]]:
    """
    Get all candidate pairs for comparison using multiple blocking strategies.

    Returns deduplicated pairs (A,B) where A.source_id < B.source_id.
    """
    seen_pairs: set[tuple[str, str]] = set()
    pairs: list[tuple[PhysicianRecord, PhysicianRecord]] = []

    def add_pairs_from_block(block: list[PhysicianRecord]) -> None:
        for i, rec1 in enumerate(block):
            for rec2 in block[i + 1 :]:
                # Skip same-source comparisons (optional, depends on use case)
                # if rec1.source == rec2.source:
                #     continue

                # Canonical ordering
                if rec1.source_id < rec2.source_id:
                    pair_key = (rec1.source_id, rec2.source_id)
                else:
                    pair_key = (rec2.source_id, rec1.source_id)
                    rec1, rec2 = rec2, rec1

                if pair_key not in seen_pairs:
                    seen_pairs.add(pair_key)
                    pairs.append((rec1, rec2))

    # Apply blocking strategies
    logger.info("Applying blocking strategies...")

    # NPI blocking (highest confidence)
    for block in block_by_npi(records).values():
        add_pairs_from_block(block)

    # Last name + state blocking
    for block in block_by_last_name_state(records).values():
        add_pairs_from_block(block)

    # Soundex blocking (catches typos)
    if use_soundex:
        for block in block_by_soundex_state(records).values():
            add_pairs_from_block(block)

    logger.info(f"Generated {len(pairs)} candidate pairs")
    return pairs
