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

# Tier 1 UI: Inter font, hide chrome, style dropzone, sticky footer.
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif; }
[data-testid="stStatusWidget"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stFileUploaderDropzone"] {
    border: 2px dashed #00695C !important;
    border-radius: 14px !important;
    background-color: #FFFFFF !important;
    padding: 2rem 1.5rem !important;
}
[data-testid="stFileUploaderDropzone"] button {
    background-color: #00695C !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.6rem 1.8rem !important;
    font-weight: 600 !important;
}
.sticky-footer {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background-color: #FFFFFF;
    border-top: 1px solid #E0E0E0;
    padding: 8px 24px;
    font-size: 0.78rem;
    color: #757575;
    z-index: 999;
    text-align: center;
}
.main .block-container,
[data-testid="stMainBlockContainer"],
section[data-testid="stMain"] > div {
    padding-top: 2rem !important;
    padding-bottom: 60px !important;
}
[data-testid="stSidebar"] .block-container,
[data-testid="stSidebarUserContent"],
[data-testid="stSidebar"] > div {
    padding-top: 1.5rem !important;
}
/* Hide the Streamlit header bar (60px white space at top) */
header[data-testid="stHeader"],
.stAppHeader {
    display: none !important;
}
/* Sidebar top spacing - aggressive multi-selector */
section[data-testid="stSidebar"],
[data-testid="stSidebar"],
.st-emotion-cache-10p9htt {
    padding-top: 0 !important;
    margin-top: 0 !important;
}
section[data-testid="stSidebar"] > div,
[data-testid="stSidebar"] > div {
    padding-top: 0.5rem !important;
}
</style>
""", unsafe_allow_html=True)

# Sticky footer renders at top of script so it's visible even during analysis.
st.markdown(
    '<div class="sticky-footer">CadenceCare is a screening and trend-monitoring aid'
    ', not a medical device. Gait analysis uses pose estimation (MediaPipe).</div>',
    unsafe_allow_html=True,
)

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
    locked = (st.session_state.get("analysing", False)
          or st.session_state.get("analysis_phase") in (2, 3))
    choice = st.sidebar.radio(
        "Page", list(PAGES), label_visibility="collapsed",
        disabled=locked,
    )
    st.sidebar.divider()
    # Technical details checkbox moved to bottom of sidebar (after page content).
    # Read current value here so pages can use it during render.
    show_technical = st.session_state.get("show_technical", False)
    if locked:
        st.sidebar.caption("Sidebar is disabled during analysis and will be re-enabled when it finishes.")

    PAGES[choice](cfg)

    # Technical details at bottom of sidebar
    st.sidebar.divider()
    new_technical = st.sidebar.checkbox(
        "Technical details",
        value=show_technical,
        help="Show pipeline internals: algorithm version, technical caveats, diagnostic detail.",
        disabled=locked,
    )
    if new_technical != show_technical:
        st.session_state["show_technical"] = new_technical
        st.rerun()
    if new_technical:
        st.sidebar.caption("Flag thresholds (illustrative):")
        _render_thresholds(cfg)

    # Show storage backend unconditionally (which DB are we on?)
    try:
        from app.shared import open_repository
        _repo = open_repository(cfg)
        _backend = getattr(_repo, "backend", "?")
        st.sidebar.caption(f"Storage: {_backend}")
        _note = getattr(_repo, "backend_note", None)
        if _note:
            st.sidebar.caption(f":orange[{_note}]")
    except Exception:
        pass

    # Footer now sticky (rendered above via CSS).


main()
