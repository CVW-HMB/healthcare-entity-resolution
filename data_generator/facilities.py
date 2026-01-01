import random

HOSPITAL_PREFIXES = [
    "Memorial",
    "St. Mary's",
    "University",
    "Regional",
    "Community",
    "General",
    "Sacred Heart",
    "Providence",
    "Mercy",
    "Baptist",
    "Methodist",
    "Presbyterian",
    "Lutheran",
    "Good Samaritan",
    "Holy Cross",
    "Mount Sinai",
    "Cedars",
    "Kaiser",
    "Veterans",
    "Children's",
    "Northwestern",
    "Duke",
    "Johns Hopkins",
    "Mayo",
]

HOSPITAL_SUFFIXES = [
    "Hospital",
    "Medical Center",
    "Health System",
    "Healthcare",
    "Clinic",
    "Medical Group",
    "Health",
    "Regional Medical Center",
    "Community Hospital",
]

CITIES = [
    ("Boston", "MA", "02101"),
    ("New York", "NY", "10001"),
    ("Los Angeles", "CA", "90001"),
    ("Chicago", "IL", "60601"),
    ("Houston", "TX", "77001"),
    ("Phoenix", "AZ", "85001"),
    ("Philadelphia", "PA", "19101"),
    ("San Antonio", "TX", "78201"),
    ("San Diego", "CA", "92101"),
    ("Dallas", "TX", "75201"),
    ("San Jose", "CA", "95101"),
    ("Austin", "TX", "78701"),
    ("Jacksonville", "FL", "32201"),
    ("Fort Worth", "TX", "76101"),
    ("Columbus", "OH", "43201"),
    ("Charlotte", "NC", "28201"),
    ("Seattle", "WA", "98101"),
    ("Denver", "CO", "80201"),
    ("Nashville", "TN", "37201"),
    ("Portland", "OR", "97201"),
    ("Detroit", "MI", "48201"),
    ("Memphis", "TN", "38101"),
    ("Atlanta", "GA", "30301"),
    ("Miami", "FL", "33101"),
    ("Cleveland", "OH", "44101"),
    ("Minneapolis", "MN", "55401"),
    ("Pittsburgh", "PA", "15201"),
    ("St. Louis", "MO", "63101"),
    ("Baltimore", "MD", "21201"),
    ("Tampa", "FL", "33601"),
]

STREET_NAMES = [
    "Main",
    "Oak",
    "Maple",
    "Cedar",
    "Pine",
    "Elm",
    "Washington",
    "Park",
    "Lake",
    "Hill",
    "Forest",
    "River",
    "Spring",
    "Valley",
    "Sunset",
    "Highland",
    "Franklin",
    "Lincoln",
    "Jefferson",
    "Madison",
    "Adams",
    "Monroe",
    "Jackson",
]

STREET_TYPES = ["St", "Ave", "Blvd", "Dr", "Ln", "Way", "Rd", "Pkwy"]

SPECIALTIES = [
    "Internal Medicine",
    "Family Medicine",
    "Cardiology",
    "Orthopedic Surgery",
    "General Surgery",
    "Pediatrics",
    "Obstetrics & Gynecology",
    "Psychiatry",
    "Neurology",
    "Dermatology",
    "Radiology",
    "Anesthesiology",
    "Emergency Medicine",
    "Ophthalmology",
    "Gastroenterology",
    "Pulmonology",
    "Nephrology",
    "Oncology",
    "Urology",
    "Endocrinology",
    "Rheumatology",
    "Infectious Disease",
    "Physical Medicine",
    "Plastic Surgery",
    "Vascular Surgery",
]

MEDICAL_SCHOOLS = [
    "Harvard Medical School",
    "Johns Hopkins School of Medicine",
    "Stanford University School of Medicine",
    "UCSF School of Medicine",
    "Columbia University College of Physicians",
    "University of Pennsylvania Perelman School of Medicine",
    "Yale School of Medicine",
    "Duke University School of Medicine",
    "Washington University School of Medicine",
    "University of Michigan Medical School",
    "UCLA David Geffen School of Medicine",
    "Northwestern University Feinberg School of Medicine",
    "Cornell Weill Medical College",
    "University of Chicago Pritzker School of Medicine",
    "Vanderbilt University School of Medicine",
    "University of Pittsburgh School of Medicine",
    "NYU Grossman School of Medicine",
    "Emory University School of Medicine",
    "University of Virginia School of Medicine",
    "Case Western Reserve University School of Medicine",
]


def generate_hospital_name() -> str:
    """Generate a random hospital name."""
    return f"{random.choice(HOSPITAL_PREFIXES)} {random.choice(HOSPITAL_SUFFIXES)}"


def generate_location() -> dict:
    """Generate a random location with address."""
    city, state, base_zip = random.choice(CITIES)

    # Vary the zip slightly
    zip_code = str(int(base_zip) + random.randint(0, 99)).zfill(5)

    street_num = random.randint(100, 9999)
    street_name = random.choice(STREET_NAMES)
    street_type = random.choice(STREET_TYPES)
    address = f"{street_num} {street_name} {street_type}"

    return {
        "address": address,
        "city": city,
        "state": state,
        "zip": zip_code,
    }


def generate_specialty() -> str:
    """Generate a random medical specialty."""
    return random.choice(SPECIALTIES)


def generate_medical_school() -> str:
    """Generate a random medical school."""
    return random.choice(MEDICAL_SCHOOLS)


def generate_facility() -> dict:
    """Generate a complete facility record."""
    location = generate_location()
    return {
        "name": generate_hospital_name(),
        "address": location["address"],
        "city": location["city"],
        "state": location["state"],
        "zip": location["zip"],
    }
