"""Streamlit configuration utilities."""

from __future__ import annotations

import streamlit as st


def configure() -> None:
    """Configure global Streamlit settings and theme."""
    st.set_page_config(page_title="Sales Analysis", page_icon="📊", layout="wide")
    st.write(
        """<style>
            .stApp {background-color: #fafafa;}
        </style>""",
        unsafe_allow_html=True,
    )
