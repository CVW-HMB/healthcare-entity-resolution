"""Streamlit dashboard for physician entity resolution."""

import sys
from pathlib import Path

import streamlit as st

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

st.set_page_config(
    page_title="Physician Entity Resolution",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🏥 Physician Entity Resolution")
st.markdown("""
Welcome to the Physician Entity Resolution dashboard. This tool helps MedTech sales teams:

- **Find physicians** by specialty, location, and procedure volume
- **Explore referral networks** to understand physician relationships
- **Trace data provenance** to see how physician records were resolved
- **Monitor data quality** and entity resolution metrics

### Getting Started

Use the sidebar to navigate between pages:

1. **Physician Search** - Find and filter physicians
2. **Referral Network** - Visualize physician connections
3. **Data Provenance** - See how records were matched
4. **Resolution Stats** - Pipeline quality metrics

### Data Status
""")

# Try to load some basic stats
try:
    from physician_resolution.config import OUTPUTS_DIR

    # Find most recent run
    runs_dir = OUTPUTS_DIR / "runs"
    if runs_dir.exists():
        runs = sorted(runs_dir.iterdir(), reverse=True)
        if runs:
            latest_run = runs[0]
            st.success(f"✅ Latest pipeline run: `{latest_run.name}`")

            # Check for exports
            exports_dir = latest_run / "exports"
            if exports_dir.exists():
                files = list(exports_dir.glob("*.csv"))
                st.info(f"📁 {len(files)} export files available")
        else:
            st.warning("⚠️ No pipeline runs found. Run `python scripts/run_pipeline.py` first.")
    else:
        st.warning("⚠️ No pipeline runs found. Run `python scripts/run_pipeline.py` first.")

except Exception as e:
    st.error(f"Error loading data: {e}")
    st.info("Make sure you've run the pipeline first.")
