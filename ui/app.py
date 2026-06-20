"""
Streamlit frontend — calls the FastAPI SSE stream and renders live agent steps + final report.
"""

import json
import os
import httpx
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Multi-Agent Research Assistant",
    page_icon="🔬",
    layout="wide",
)

# ── Styling ──────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .agent-card {
        background: #1e1e2e;
        border-left: 4px solid #7c6af7;
        border-radius: 6px;
        padding: 12px 16px;
        margin: 8px 0;
        font-family: monospace;
        font-size: 0.9em;
    }
    .agent-label {
        font-weight: 700;
        color: #cba6f7;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-size: 0.75em;
    }
    .agent-msg { color: #cdd6f4; margin-top: 4px; }
    .stMarkdown h1 { color: #cba6f7; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🔬 Multi-Agent Research Assistant")
st.caption(
    "Powered by **LangGraph** · **Groq + Llama 3** · **arXiv** — "
    "watches live as each agent thinks"
)
st.divider()

# ── Input ─────────────────────────────────────────────────────────────────────
col1, col2 = st.columns([4, 1])
with col1:
    query = st.text_input(
        "Research question",
        placeholder="e.g. What are the latest approaches to RAG for low-resource languages?",
        label_visibility="collapsed",
    )
with col2:
    run = st.button("🚀 Research", use_container_width=True, type="primary")

example_queries = [
    "Retrieval-augmented generation for low-resource languages",
    "Large language models for Arabic natural language processing",
    "Multimodal transformers for document understanding",
]
with st.expander("💡 Example queries", expanded=False):
    for eq in example_queries:
        if st.button(eq, key=eq):
            query = eq
            run = True

st.divider()

AGENT_ICONS = {
    "Orchestrator": "🧭",
    "Search Agent": "🔍",
    "Analysis Agent": "🧠",
    "Writer Agent": "✍️",
}


def render_trace_entry(entry: dict):
    agent = entry.get("agent", "Agent")
    icon = AGENT_ICONS.get(agent, "🤖")
    msg = entry.get("message", "")
    st.markdown(
        f"""
        <div class="agent-card">
            <div class="agent-label">{icon} {agent}</div>
            <div class="agent-msg">{msg}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


if run and query.strip():
    trace_container = st.container()
    report_placeholder = st.empty()

    with trace_container:
        st.subheader("🔄 Agent Activity")
        trace_display = st.empty()

    rendered_trace: list[dict] = []

    def refresh_trace():
        with trace_display.container():
            for entry in rendered_trace:
                render_trace_entry(entry)

    status = st.status("Running research pipeline...", expanded=True)

    try:
        with httpx.Client(timeout=120) as client:
            with client.stream(
                "POST",
                f"{API_BASE}/research/stream",
                json={"query": query},
                headers={"Accept": "text/event-stream"},
            ) as response:
                response.raise_for_status()

                for line in response.iter_lines():
                    if not line.startswith("data:"):
                        continue

                    raw = line[len("data:"):].strip()
                    if not raw:
                        continue

                    event = json.loads(raw)
                    etype = event.get("type")

                    if etype == "trace":
                        entry = event["entry"]
                        rendered_trace.append(entry)
                        refresh_trace()
                        status.update(
                            label=f"⏳ {entry['agent']}: {entry['message'][:80]}..."
                        )

                    elif etype == "done":
                        status.update(label="✅ Research complete!", state="complete")
                        report = event.get("report", "")
                        sources = event.get("sources", [])

                        st.divider()
                        st.subheader("📄 Research Report")
                        st.markdown(report)

                        if sources:
                            with st.expander(
                                f"📚 Sources ({len(sources)} papers)", expanded=False
                            ):
                                for i, src in enumerate(sources, 1):
                                    authors = ", ".join(src.get("authors", []))
                                    st.markdown(
                                        f"**[{i}] [{src['title']}]({src['url']})**  \n"
                                        f"{authors} · {src.get('published', '')}"
                                    )

                    elif etype == "error":
                        status.update(label="❌ Error", state="error")
                        st.error(f"Pipeline error: {event.get('message', 'Unknown error')}")

    except httpx.ConnectError:
        st.error(
            "⚠️ Cannot connect to the research API. "
            "Make sure FastAPI is running at `http://localhost:8000` "
            "(run `uvicorn api.main:app --reload` in the project root)."
        )
    except httpx.HTTPStatusError as e:
        st.error(f"API returned an error: {e.response.status_code} — {e.response.text}")
    except Exception as e:
        st.error(f"Unexpected error: {e}")

elif run and not query.strip():
    st.warning("Please enter a research question before clicking Research.")
