"""Session state handling for the app."""

from __future__ import annotations

from dataclasses import dataclass

import streamlit as st


@dataclass
class AppState:
    """Central application state stored in ``st.session_state``."""

    product: str | None = None
    month: int | None = None
    page: int = 0


def get_state() -> AppState:
    """Return the current :class:`AppState` instance."""
    if "app_state" not in st.session_state:
        st.session_state["app_state"] = AppState()
    return st.session_state["app_state"]
