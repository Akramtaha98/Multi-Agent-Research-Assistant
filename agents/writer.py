"""
Writer Agent — synthesizes analysis into a structured markdown research report.
"""

import json
from langchain_core.messages import SystemMessage, HumanMessage
from agents.llm import get_llm
from graph.state import ResearchState, AgentTraceEntry


WRITER_SYSTEM = """You are an academic research writer. Write a clear, structured research synthesis report in Markdown.

Format the report exactly as:

# Research Summary: <topic>

## Introduction
<2–3 sentence overview of the research landscape>

## Key Findings by Theme

### <Theme 1 Name>
<Synthesized paragraph referencing specific papers using [N] citation markers>

### <Theme 2 Name>
...

## Contradictions & Open Questions
<If contradictions exist, describe them and which papers disagree. If none, briefly note consensus.>

## Conclusion
<2–3 sentence takeaway>

## References
<numbered list of all cited papers>

Rules:
- Use [N] inline citations that match the numbered References list
- Reference ONLY papers that were actually provided — never invent sources
- Keep it academic but readable — suitable for a PhD audience
- Length: 400–700 words
"""


def writer_node(state: ResearchState) -> dict:
    if state.get("error"):
        return {
            "final_report": f"# Error\n\n{state['error']}",
            "agent_trace": [
                {
                    "agent": "Writer Agent",
                    "message": "Skipped — no papers to synthesize.",
                    "data": {},
                }
            ],
        }

    llm = get_llm(temperature=0.3, max_tokens=2048, speed="smart")

    # Build sources reference for the writer
    sources_text = ""
    for i, src in enumerate(state["sources"], 1):
        authors = ", ".join(src["authors"])
        sources_text += f"[{i}] {src['title']} — {authors} ({src['published']}) — {src['url']}\n"

    analysis_json = json.dumps(state["analysis"], separators=(",", ":"))

    messages = [
        SystemMessage(content=WRITER_SYSTEM),
        HumanMessage(
            content=(
                f"Research question: {state['query']}\n\n"
                f"Analysis:\n{analysis_json}\n\n"
                f"Full source list:\n{sources_text}"
            )
        ),
    ]

    response = llm.invoke(messages)
    report = response.content.strip()

    trace_entry: AgentTraceEntry = {
        "agent": "Writer Agent",
        "message": f"Compiled final report ({len(report.split())} words) with {len(state['sources'])} cited sources.",
        "data": {"word_count": len(report.split()), "source_count": len(state["sources"])},
    }

    return {
        "final_report": report,
        "agent_trace": [trace_entry],
    }
