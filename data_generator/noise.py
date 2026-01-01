import random
import string


def add_typo(text: str, probability: float = 0.1) -> str:
    """Add a random typo to text."""
    if not text or random.random() > probability:
        return text

    text = list(text)
    typo_type = random.choice(["swap", "drop", "double", "replace"])
    pos = random.randint(0, len(text) - 1)

    if typo_type == "swap" and pos < len(text) - 1:
        text[pos], text[pos + 1] = text[pos + 1], text[pos]
    elif typo_type == "drop" and len(text) > 3:
        text.pop(pos)
    elif typo_type == "double":
        text.insert(pos, text[pos])
    elif typo_type == "replace":
        text[pos] = random.choice(string.ascii_lowercase)

    return "".join(text)


def maybe_uppercase(text: str, probability: float = 0.3) -> str:
    """Randomly uppercase entire string."""
    if random.random() < probability:
        return text.upper()
    return text


def maybe_missing(value: str | None, probability: float = 0.1) -> str | None:
    """Randomly return None to simulate missing data."""
    if random.random() < probability:
        return None
    return value


def vary_hospital_name(name: str) -> str:
    """Create variations of hospital names."""
    variations = [
        lambda n: n,
        lambda n: n.replace("Hospital", "Hosp"),
        lambda n: n.replace("Hospital", "Hosp."),
        lambda n: n.replace("Medical Center", "Med Ctr"),
        lambda n: n.replace("Medical Center", "Med. Ctr."),
        lambda n: n.replace("St.", "Saint"),
        lambda n: n.replace("Saint", "St."),
        lambda n: n.replace("'s", "s"),
        lambda n: n + " - Main Campus",
        lambda n: n + " East",
        lambda n: add_typo(n, probability=0.5),
    ]
    return random.choice(variations)(name)


def vary_specialty(specialty: str) -> str:
    """Create variations of specialty names."""
    mappings = {
        "Internal Medicine": ["Internal Med", "Int Medicine", "IM"],
        "Family Medicine": ["Family Med", "Family Practice", "FP"],
        "Cardiology": ["Cardiovascular Disease", "Cardiovascular Med", "CV"],
        "Orthopedic Surgery": ["Orthopaedic Surgery", "Orthopedics", "Ortho"],
        "General Surgery": ["Surgery", "Gen Surgery"],
        "Pediatrics": ["Pediatric Medicine", "Peds"],
        "Obstetrics & Gynecology": ["OB/GYN", "OB-GYN", "Obstetrics and Gynecology"],
        "Psychiatry": ["Psychiatric Medicine", "Psych"],
        "Neurology": ["Neurological Medicine", "Neuro"],
        "Gastroenterology": ["GI", "Gastro", "GI Medicine"],
        "Pulmonology": ["Pulmonary Medicine", "Pulmonary Disease"],
        "Nephrology": ["Renal Medicine", "Kidney Disease"],
        "Oncology": ["Medical Oncology", "Cancer Medicine"],
        "Emergency Medicine": ["ER", "Emergency Med", "EM"],
    }

    if specialty in mappings and random.random() > 0.5:
        return random.choice(mappings[specialty])
    return specialty


def vary_address(address: str) -> str:
    """Create variations of address formatting."""
    variations = [
        lambda a: a,
        lambda a: a.replace(" St", " Street"),
        lambda a: a.replace(" Ave", " Avenue"),
        lambda a: a.replace(" Blvd", " Boulevard"),
        lambda a: a.replace(" Dr", " Drive"),
        lambda a: a.replace("Street", "St"),
        lambda a: a.replace("Avenue", "Ave"),
        lambda a: a.upper(),
    ]
    return random.choice(variations)(address)


def corrupt_npi(npi: str, probability: float = 0.05) -> str | None:
    """Simulate NPI data quality issues."""
    if random.random() < probability:
        issue = random.choice(["missing", "malformed", "truncated"])
        if issue == "missing":
            return None
        elif issue == "malformed":
            return npi[:5] + "XXXXX"
        elif issue == "truncated":
            return npi[:8]
    return npi
