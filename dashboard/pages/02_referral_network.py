"""Referral network visualization page."""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

st.set_page_config(page_title="Referral Network", page_icon="🕸️", layout="wide")
st.title("🕸️ Referral Network Explorer")


@st.cache_data
def load_data():
    """Load physicians and influence scores."""
    from physician_resolution.config import OUTPUTS_DIR

    runs_dir = OUTPUTS_DIR / "runs"
    if not runs_dir.exists():
        return None, None

    runs = sorted(runs_dir.iterdir(), reverse=True)
    if not runs:
        return None, None

    latest = runs[0] / "exports"

    physicians_path = latest / "canonical_physicians.csv"
    influence_path = latest / "influence_scores.csv"

    physicians = pd.read_csv(physicians_path) if physicians_path.exists() else None
    influence = pd.read_csv(influence_path) if influence_path.exists() else None

    return physicians, influence


physicians_df, influence_df = load_data()

if physicians_df is None:
    st.error("No physician data found. Run the pipeline first.")
    st.stop()

# Merge influence scores
if influence_df is not None:
    physicians_df = physicians_df.merge(
        influence_df,
        left_on="canonical_id",
        right_on="canonical_id",
        how="left",
    )
    physicians_df["influence_score"] = physicians_df["influence_score"].fillna(0)
else:
    physicians_df["influence_score"] = 0

st.success(f"Loaded {len(physicians_df)} physicians")

# Top influencers
st.subheader("🏆 Top Influencers (by PageRank)")

top_n = st.slider("Number of top influencers", 5, 50, 20)

top_influencers = physicians_df.nlargest(top_n, "influence_score")[
    ["canonical_id", "name", "specialty", "state", "influence_score"]
]

st.dataframe(top_influencers, use_container_width=True, hide_index=True)

# Influence distribution
st.subheader("📊 Influence Score Distribution")

fig = px.histogram(
    physicians_df[physicians_df["influence_score"] > 0],
    x="influence_score",
    nbins=50,
    title="Distribution of Influence Scores",
)
st.plotly_chart(fig, use_container_width=True)

# By specialty
st.subheader("📋 Influence by Specialty")

specialty_influence = (
    physicians_df.groupby("specialty")["influence_score"]
    .agg(["mean", "sum", "count"])
    .reset_index()
    .sort_values("sum", ascending=False)
    .head(15)
)
specialty_influence.columns = ["Specialty", "Avg Influence", "Total Influence", "Count"]

fig2 = px.bar(
    specialty_influence,
    x="Specialty",
    y="Total Influence",
    title="Total Influence by Specialty",
)
st.plotly_chart(fig2, use_container_width=True)

# Network visualization placeholder
st.subheader("🕸️ Network Visualization")
st.info(
    "Interactive network visualization requires building the referral graph. "
    "Select a physician to see their network."
)

selected_physician = st.selectbox(
    "Select a physician to explore their network",
    options=physicians_df["canonical_id"].tolist(),
    format_func=lambda x: physicians_df[physicians_df["canonical_id"] == x]["name"].values[0]
    if len(physicians_df[physicians_df["canonical_id"] == x]) > 0
    else x,
)

if selected_physician:
    phys_data = physicians_df[physicians_df["canonical_id"] == selected_physician].iloc[0]

    col1, col2 = st.columns(2)
    with col1:
        st.write("**Name:**", phys_data.get("name", "N/A"))
        st.write("**Specialty:**", phys_data.get("specialty", "N/A"))
        st.write(
            "**Location:**", f"{phys_data.get('city', 'N/A')}, {phys_data.get('state', 'N/A')}"
        )
    with col2:
        st.write("**NPI:**", phys_data.get("npi", "N/A"))
        st.write("**Influence Score:**", f"{phys_data.get('influence_score', 0):.6f}")
        st.write("**Source Records:**", phys_data.get("source_count", "N/A"))
