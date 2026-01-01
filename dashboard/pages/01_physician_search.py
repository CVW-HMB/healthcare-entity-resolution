"""Physician search page."""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

st.set_page_config(page_title="Physician Search", page_icon="🔍", layout="wide")
st.title("🔍 Physician Search")


@st.cache_data
def load_physicians():
    """Load canonical physicians from most recent run."""
    from physician_resolution.config import OUTPUTS_DIR

    runs_dir = OUTPUTS_DIR / "runs"
    if not runs_dir.exists():
        return None

    runs = sorted(runs_dir.iterdir(), reverse=True)
    if not runs:
        return None

    csv_path = runs[0] / "exports" / "canonical_physicians.csv"
    if not csv_path.exists():
        return None

    return pd.read_csv(csv_path)


# Load data
df = load_physicians()

if df is None:
    st.error("No physician data found. Run the pipeline first.")
    st.stop()

st.success(f"Loaded {len(df)} physicians")

# Filters
st.sidebar.header("Filters")

# State filter
states = sorted(df["state"].dropna().unique())
selected_states = st.sidebar.multiselect("State", states)

# Specialty filter
specialties = sorted(df["specialty"].dropna().unique())
selected_specialties = st.sidebar.multiselect("Specialty", specialties)

# Confidence filter
min_confidence = st.sidebar.slider(
    "Minimum Confidence",
    min_value=0.0,
    max_value=1.0,
    value=0.0,
    step=0.05,
)

# Name search
name_search = st.sidebar.text_input("Search by Name")

# Apply filters
filtered_df = df.copy()

if selected_states:
    filtered_df = filtered_df[filtered_df["state"].isin(selected_states)]

if selected_specialties:
    filtered_df = filtered_df[filtered_df["specialty"].isin(selected_specialties)]

if min_confidence > 0:
    filtered_df = filtered_df[filtered_df["confidence"] >= min_confidence]

if name_search:
    filtered_df = filtered_df[filtered_df["name"].str.contains(name_search, case=False, na=False)]

# Display results
st.subheader(f"Results: {len(filtered_df)} physicians")

# Metrics row
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Matching", len(filtered_df))
with col2:
    avg_conf = filtered_df["confidence"].mean() if len(filtered_df) > 0 else 0
    st.metric("Avg Confidence", f"{avg_conf:.2f}")
with col3:
    with_npi = filtered_df["npi"].notna().sum()
    st.metric("With NPI", with_npi)
with col4:
    avg_sources = filtered_df["source_count"].mean() if len(filtered_df) > 0 else 0
    st.metric("Avg Sources", f"{avg_sources:.1f}")

# Data table
st.dataframe(
    filtered_df[
        [
            "canonical_id",
            "name",
            "specialty",
            "primary_facility",
            "city",
            "state",
            "confidence",
            "npi",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)

# Download button
csv = filtered_df.to_csv(index=False)
st.download_button(
    label="Download CSV",
    data=csv,
    file_name="physicians_filtered.csv",
    mime="text/csv",
)
