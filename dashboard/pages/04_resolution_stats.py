"""Resolution statistics page."""

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

st.set_page_config(page_title="Resolution Stats", page_icon="📈", layout="wide")
st.title("📈 Entity Resolution Statistics")


@st.cache_data
def load_reports():
    """Load all reports from most recent run."""
    from physician_resolution.config import OUTPUTS_DIR

    runs_dir = OUTPUTS_DIR / "runs"
    if not runs_dir.exists():
        return None

    runs = sorted(runs_dir.iterdir(), reverse=True)
    if not runs:
        return None

    reports_dir = runs[0] / "reports"
    reports = {}

    for report_file in reports_dir.glob("*.json"):
        with open(report_file) as f:
            reports[report_file.stem] = json.load(f)

    return reports


reports = load_reports()

if not reports:
    st.error("No reports found. Run the pipeline first.")
    st.stop()

# Tabs for different reports
tab1, tab2, tab3 = st.tabs(["📊 Data Quality", "🔗 Match Quality", "🎯 Cluster Quality"])

with tab1:
    st.subheader("Data Quality Report")

    data_quality = reports.get("data_quality", {})
    summary = data_quality.get("summary", {})

    if summary:
        st.write("### Overall Coverage")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Records", summary.get("total_records", 0))
        with col2:
            st.metric("NPI Coverage", f"{summary.get('npi_coverage', 0):.1%}")
        with col3:
            st.metric("Name Coverage", f"{summary.get('name_coverage', 0):.1%}")
        with col4:
            st.metric("Location Coverage", f"{summary.get('location_coverage', 0):.1%}")

        # Per-source breakdown
        st.write("### Coverage by Source")
        sources = summary.get("sources", {})
        if sources:
            source_data = []
            for source, metrics in sources.items():
                source_data.append(
                    {
                        "Source": source,
                        "Records": metrics.get("record_count", 0),
                        "NPI Coverage": metrics.get("npi_coverage", 0),
                        "Name Coverage": metrics.get("name_coverage", 0),
                        "Specialty Coverage": metrics.get("specialty_coverage", 0),
                    }
                )

            source_df = pd.DataFrame(source_data)
            st.dataframe(source_df, use_container_width=True, hide_index=True)

            # Bar chart
            fig = px.bar(
                source_df,
                x="Source",
                y="Records",
                title="Records by Source",
            )
            st.plotly_chart(fig, use_container_width=True)

    # Duplicate analysis
    dup_analysis = data_quality.get("duplicate_analysis", {})
    if dup_analysis:
        st.write("### NPI Quality")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total NPIs", dup_analysis.get("total_npis", 0))
        with col2:
            st.metric("NPIs with Multiple Names", dup_analysis.get("npis_with_multiple_names", 0))

with tab2:
    st.subheader("Match Quality Report")

    match_quality = reports.get("match_quality", {})
    match_summary = match_quality.get("summary", {})

    if match_summary:
        st.write("### Match Decisions")
        col1, col2, col3, col4 = st.columns(4)

        decisions = match_summary.get("decisions", {})
        with col1:
            st.metric("Total Comparisons", match_summary.get("total_comparisons", 0))
        with col2:
            st.metric("Matches", decisions.get("match", 0))
        with col3:
            st.metric("Non-Matches", decisions.get("non_match", 0))
        with col4:
            st.metric("Uncertain", decisions.get("uncertain", 0))

        # Match rate
        st.metric("Match Rate", f"{match_summary.get('match_rate', 0):.2%}")

        # Match types
        st.write("### Match Types")
        match_types = match_summary.get("match_types", {})
        if match_types:
            fig = px.pie(
                values=list(match_types.values()),
                names=list(match_types.keys()),
                title="Match Type Distribution",
            )
            st.plotly_chart(fig, use_container_width=True)

    # Confidence analysis
    conf_analysis = match_quality.get("confidence_analysis", {})
    if conf_analysis:
        st.write("### Confidence Distribution")
        conf_dist = conf_analysis.get("confidence_distribution", {})
        if conf_dist:
            conf_df = pd.DataFrame([{"Level": k, "Count": v} for k, v in conf_dist.items()])
            fig = px.bar(conf_df, x="Level", y="Count", title="Match Confidence Levels")
            st.plotly_chart(fig, use_container_width=True)

    # Low confidence matches
    low_conf = match_quality.get("low_confidence_matches", [])
    if low_conf:
        st.write("### ⚠️ Low Confidence Matches (for review)")
        st.dataframe(pd.DataFrame(low_conf), use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Cluster Quality Report")

    cluster_report = reports.get("cluster_report", {})

    # Size analysis
    size_analysis = cluster_report.get("size_analysis", {})
    if size_analysis:
        st.write("### Cluster Sizes")
        col1, col2, col3 = st.columns(3)

        size_stats = size_analysis.get("size_stats", {})
        with col1:
            st.metric("Total Clusters", size_analysis.get("total_clusters", 0))
        with col2:
            st.metric("Avg Size", f"{size_stats.get('mean', 0):.1f}")
        with col3:
            st.metric("Max Size", size_stats.get("max", 0))

        # Size distribution
        size_dist = size_analysis.get("size_distribution", {})
        if size_dist:
            dist_df = pd.DataFrame([{"Category": k, "Count": v} for k, v in size_dist.items()])
            fig = px.bar(dist_df, x="Category", y="Count", title="Cluster Size Distribution")
            st.plotly_chart(fig, use_container_width=True)

    # Quality analysis
    quality_analysis = cluster_report.get("quality_analysis", {})
    if quality_analysis:
        st.write("### Cluster Quality")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Avg Quality Score", f"{quality_analysis.get('avg_quality_score', 0):.2f}")
        with col2:
            st.metric("NPI Conflicts", quality_analysis.get("npi_conflict_clusters", 0))
        with col3:
            st.metric("Problematic Clusters", quality_analysis.get("problematic_clusters", 0))

        # Sample issues
        sample_issues = quality_analysis.get("sample_issues", [])
        if sample_issues:
            st.write("### ⚠️ Sample Problematic Clusters")
            for issue in sample_issues[:5]:
                with st.expander(
                    f"Cluster {issue['cluster_id']} (size={issue['size']}, score={issue['quality_score']:.2f})"
                ):
                    for warning in issue.get("warnings", []):
                        st.warning(warning)

    # Physician analysis
    phys_analysis = cluster_report.get("physician_analysis", {})
    if phys_analysis:
        st.write("### Final Physician Statistics")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Physicians", phys_analysis.get("total_physicians", 0))
        with col2:
            st.metric("NPI Coverage", f"{phys_analysis.get('npi_coverage', 0):.1%}")
        with col3:
            conf_stats = phys_analysis.get("confidence_stats", {})
            st.metric("Avg Confidence", f"{conf_stats.get('mean', 0):.2f}")

        # Top states
        st.write("### Top States")
        top_states = phys_analysis.get("top_states", {})
        if top_states:
            states_df = pd.DataFrame([{"State": k, "Count": v} for k, v in top_states.items()])
            fig = px.bar(states_df, x="State", y="Count", title="Physicians by State")
            st.plotly_chart(fig, use_container_width=True)
