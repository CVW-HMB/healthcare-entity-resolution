"""Parse and standardize physician names."""

import re

from ..logging import get_logger
from ..schemas.records import ParsedName

logger = get_logger("etl.name_parser")

# Titles to strip
TITLES = {"DR", "DR.", "PROF", "PROF.", "PROFESSOR"}

# Suffixes to extract
SUFFIXES = {
    "MD",
    "M.D.",
    "M.D",
    "DO",
    "D.O.",
    "D.O",
    "PHD",
    "PH.D.",
    "PH.D",
    "FACS",
    "F.A.C.S.",
    "FACC",
    "F.A.C.C.",
    "FACP",
    "F.A.C.P.",
    "JR",
    "JR.",
    "SR",
    "SR.",
    "II",
    "III",
    "IV",
}

# Pattern for "LAST, FIRST" or "LAST, FIRST MIDDLE"
LAST_FIRST_PATTERN = re.compile(r"^([^,]+),\s*(.+)$")

# Pattern for suffix at end
SUFFIX_PATTERN = re.compile(
    r",?\s*(" + "|".join(re.escape(s) for s in SUFFIXES) + r")\.?\s*$", re.IGNORECASE
)


def parse_name(raw_name: str) -> ParsedName:
    """
    Parse a raw name string into components.

    Handles:
    - LAST, FIRST format (CMS style)
    - FIRST LAST format
    - Suffixes (MD, DO, PhD, Jr, III)
    - Titles (Dr., Prof.)
    - Middle names vs middle initials
    - Hyphenated last names
    """
    if not raw_name or not raw_name.strip():
        return ParsedName()

    name = raw_name.strip()
    suffix = None
    title = None

    # Extract suffix(es)
    suffixes_found = []
    while True:
        match = SUFFIX_PATTERN.search(name)
        if match:
            suffixes_found.append(match.group(1).upper().replace(".", ""))
            name = name[: match.start()].strip()
        else:
            break

    if suffixes_found:
        suffix = ", ".join(reversed(suffixes_found))

    # Remove title
    name_upper = name.upper()
    for t in TITLES:
        if name_upper.startswith(t + " "):
            title = t.replace(".", "")
            name = name[len(t) :].strip()
            break

    # Clean up extra whitespace
    name = " ".join(name.split())

    # Try LAST, FIRST pattern
    match = LAST_FIRST_PATTERN.match(name)
    if match:
        last = match.group(1).strip()
        rest = match.group(2).strip()

        # Split rest into first and middle
        parts = rest.split()
        first = parts[0] if parts else None
        middle = " ".join(parts[1:]) if len(parts) > 1 else None

        # Handle single letter middle initial
        if middle and len(middle) == 1:
            middle = middle.upper()
        elif middle and len(middle) == 2 and middle.endswith("."):
            middle = middle[0].upper()

        return ParsedName(
            first=first,
            last=last,
            middle=middle,
            suffix=suffix,
            title=title,
        )

    # FIRST LAST or FIRST MIDDLE LAST pattern
    parts = name.split()

    if len(parts) == 1:
        # Just one name - assume it's last name
        return ParsedName(last=parts[0], suffix=suffix, title=title)

    if len(parts) == 2:
        # FIRST LAST
        return ParsedName(
            first=parts[0],
            last=parts[1],
            suffix=suffix,
            title=title,
        )

    # 3+ parts: FIRST [MIDDLE...] LAST
    # Check if last part might be a compound last name
    first = parts[0]
    last = parts[-1]
    middle_parts = parts[1:-1]

    # Handle initials like "J. A. Smith" -> first=J, middle=A, last=Smith
    if len(first) <= 2 and first.endswith("."):
        first = first[0]

    middle = None
    if middle_parts:
        # Check if it's just an initial
        if len(middle_parts) == 1:
            m = middle_parts[0]
            if len(m) == 1:
                middle = m.upper()
            elif len(m) == 2 and m.endswith("."):
                middle = m[0].upper()
            else:
                middle = m
        else:
            middle = " ".join(middle_parts)

    return ParsedName(
        first=first,
        last=last,
        middle=middle,
        suffix=suffix,
        title=title,
    )


def standardize_name(parsed: ParsedName) -> str:
    """
    Return canonical format: 'LAST, FIRST M'

    All caps, middle initial only, no suffix.
    """
    if not parsed.last:
        return ""

    parts = [parsed.last.upper() + ","]

    if parsed.first:
        first_part = parsed.first.upper()
        if parsed.middle:
            # Just use first letter of middle
            first_part += " " + parsed.middle[0].upper()
        parts.append(first_part)

    return " ".join(parts)


def names_match_fuzzy(name1: str, name2: str) -> bool:
    """Quick check if two names might be the same person."""
    p1 = parse_name(name1)
    p2 = parse_name(name2)

    # Must have matching last names
    if not p1.last or not p2.last:
        return False

    last1 = p1.last.upper().replace("-", "").replace("'", "").replace(" ", "")
    last2 = p2.last.upper().replace("-", "").replace("'", "").replace(" ", "")

    if last1 != last2:
        return False

    # Check first name compatibility
    if p1.first and p2.first:
        f1 = p1.first.upper()
        f2 = p2.first.upper()

        # Exact match
        if f1 == f2:
            return True

        # Initial match (J matches John)
        if len(f1) == 1 and f2.startswith(f1):
            return True
        if len(f2) == 1 and f1.startswith(f2):
            return True

        # Otherwise first names don't match
        return False

    # One or both missing first name - consider it a possible match
    return True
