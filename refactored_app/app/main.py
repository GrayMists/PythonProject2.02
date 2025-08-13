"""Streamlit application entry point."""

from __future__ import annotations

import streamlit as st

from . import config
from .pages import analysis, ingest

PAGES = {"Analysis": analysis, "Ingest": ingest}


def main() -> None:
    """Run the main application."""
    config.configure()
    st.sidebar.title("Navigation")
    selection = st.sidebar.radio("Go to", list(PAGES))
    page = PAGES[selection]
    page.render()


if __name__ == "__main__":
    main()
