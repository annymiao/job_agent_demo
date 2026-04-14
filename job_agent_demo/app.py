from __future__ import annotations

import streamlit as st

from demo_core.analysis import (
    bar_width,
    compare_jobs,
    comparison_markdown,
    compact_company_title,
    fit_snapshot,
    fit_snapshot_markdown,
    interview_prep,
    interview_prep_markdown,
)
from demo_core.data import load_candidates, load_jobs
from demo_core.llm import llm_ready, polish_section, resolve_model


st.set_page_config(
    page_title="Job Agent Demo",
    layout="wide",
    initial_sidebar_state="expanded",
)


CUSTOM_CSS = """
<style>
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(218, 171, 98, 0.16), transparent 24%),
            radial-gradient(circle at bottom right, rgba(77, 106, 140, 0.22), transparent 28%),
            linear-gradient(180deg, #08101c 0%, #0d1726 48%, #111d2c 100%);
        color: #f5efe3;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(7, 14, 24, 0.96) 0%, rgba(12, 20, 31, 0.96) 100%);
        border-right: 1px solid rgba(206, 168, 104, 0.18);
    }
    .block-container {
        padding-top: 2.2rem;
        padding-bottom: 2.2rem;
    }
    .demo-hero {
        padding: 1.2rem 0 1.4rem 0;
        border-bottom: 1px solid rgba(214, 183, 131, 0.18);
        margin-bottom: 1.25rem;
        animation: fadeIn 0.45s ease-out;
    }
    .demo-kicker {
        text-transform: uppercase;
        letter-spacing: 0.18em;
        color: #cba66a;
        font-size: 0.75rem;
        margin-bottom: 0.65rem;
    }
    .demo-title {
        font-size: 3rem;
        line-height: 0.95;
        margin: 0;
        color: #f9f2e6;
    }
    .demo-subtitle {
        margin-top: 0.85rem;
        color: #c7d3df;
        max-width: 44rem;
        font-size: 1rem;
        line-height: 1.65;
    }
    .signal-rail {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.8rem;
        margin: 1.35rem 0 1.6rem 0;
    }
    .signal-tile {
        padding: 0.9rem 0 1rem 0;
        border-top: 1px solid rgba(214, 183, 131, 0.2);
    }
    .signal-label {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.16em;
        color: #95a6ba;
        margin-bottom: 0.4rem;
    }
    .signal-value {
        font-size: 1.65rem;
        color: #f7f0e2;
    }
    .section-shell {
        padding: 1rem 0 1.1rem 0;
        animation: fadeIn 0.55s ease-out;
    }
    .section-title {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.16em;
        color: #cba66a;
        margin-bottom: 0.65rem;
    }
    .section-note {
        color: #b9c7d7;
        margin-bottom: 1rem;
        max-width: 44rem;
    }
    .score-shell {
        margin: 1.1rem 0 1.3rem 0;
        border-top: 1px solid rgba(214, 183, 131, 0.18);
        padding-top: 0.95rem;
    }
    .score-headline {
        display: flex;
        justify-content: space-between;
        align-items: end;
        gap: 1rem;
        margin-bottom: 0.5rem;
    }
    .score-label {
        color: #f7f0e2;
        font-size: 1.45rem;
    }
    .score-number {
        color: #f5c977;
        font-size: 2.3rem;
        font-weight: 600;
    }
    .score-track {
        width: 100%;
        height: 10px;
        border-radius: 999px;
        background: rgba(245, 239, 227, 0.08);
        overflow: hidden;
        position: relative;
    }
    .score-fill {
        height: 100%;
        border-radius: 999px;
        background: linear-gradient(90deg, #c7923b 0%, #f1d098 55%, #f5b655 100%);
        box-shadow: 0 0 22px rgba(233, 193, 112, 0.3);
        animation: pulse 2.6s ease-in-out infinite;
    }
    .mini-bar {
        margin-bottom: 0.85rem;
    }
    .mini-label-row {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        color: #d8e2ed;
        font-size: 0.92rem;
        margin-bottom: 0.32rem;
    }
    .mini-track {
        width: 100%;
        height: 6px;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.08);
        overflow: hidden;
    }
    .mini-fill {
        height: 100%;
        border-radius: 999px;
        background: linear-gradient(90deg, rgba(203,166,106,0.85), rgba(245,208,152,0.95));
    }
    .list-block {
        border-top: 1px solid rgba(214, 183, 131, 0.18);
        padding-top: 0.95rem;
        min-height: 13rem;
    }
    .list-block ul {
        padding-left: 1.1rem;
        color: #d2dde9;
        line-height: 1.7;
    }
    .note-block {
        border-top: 1px solid rgba(214, 183, 131, 0.18);
        padding-top: 0.95rem;
        color: #c4d0de;
    }
    .ranking-row {
        border-top: 1px solid rgba(214, 183, 131, 0.14);
        padding: 0.95rem 0;
    }
    .ranking-header {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        gap: 1rem;
        margin-bottom: 0.35rem;
    }
    .ranking-title {
        color: #f8f1e4;
        font-size: 1.05rem;
    }
    .ranking-score {
        color: #f2c469;
        font-size: 1.15rem;
    }
    .ranking-sub {
        color: #9db0c5;
        font-size: 0.86rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-bottom: 0.35rem;
    }
    .ranking-copy {
        color: #d0dbe8;
        line-height: 1.65;
    }
    .polish-shell {
        border-top: 1px solid rgba(214, 183, 131, 0.18);
        margin-top: 1rem;
        padding-top: 1rem;
        color: #e0e8f0;
        white-space: pre-wrap;
    }
    .caption {
        color: #92a4ba;
        font-size: 0.88rem;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(6px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes pulse {
        0%, 100% { filter: brightness(1); }
        50% { filter: brightness(1.08); }
    }
</style>
"""


