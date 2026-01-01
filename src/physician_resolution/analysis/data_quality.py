"""Data quality analysis for input sources."""

import pandas as pd

from ..logging import get_logger
from ..schemas.records import PhysicianRecord

logger = get_logger("analysis.data_quality")


def analyze_source_records(records: list[PhysicianRecord]) -> dict:
    """Analyze data quality across all source records."""
    if not records:
        return {"error": "No records provided"}

    # Group by source
    by_source: dict[str, list[PhysicianRecord]] = {}
    for record in records:
        if record.source not in by_source:
            by_source[record.source] = []
        by_source[record.source].append(record)

    # Overall stats
    total = len(records)
    with_npi = sum(1 for r in records if r.npi)
    with_name = sum(1 for r in records if r.name_last)
    with_specialty = sum(1 for r in records if r.specialty)
    with_location = sum(1 for r in records if r.facility_state)

    report = {
        "total_records": total,
        "npi_coverage": with_npi / total if total else 0,
        "name_coverage": with_name / total if total else 0,
        "specialty_coverage": with_specialty / total if total else 0,
        "location_coverage": with_location / total if total else 0,
        "sources": {},
    }

    # Per-source stats
    for source, source_records in by_source.items():
        count = len(source_records)
        report["sources"][source] = {
            "record_count": count,
            "npi_coverage": sum(1 for r in source_records if r.npi) / count,
            "name_coverage": sum(1 for r in source_records if r.name_last) / count,
            "specialty_coverage": sum(1 for r in source_records if r.specialty) / count,
            "location_coverage": sum(1 for r in source_records if r.facility_state) / count,
            "unique_npis": len(set(r.npi for r in source_records if r.npi)),
            "unique_states": len(set(r.facility_state for r in source_records if r.facility_state)),
        }

    return report


def analyze_dataframe(df: pd.DataFrame, source_name: str) -> dict:
    """Analyze data quality of a single DataFrame."""
    if df.empty:
        return {"error": f"Empty DataFrame for {source_name}"}

    total = len(df)
    report = {
        "source": source_name,
        "total_rows": total,
        "columns": list(df.columns),
        "missing_values": {},
        "unique_counts": {},
    }

    # Missing value analysis
    for col in df.columns:
        missing = df[col].isna().sum() + (df[col] == "").sum()
        report["missing_values"][col] = {
            "count": int(missing),
            "percentage": missing / total if total else 0,
        }

    # Unique value counts for key columns
    key_columns = ["npi", "physician_name", "provider_name", "specialty", "facility_state"]
    for col in key_columns:
        if col in df.columns:
            non_null = df[col].dropna()
            non_empty = non_null[non_null != ""]
            report["unique_counts"][col] = len(non_empty.unique())

    return report


def find_duplicate_npis(records: list[PhysicianRecord]) -> dict:
    """Find NPIs that appear with different names (potential data issues)."""
    npi_names: dict[str, set[str]] = {}

    for record in records:
        if record.npi and record.name_last:
            if record.npi not in npi_names:
                npi_names[record.npi] = set()
            # Normalize name for comparison
            name_key = f"{record.name_last.upper()}, {(record.name_first or '').upper()}"
            npi_names[record.npi].add(name_key)

    # Find NPIs with multiple names
    duplicates = {npi: list(names) for npi, names in npi_names.items() if len(names) > 1}

    return {
        "total_npis": len(npi_names),
        "npis_with_multiple_names": len(duplicates),
        "examples": dict(list(duplicates.items())[:10]),  # First 10 examples
    }


def generate_data_quality_report(
    records: list[PhysicianRecord],
    source_dfs: dict[str, pd.DataFrame] | None = None,
) -> dict:
    """Generate comprehensive data quality report."""
    report = {
        "summary": analyze_source_records(records),
        "duplicate_analysis": find_duplicate_npis(records),
    }

    if source_dfs:
        report["source_details"] = {}
        for source_name, df in source_dfs.items():
            report["source_details"][source_name] = analyze_dataframe(df, source_name)

    logger.info(f"Generated data quality report for {len(records)} records")

    return report
