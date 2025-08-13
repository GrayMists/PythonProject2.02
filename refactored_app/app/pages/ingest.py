"""Data ingestion page."""

from __future__ import annotations

import streamlit as st


def render() -> None:
    """Render the data ingestion page."""
    st.title("Upload Sales Data")
    uploaded = st.file_uploader("CSV file")
    if uploaded is not None:
        st.success("File uploaded: %s" % uploaded.name)
