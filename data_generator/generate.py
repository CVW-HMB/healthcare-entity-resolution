import csv
import random
from datetime import date, timedelta
from pathlib import Path

from .facilities import (
    generate_facility,
    generate_medical_school,
    generate_specialty,
)
from .names import (
    format_name_cms,
    format_name_hospital,
    format_name_license,
    format_name_publication,
    generate_npi,
    generate_physician_name,
)
from .noise import (
    add_typo,
    corrupt_npi,
    maybe_missing,
    vary_address,
    vary_hospital_name,
    vary_specialty,
)


def generate_true_physicians(n: int) -> list[dict]:
    """Generate N ground-truth physician records."""
    physicians = []

    for i in range(n):
        name = generate_physician_name()
        facility = generate_facility()
        specialty = generate_specialty()
        npi = generate_npi()
        med_school = generate_medical_school()
        grad_year = random.randint(1970, 2015)

        physicians.append(
            {
                "true_id": f"TRUE_{i:05d}",
                "npi": npi,
                "name": name,
                "specialty": specialty,
                "facility": facility,
                "medical_school": med_school,
                "graduation_year": grad_year,
            }
        )

    return physicians


def generate_cms_claims(physicians: list[dict], output_path: Path) -> list[dict]:
    """Generate CMS claims records."""
    records = []
    record_idx = 0

    for phys in physicians:
        num_records = random.randint(1, 5)

        for j in range(num_records):
            proc_date = date.today() - timedelta(days=random.randint(1, 365))
            patient_id = f"PAT_{random.randint(10000, 99999)}"

            npi = corrupt_npi(phys["npi"], probability=0.05)
            facility_name = vary_hospital_name(phys["facility"]["name"])

            records.append(
                {
                    "source_id": f"cms_{record_idx:06d}",
                    "npi": npi,
                    "provider_name": format_name_cms(phys["name"]),
                    "provider_specialty": vary_specialty(phys["specialty"]),
                    "facility_name": facility_name,
                    "facility_npi": generate_npi(),
                    "procedure_code": f"{random.randint(10000, 99999)}",
                    "procedure_date": proc_date.isoformat(),
                    "patient_id": patient_id,
                    "true_physician_id": phys["true_id"],
                }
            )
            record_idx += 1

    fieldnames = [
        "source_id",
        "npi",
        "provider_name",
        "provider_specialty",
        "facility_name",
        "facility_npi",
        "procedure_code",
        "procedure_date",
        "patient_id",
        "true_physician_id",
    ]
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    return records


def generate_state_licenses(physicians: list[dict], output_path: Path) -> list[dict]:
    """Generate state license records."""
    records = []
    record_idx = 0

    for phys in physicians:
        license_num = f"{phys['facility']['state']}-{random.randint(10000, 99999)}"

        records.append(
            {
                "source_id": f"lic_{record_idx:06d}",
                "license_number": license_num,
                "physician_name": format_name_license(phys["name"]),
                "specialty": vary_specialty(phys["specialty"]),
                "license_state": phys["facility"]["state"],
                "license_status": random.choice(["Active", "Active", "Active", "Inactive"]),
                "address_line1": vary_address(phys["facility"]["address"]),
                "address_city": phys["facility"]["city"],
                "address_state": phys["facility"]["state"],
                "address_zip": phys["facility"]["zip"],
                "medical_school": phys["medical_school"],
                "graduation_year": phys["graduation_year"],
                "true_physician_id": phys["true_id"],
            }
        )
        record_idx += 1

    fieldnames = [
        "source_id",
        "license_number",
        "physician_name",
        "specialty",
        "license_state",
        "license_status",
        "address_line1",
        "address_city",
        "address_state",
        "address_zip",
        "medical_school",
        "graduation_year",
        "true_physician_id",
    ]
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    return records


def generate_hospital_affiliations(physicians: list[dict], output_path: Path) -> list[dict]:
    """Generate hospital affiliation records."""
    records = []
    record_idx = 0

    for phys in physicians:
        num_affiliations = random.choices([1, 2, 3], weights=[0.7, 0.2, 0.1])[0]

        for _ in range(num_affiliations):
            if random.random() > 0.3:
                facility = phys["facility"]
            else:
                facility = generate_facility()

            hospital_id = f"HOSP_{random.randint(1000, 9999)}"
            start_date = date.today() - timedelta(days=random.randint(365, 3650))

            npi = phys["npi"] if random.random() > 0.4 else None

            titles = ["Attending", "Associate", "Chief", "Director", "Fellow"]

            records.append(
                {
                    "source_id": f"hosp_{record_idx:06d}",
                    "hospital_id": hospital_id,
                    "hospital_name": vary_hospital_name(facility["name"]),
                    "physician_name": format_name_hospital(phys["name"]),
                    "department": phys["specialty"],
                    "title": random.choice(titles),
                    "phone": f"({random.randint(200,999)}) {random.randint(200,999)}-{random.randint(1000,9999)}",
                    "email": maybe_missing(
                        f"{phys['name']['first'].lower()}.{phys['name']['last'].lower()}@{facility['name'].split()[0].lower()}.org",
                        probability=0.3,
                    ),
                    "start_date": start_date.isoformat(),
                    "npi": npi,
                    "true_physician_id": phys["true_id"],
                }
            )
            record_idx += 1

    fieldnames = [
        "source_id",
        "hospital_id",
        "hospital_name",
        "physician_name",
        "department",
        "title",
        "phone",
        "email",
        "start_date",
        "npi",
        "true_physician_id",
    ]
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    return records


