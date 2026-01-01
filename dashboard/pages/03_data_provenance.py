"""Data provenance page - show how physicians were resolved."""

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

st.set_page_config(page_title="Data Provenance", page_icon="🔬", layout="wide")
st.title("🔬 Data Provenance")

st.markdown("""
Explore how physician records were matched and merged across data sources.
""")


@st.cache_data
def load_data():
    """Load physicians and mapping."""
    from physician_resolution.config import OUTPUTS_DIR

    runs_dir = OUTPUTS_DIR / "runs"
    if not runs_dir.exists():
        return None, None, None

    runs = sorted(runs_dir.iterdir(), reverse=True)
    if not runs:
        return None, None, None

    latest = runs[0]
    exports = latest / "exports"
    reports = latest / "reports"

    physicians = None
    mapping = None
    cluster_report = None

    if (exports / "canonical_physicians.csv").exists():
        physicians = pd.read_csv(exports / "canonical_physicians.csv")

    if (exports / "source_to_canonical_mapping.csv").exists():
        mapping = pd.read_csv(exports / "source_to_canonical_mapping.csv")

    if (reports / "cluster_report.json").exists():
        with open(reports / "cluster_report.json") as f:
            cluster_report = json.load(f)

    return physicians, mapping, cluster_report


physicians_df, mapping_df, cluster_report = load_data()

if physicians_df is None:
    st.error("No physician data found. Run the pipeline first.")
    st.stop()

# Search for a physician
st.subheader("🔍 Search for a Physician")

search_method = st.radio("Search by", ["Name", "NPI", "Canonical ID"])

if search_method == "Name":
    search_term = st.text_input("Enter name")
    if search_term:
        matches = physicians_df[
            physicians_df["name"].str.contains(search_term, case=False, na=False)
        ]
elif search_method == "NPI":
    search_term = st.text_input("Enter NPI")
    if search_term:
        matches = physicians_df[physicians_df["npi"] == search_term]
else:
    search_term = st.text_input("Enter Canonical ID")
    if search_term:
        matches = physicians_df[physicians_df["canonical_id"] == search_term]

if "search_term" in dir() and search_term:
    if len(matches) == 0:
        st.warning("No matches found")
    else:
        st.success(f"Found {len(matches)} match(es)")

        for _, phys in matches.iterrows():
            with st.expander(f"📋 {phys['name']} ({phys['canonical_id']})", expanded=True):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.write("**Basic Info**")
                    st.write(f"- Name: {phys['name']}")
                    st.write(f"- NPI: {phys['npi'] or 'N/A'}")
                    st.write(f"- Specialty: {phys['specialty'] or 'N/A'}")

                with col2:
                    st.write("**Location**")
                    st.write(f"- Facility: {phys['primary_facility'] or 'N/A'}")
                    st.write(f"- City: {phys['city'] or 'N/A'}")
                    st.write(f"- State: {phys['state'] or 'N/A'}")

                with col3:
                    st.write("**Resolution Info**")
                    st.write(f"- Confidence: {phys['confidence']:.2%}")
                    st.write(f"- Source Records: {phys['source_count']}")

                # Show source records if mapping available
                if mapping_df is not None:
                    source_records = mapping_df[mapping_df["canonical_id"] == phys["canonical_id"]]
                    st.write(f"**Source Record IDs ({len(source_records)}):**")
                    st.dataframe(source_records, use_container_width=True, hide_index=True)

# Cluster analysis
st.subheader("📊 Cluster Analysis")

if cluster_report:
    col1, col2, col3 = st.columns(3)

    size_analysis = cluster_report.get("size_analysis", {})
    quality_analysis = cluster_report.get("quality_analysis", {})

    with col1:
        st.metric("Total Clusters", size_analysis.get("total_clusters", "N/A"))
    with col2:
        st.metric("Avg Quality Score", f"{quality_analysis.get('avg_quality_score', 0):.2f}")
    with col3:
        st.metric("NPI Conflicts", quality_analysis.get("npi_conflict_clusters", "N/A"))

    # Size distribution
    st.write("**Cluster Size Distribution**")
    size_dist = size_analysis.get("size_distribution", {})
    if size_dist:
        dist_df = pd.DataFrame([{"Category": k, "Count": v} for k, v in size_dist.items()])
        st.bar_chart(dist_df.set_index("Category"))

    # Quality distribution
    st.write("**Quality Distribution**")
    qual_col1, qual_col2, qual_col3 = st.columns(3)
    with qual_col1:
        st.metric("High Quality (≥0.8)", quality_analysis.get("high_quality_count", 0))
    with qual_col2:
        st.metric("Medium Quality", quality_analysis.get("medium_quality_count", 0))
    with qual_col3:
        st.metric("Low Quality (<0.5)", quality_analysis.get("low_quality_count", 0))
else:
    st.info("Cluster report not available")