def render_signal_tile(label: str, value: str) -> str:
    return f"""
    <div class="signal-tile">
        <div class="signal-label">{label}</div>
        <div class="signal-value">{value}</div>
    </div>
    """


def render_component_bar(label: str, value: int) -> str:
    return f"""
    <div class="mini-bar">
        <div class="mini-label-row">
            <span>{label}</span>
            <span>{value}</span>
        </div>
        <div class="mini-track">
            <div class="mini-fill" style="width: {bar_width(value)};"></div>
        </div>
    </div>
    """


def list_to_markdown(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def maybe_render_polish(section_key: str, payload: dict):
    button_key = f"polish_button_{section_key}"
    content_key = f"polish_content_{section_key}"

    if llm_ready():
        if st.button("Polish This View With Live Model", key=button_key):
            with st.spinner(f"Polishing {section_key.replace('_', ' ')} with {resolve_model()}..."):
                st.session_state[content_key] = polish_section(section_key, payload)

        polished = st.session_state.get(content_key, "")
        if polished:
            st.markdown(
                f"""
                <div class="polish-shell">
                    <div class="section-title">Live Narrative Polish</div>
                    {polished}
                </div>
                """,
                unsafe_allow_html=True,
            )


st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

candidates = load_candidates()
jobs = load_jobs()

candidate_options = {candidate["name"]: candidate for candidate in candidates}
job_options = {compact_company_title(job): job for job in jobs}

with st.sidebar:
    st.markdown("### Demo Controls")
    selected_candidate_name = st.selectbox("Sample Candidate", list(candidate_options.keys()))
    selected_job_name = st.selectbox("Primary Job", list(job_options.keys()))
    default_compare = list(job_options.keys())[:3]
    compare_selection = st.multiselect(
        "Comparison Basket",
        list(job_options.keys()),
        default=default_compare,
        max_selections=4,
    )
    st.markdown("---")
    if llm_ready():
        st.caption(f"Live polish enabled via `{resolve_model()}`.")
    else:
        st.caption("Running in deterministic demo mode. Add `.env` values to enable optional live polish.")

candidate = candidate_options[selected_candidate_name]
primary_job = job_options[selected_job_name]
compare_jobs_list = [job_options[label] for label in compare_selection] or [primary_job]

snapshot = fit_snapshot(candidate, primary_job)
comparison = compare_jobs(candidate, compare_jobs_list)
prep = interview_prep(candidate, primary_job)

st.markdown(
    f"""
    <section class="demo-hero">
        <div class="demo-kicker">Public Demo Surface</div>
        <h1 class="demo-title">job agent demo</h1>
        <div class="demo-subtitle">
            A small, GitHub-ready showcase that demonstrates role fit judgment, shortlist prioritization,
            and interview preparation without exposing the private orchestration layer behind the full system.
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="signal-rail">
        """
    + render_signal_tile("Candidate", candidate["name"])
    + render_signal_tile("Primary Role", primary_job["title"])
    + render_signal_tile("Company", primary_job["company"])
    + render_signal_tile("Fit Signal", f"{snapshot['fit_score']}/100")
    + """
    </div>
    """,
    unsafe_allow_html=True,
)

fit_tab, compare_tab, prep_tab = st.tabs(["Fit Snapshot", "Offer Comparison", "Interview Prep Brief"])

with fit_tab:
    st.markdown(
        """
        <div class="section-shell">
            <div class="section-title">Single-role readout</div>
            <div class="section-note">
                This view compresses the candidate-vs-role judgment into one public-facing decision sheet:
                overall fit, evidence, risks, and positioning guidance.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="score-shell">
            <div class="score-headline">
                <div class="score-label">{snapshot['readiness']}</div>
                <div class="score-number">{snapshot['fit_score']}</div>
            </div>
            <div class="score-track">
                <div class="score-fill" style="width: {bar_width(snapshot['fit_score'])};"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1, 1])
    with left:
        st.markdown(
            '<div class="section-title">Component Scores</div>',
            unsafe_allow_html=True,
        )
        for key, value in snapshot["component_scores"].items():
            st.markdown(render_component_bar(key.title(), value), unsafe_allow_html=True)

    with right:
        st.markdown(
            '<div class="note-block"><div class="section-title">Signal Notes</div></div>',
            unsafe_allow_html=True,
        )
        st.markdown(list_to_markdown([f"{key.title()}: {value}" for key, value in snapshot["notes"].items() if isinstance(value, str)]))

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown('<div class="list-block"><div class="section-title">Strong Matches</div></div>', unsafe_allow_html=True)
        st.markdown(list_to_markdown(snapshot["strong_matches"]))
    with col_b:
        st.markdown('<div class="list-block"><div class="section-title">Primary Risks</div></div>', unsafe_allow_html=True)
        st.markdown(list_to_markdown(snapshot["risks"]))
    with col_c:
        st.markdown('<div class="list-block"><div class="section-title">Positioning Advice</div></div>', unsafe_allow_html=True)
        st.markdown(list_to_markdown(snapshot["positioning_advice"]))

    st.markdown('<div class="section-title">Evidence Grid</div>', unsafe_allow_html=True)
    if snapshot["evidence_grid"]:
        st.table(snapshot["evidence_grid"])
    else:
        st.caption("No direct evidence matches in the simplified demo logic.")

    st.download_button(
        "Download Fit Snapshot (.md)",
        data=fit_snapshot_markdown(candidate, primary_job, snapshot),
        file_name="fit_snapshot.md",
        mime="text/markdown",
    )
    maybe_render_polish("fit_snapshot", {"candidate": candidate["name"], "job": compact_company_title(primary_job), "snapshot": snapshot})

with compare_tab:
    st.markdown(
        """
        <div class="section-shell">
            <div class="section-title">Shortlist sequencing</div>
            <div class="section-note">
                This view is intentionally about decisions rather than copy generation:
                what to prioritize now, what to keep warm, and where the main tradeoffs sit.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title">Recommendation</div>', unsafe_allow_html=True)
    st.markdown(list_to_markdown(comparison["summary"]))

    st.markdown('<div class="section-title">Ranked Roles</div>', unsafe_allow_html=True)
    for row in comparison["ranking"]:
        st.markdown(
            f"""
            <div class="ranking-row">
                <div class="ranking-header">
                    <div class="ranking-title">{row['rank']}. {row['company']} - {row['title']}</div>
                    <div class="ranking-score">{row['fit_score']}/100</div>
                </div>
                <div class="ranking-sub">{row['posture']} · {row['readiness']}</div>
                <div class="ranking-copy">{row['tradeoff']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.download_button(
        "Download Comparison (.md)",
        data=comparison_markdown(candidate, comparison),
        file_name="offer_comparison.md",
        mime="text/markdown",
    )
    maybe_render_polish("offer_comparison", {"candidate": candidate["name"], "comparison": comparison})

with prep_tab:
    st.markdown(
        """
        <div class="section-shell">
            <div class="section-title">Interview prep brief</div>
            <div class="section-note">
                This page turns the role fit readout into a short preparation pack:
                probable questions, strongest stories, and due-diligence angles.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.05, 0.95])
    with left:
        st.markdown('<div class="section-title">Likely Questions</div>', unsafe_allow_html=True)
        st.markdown(list_to_markdown(prep["likely_questions"]))
        st.markdown('<div class="section-title">Prep Focus</div>', unsafe_allow_html=True)
        st.markdown(list_to_markdown(prep["prep_focus"]))

    with right:
        st.markdown('<div class="section-title">Due Diligence</div>', unsafe_allow_html=True)
        st.markdown(list_to_markdown(prep["due_diligence"]))

    st.markdown('<div class="section-title">Story Map</div>', unsafe_allow_html=True)
    story_rows = [
        {
            "project": item["project_name"],
            "why_relevant": item["why_relevant"],
            "interview_angle": item["interview_angle"],
            "proof_point": item["proof_point"],
        }
        for item in prep["story_map"]
    ]
    st.table(story_rows)

    st.download_button(
        "Download Interview Prep (.md)",
        data=interview_prep_markdown(candidate, primary_job, prep),
        file_name="interview_prep_brief.md",
        mime="text/markdown",
    )
    maybe_render_polish("interview_prep", {"candidate": candidate["name"], "job": compact_company_title(primary_job), "prep": prep})

st.markdown(
    """
    <div class="caption">
        The app runs entirely on synthetic sample data and intentionally simplified public logic.
        It demonstrates output quality and workflow shape without exposing the private orchestration layer.
    </div>
    """,
    unsafe_allow_html=True,
)