def generate_publications(physicians: list[dict], output_path: Path) -> list[dict]:
    """Generate publication records."""
    records = []
    record_idx = 0

    publishing_physicians = random.sample(physicians, k=int(len(physicians) * 0.4))

    journals = [
        "New England Journal of Medicine",
        "JAMA",
        "The Lancet",
        "BMJ",
        "Annals of Internal Medicine",
        "JAMA Internal Medicine",
        "Circulation",
        "Journal of Clinical Oncology",
        "Journal of the American College of Cardiology",
        "Gastroenterology",
    ]

    for phys in publishing_physicians:
        num_pubs = random.randint(1, 5)

        for _ in range(num_pubs):
            pub_date = date.today() - timedelta(days=random.randint(30, 2000))
            pub_id = f"PMID{random.randint(10000000, 99999999)}"

            affiliation = f"{phys['facility']['name']}, {phys['facility']['city']}, {phys['facility']['state']}"
            if random.random() > 0.5:
                affiliation = add_typo(affiliation, probability=0.3)

            records.append(
                {
                    "source_id": f"pub_{record_idx:06d}",
                    "publication_id": pub_id,
                    "title": f"Study on {phys['specialty']} outcomes in clinical practice",
                    "author_name": format_name_publication(phys["name"]),
                    "author_position": random.choice([1, 2, 3, -1]),
                    "author_affiliation": affiliation,
                    "publication_date": pub_date.isoformat(),
                    "journal": random.choice(journals),
                    "true_physician_id": phys["true_id"],
                }
            )
            record_idx += 1

    fieldnames = [
        "source_id",
        "publication_id",
        "title",
        "author_name",
        "author_position",
        "author_affiliation",
        "publication_date",
        "journal",
        "true_physician_id",
    ]
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    return records


def generate_referrals(physicians: list[dict], output_path: Path) -> list[dict]:
    """Generate referral records between physicians."""
    records = []

    pcp_specialties = {"Internal Medicine", "Family Medicine", "Pediatrics"}
    pcps = [p for p in physicians if p["specialty"] in pcp_specialties]
    specialists = [p for p in physicians if p["specialty"] not in pcp_specialties]

    for pcp in pcps:
        num_referrals = random.randint(2, 10)
        referred_to = random.sample(specialists, k=min(num_referrals, len(specialists)))

        for specialist in referred_to:
            num_patients = random.randint(1, 20)

            for _ in range(num_patients):
                ref_date = date.today() - timedelta(days=random.randint(1, 365))
                patient_id = f"PAT_{random.randint(10000, 99999)}"

                referring_npi = corrupt_npi(pcp["npi"], probability=0.08)
                receiving_npi = corrupt_npi(specialist["npi"], probability=0.08)

                records.append(
                    {
                        "referring_npi": referring_npi,
                        "receiving_npi": receiving_npi,
                        "patient_id": patient_id,
                        "referral_date": ref_date.isoformat(),
                        "diagnosis_code": f"{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.randint(10, 99)}.{random.randint(0, 9)}",
                        "referring_true_id": pcp["true_id"],
                        "receiving_true_id": specialist["true_id"],
                    }
                )

    fieldnames = [
        "referring_npi",
        "receiving_npi",
        "patient_id",
        "referral_date",
        "diagnosis_code",
        "referring_true_id",
        "receiving_true_id",
    ]
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    return records


def generate_ground_truth(
    cms_records: list[dict],
    license_records: list[dict],
    hospital_records: list[dict],
    publication_records: list[dict],
    output_path: Path,
) -> None:
    """Generate ground truth mapping: source_id -> true_physician_id."""
    rows = []

    for r in cms_records:
        rows.append(
            {
                "source_id": r["source_id"],
                "true_physician_id": r["true_physician_id"],
                "source": "cms",
            }
        )
    for r in license_records:
        rows.append(
            {
                "source_id": r["source_id"],
                "true_physician_id": r["true_physician_id"],
                "source": "license",
            }
        )
    for r in hospital_records:
        rows.append(
            {
                "source_id": r["source_id"],
                "true_physician_id": r["true_physician_id"],
                "source": "hospital",
            }
        )
    for r in publication_records:
        rows.append(
            {
                "source_id": r["source_id"],
                "true_physician_id": r["true_physician_id"],
                "source": "publication",
            }
        )

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["source_id", "true_physician_id", "source"])
        writer.writeheader()
        writer.writerows(rows)


def generate_all(
    num_physicians: int = 500,
    output_dir: str | Path = "data/synthetic",
    seed: int | None = 42,
) -> None:
    """Generate all synthetic datasets."""
    if seed is not None:
        random.seed(seed)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating {num_physicians} physicians...")
    physicians = generate_true_physicians(num_physicians)

    print("Generating CMS claims...")
    cms_records = generate_cms_claims(physicians, output_dir / "cms_claims.csv")

    print("Generating state licenses...")
    license_records = generate_state_licenses(physicians, output_dir / "state_licenses.csv")

    print("Generating hospital affiliations...")
    hospital_records = generate_hospital_affiliations(
        physicians, output_dir / "hospital_affiliations.csv"
    )

    print("Generating publications...")
    publication_records = generate_publications(physicians, output_dir / "publications.csv")

    print("Generating referrals...")
    generate_referrals(physicians, output_dir / "referrals.csv")

    print("Generating ground truth...")
    generate_ground_truth(
        cms_records,
        license_records,
        hospital_records,
        publication_records,
        output_dir / "ground_truth.csv",
    )

    print(f"Done! Files written to {output_dir}")


if __name__ == "__main__":
    generate_all()
