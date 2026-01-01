import random

FIRST_NAMES = [
    "James",
    "John",
    "Robert",
    "Michael",
    "William",
    "David",
    "Richard",
    "Joseph",
    "Thomas",
    "Christopher",
    "Mary",
    "Patricia",
    "Jennifer",
    "Linda",
    "Elizabeth",
    "Barbara",
    "Susan",
    "Jessica",
    "Sarah",
    "Karen",
    "Matthew",
    "Daniel",
    "Anthony",
    "Mark",
    "Donald",
    "Steven",
    "Paul",
    "Andrew",
    "Joshua",
    "Kenneth",
    "Nancy",
    "Betty",
    "Margaret",
    "Sandra",
    "Ashley",
    "Dorothy",
    "Kimberly",
    "Emily",
    "Donna",
    "Michelle",
    "Brian",
    "George",
    "Edward",
    "Ronald",
    "Timothy",
    "Jason",
    "Jeffrey",
    "Ryan",
    "Jacob",
    "Gary",
    "Nicholas",
    "Eric",
    "Jonathan",
    "Stephen",
    "Larry",
]

LAST_NAMES = [
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Garcia",
    "Miller",
    "Davis",
    "Rodriguez",
    "Martinez",
    "Hernandez",
    "Lopez",
    "Gonzalez",
    "Wilson",
    "Anderson",
    "Thomas",
    "Taylor",
    "Moore",
    "Jackson",
    "Martin",
    "Lee",
    "Perez",
    "Thompson",
    "White",
    "Harris",
    "Sanchez",
    "Clark",
    "Ramirez",
    "Lewis",
    "Robinson",
    "Walker",
    "Young",
    "Allen",
    "King",
    "Wright",
    "Scott",
    "Torres",
    "Nguyen",
    "Hill",
    "Flores",
    "Green",
    "Adams",
    "Nelson",
    "Baker",
    "Hall",
    "Rivera",
    "Campbell",
    "Mitchell",
    "Carter",
    "Roberts",
    "Chen",
    "Wu",
    "Patel",
    "Shah",
    "Kim",
    "Park",
    "O'Brien",
    "O'Connor",
    "McDonald",
    "Van Der Berg",
    "De La Cruz",
    "Smith-Jones",
    "Al-Rashid",
]

MIDDLE_NAMES = [
    "Alan",
    "Anne",
    "Beth",
    "Carl",
    "Claire",
    "Dean",
    "Diane",
    "Earl",
    "Ellen",
    "Frank",
    "Grace",
    "Henry",
    "Irene",
    "Jack",
    "Jean",
    "Keith",
    "Laura",
    "Louis",
    "Marie",
    "Neil",
    "Olivia",
    "Paul",
    "Quinn",
    "Ray",
    "Rose",
    "Scott",
    "Sue",
    "Todd",
    "Uma",
    "Victor",
    "Wayne",
    "Xavier",
    "Yvonne",
    "Zane",
    None,
    None,
    None,
]

SUFFIXES = ["MD", "DO", "PhD", "MD, PhD", "MD, FACS", "DO, FACC", None, None, None, None]


def generate_physician_name() -> dict:
    """Generate a random physician name with all components."""
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    middle = random.choice(MIDDLE_NAMES)
    suffix = random.choice(SUFFIXES)

    return {
        "first": first,
        "last": last,
        "middle": middle,
        "suffix": suffix,
    }


def format_name_cms(name: dict) -> str:
    """Format as CMS style: 'LAST, FIRST M' or 'LAST, FIRST'"""
    parts = [name["last"].upper() + ",", name["first"].upper()]
    if name["middle"] and random.random() > 0.3:
        parts.append(name["middle"][0].upper())
    return " ".join(parts)


def format_name_license(name: dict) -> str:
    """Format as license style: 'First Last, MD' or 'First M. Last, MD'"""
    parts = [name["first"]]
    if name["middle"] and random.random() > 0.4:
        parts.append(name["middle"][0] + ".")
    parts.append(name["last"])
    result = " ".join(parts)
    if name["suffix"]:
        result += ", " + name["suffix"]
    return result


def format_name_hospital(name: dict) -> str:
    """Format as hospital style: 'Dr. First Last' or 'First Last, MD'"""
    if random.random() > 0.5:
        parts = ["Dr.", name["first"]]
        if name["middle"] and random.random() > 0.5:
            parts.append(name["middle"][0] + ".")
        parts.append(name["last"])
        return " ".join(parts)
    else:
        return format_name_license(name)


def format_name_publication(name: dict) -> str:
    """Format as publication style: 'J.A. Smith' or 'J. Smith' or 'John A Smith'"""
    style = random.choice(["initials", "first_initial", "full"])

    if style == "initials":
        parts = [name["first"][0] + "."]
        if name["middle"]:
            parts.append(name["middle"][0] + ".")
        parts.append(name["last"])
        return " ".join(parts)
    elif style == "first_initial":
        return f"{name['first'][0]}. {name['last']}"
    else:
        parts = [name["first"]]
        if name["middle"]:
            parts.append(name["middle"][0])
        parts.append(name["last"])
        return " ".join(parts)


def generate_npi() -> str:
    """Generate a random 10-digit NPI."""
    return "".join([str(random.randint(0, 9)) for _ in range(10)])
