"""Reusable filter components for the dashboard."""

import pandas as pd
import streamlit as st


def state_filter(df: pd.DataFrame, column: str = "state") -> list[str]:
    """
    Render a state multiselect filter.

    Args:
        df: DataFrame containing state data
        column: Column name for state

    Returns:
        List of selected states
    """
    if column not in df.columns:
        return []

    states = sorted(df[column].dropna().unique())
    return st.multiselect("State", states, key=f"state_filter_{column}")


def specialty_filter(df: pd.DataFrame, column: str = "specialty") -> list[str]:
    """
    Render a specialty multiselect filter.

    Args:
        df: DataFrame containing specialty data
        column: Column name for specialty

    Returns:
        List of selected specialties
    """
    if column not in df.columns:
        return []

    specialties = sorted(df[column].dropna().unique())
    return st.multiselect("Specialty", specialties, key=f"specialty_filter_{column}")


def confidence_filter(
    min_val: float = 0.0,
    max_val: float = 1.0,
    default: float = 0.0,
) -> float:
    """
    Render a confidence slider filter.

    Args:
        min_val: Minimum slider value
        max_val: Maximum slider value
        default: Default value

    Returns:
        Selected minimum confidence
    """
    return st.slider(
        "Minimum Confidence",
        min_value=min_val,
        max_value=max_val,
        value=default,
        step=0.05,
        key="confidence_filter",
    )


def name_search_filter() -> str:
    """
    Render a name search text input.

    Returns:
        Search string
    """
    return st.text_input("Search by Name", key="name_search_filter")


def apply_filters(
    df: pd.DataFrame,
    states: list[str] | None = None,
    specialties: list[str] | None = None,
    min_confidence: float | None = None,
    name_search: str | None = None,
    state_col: str = "state",
    specialty_col: str = "specialty",
    confidence_col: str = "confidence",
    name_col: str = "name",
) -> pd.DataFrame:
    """
    Apply multiple filters to a DataFrame.

    Args:
        df: DataFrame to filter
        states: List of states to include
        specialties: List of specialties to include
        min_confidence: Minimum confidence threshold
        name_search: Name search string
        state_col: Column name for state
        specialty_col: Column name for specialty
        confidence_col: Column name for confidence
        name_col: Column name for name

    Returns:
        Filtered DataFrame
    """
    filtered = df.copy()

    if states and state_col in filtered.columns:
        filtered = filtered[filtered[state_col].isin(states)]

    if specialties and specialty_col in filtered.columns:
        filtered = filtered[filtered[specialty_col].isin(specialties)]

    if min_confidence is not None and min_confidence > 0 and confidence_col in filtered.columns:
        filtered = filtered[filtered[confidence_col] >= min_confidence]

    if name_search and name_col in filtered.columns:
        filtered = filtered[filtered[name_col].str.contains(name_search, case=False, na=False)]

    return filtered


def render_sidebar_filters(df: pd.DataFrame) -> dict:
    """
    Render a complete set of filters in the sidebar.

    Args:
        df: DataFrame to create filters for

    Returns:
        Dict with filter values
    """
    st.sidebar.header("Filters")

    filters = {
        "states": state_filter(df) if "state" in df.columns else [],
        "specialties": specialty_filter(df) if "specialty" in df.columns else [],
        "min_confidence": confidence_filter() if "confidence" in df.columns else 0.0,
        "name_search": name_search_filter() if "name" in df.columns else "",
    }

    return filters
