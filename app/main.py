"""Entry point for the gaitscreen pilot platform.

Run with::

    streamlit run app/main.py

Design intent for a pilot: the point of putting this in front of people is to
find out where it breaks on real footage, so the interface shows its working
rather than just its answers. Every unmeasurable metric states why, every
unreliable one carries its caveat inline, and detected gait events are plotted
over the raw signal so a tester can see whether the segmentation actually locked
on -- which is the failure a plausible-looking number would otherwise hide.
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Streamlit executes this file as a script, so the project root is not on the
# path and `import app.…` would fail without this.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
for directory in (PROJECT_ROOT, PROJECT_ROOT / "src"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

st.set_page_config(page_title="CadenceCare", page_icon="🚶", layout="wide")

from app.shared import get_config  # noqa: E402
from app.views import analyse, calibration, limitations, trends  # noqa: E402
from gaitscreen.version import ALGO_VERSION  # noqa: E402

PAGES = {
    "Analyse a walk": analyse.render,
    "Trends": trends.render,
    "Calibration": calibration.render,
    "Limitations": limitations.render,
}


_THRESHOLD_LABELS = {
    "gait_speed_mps": "Speed",
    "stride_time_cv_pct": "Step consistency",
    "step_length_asymmetry_pct": "Left/right evenness",
}


def _render_thresholds(cfg) -> None:
    """Show the active flag thresholds. Illustrative only, not clinical."""
    for key, label in _THRESHOLD_LABELS.items():
        thresh = cfg.get(f"flagging.absolute.{key}", {})
        parts = []
        for name, val in thresh.items():
            direction = ">" if "above" in name else "<"
            level = "high" if "high_risk" in name else "moderate"
            parts.append(f"{direction}{val} {level}")
        if parts:
            st.sidebar.caption(f"{label}: {', '.join(parts)}")


def main() -> None:
    cfg = get_config()

    st.sidebar.title("🚶 Gait screening")
    choice = st.sidebar.radio("Page", list(PAGES), label_visibility="collapsed")
    st.sidebar.divider()
    show_technical = st.sidebar.checkbox(
        "Technical details",
        value=st.session_state.get("show_technical", False),
        help="Show pipeline internals: algorithm version, technical caveats, diagnostic detail.",
    )
    st.session_state["show_technical"] = show_technical
    if show_technical:
        st.sidebar.caption("Flag thresholds (illustrative):")
        _render_thresholds(cfg)

    PAGES[choice](cfg)

    st.divider()
    st.caption(
        "CadenceCare is a screening and trend-monitoring aid \u2014 not a medical "
        "device. Analysis uses pose estimation (MediaPipe)."
    )


main()
