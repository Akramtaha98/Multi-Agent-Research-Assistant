"""
Analysis Agent — extracts key findings, groups themes, and flags contradictions across papers.
"""

import json
from langchain_core.messages import SystemMessage, HumanMessage
from agents.llm import get_llm
from graph.state import ResearchState, AgentTraceEntry


ANALYSIS_SYSTEM = """You are a research analyst specializing in academic literature analysis.

Given a list of papers (title + abstract), you must:
1. Extract 1–2 key findings from each paper
2. Group findings into 2–4 common themes across all papers
3. Identify any contradictions or disagreements between papers (where papers make conflicting claims)

Return ONLY valid JSON in this exact structure:
{
  "papers": [
    {
      "id": "<arxiv_id>",
      "title": "<title>",
      "key_findings": ["finding 1", "finding 2"]
    }
  ],
  "themes": [
    {
      "name": "<theme name>",
      "description": "<brief description>",
      "paper_ids": ["<id1>", "<id2>"]
    }
  ],
  "contradictions": [
    {
      "description": "<what the disagreement is>",
      "paper_ids": ["<id1>", "<id2>"]
    }
  ]
}

If no contradictions exist, return an empty list for "contradictions".
"""


def analysis_node(state: ResearchState) -> dict:
    if state.get("error"):
        return {}

    llm = get_llm(temperature=0, max_tokens=4096, speed="smart")

    # Build a compact representation of all papers to fit context
    papers_text = ""
    for i, paper in enumerate(state["search_results"], 1):
        authors = ", ".join(paper["authors"])
        papers_text += (
            f"\n[{i}] ID: {paper['id']}\n"
            f"Title: {paper['title']}\n"
            f"Authors: {authors} ({paper['published']})\n"
            f"Abstract: {paper['abstract'][:300]}...\n"
        )

    messages = [
        SystemMessage(content=ANALYSIS_SYSTEM),
        HumanMessage(
            content=f"Research question: {state['query']}\n\nPapers:\n{papers_text}"
        ),
    ]

    response = llm.invoke(messages)
    raw = response.content.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    analysis = json.loads(raw)

    theme_names = [t["name"] for t in analysis.get("themes", [])]
    contradiction_count = len(analysis.get("contradictions", []))

    trace_entry: AgentTraceEntry = {
        "agent": "Analysis Agent",
        "message": (
            f"Analyzed {len(analysis.get('papers', []))} papers. "
            f"Identified {len(theme_names)} themes: {', '.join(theme_names)}. "
            + (
                f"Found {contradiction_count} contradiction(s) across papers."
                if contradiction_count
                else "No contradictions detected."
            )
        ),
        "data": {
            "themes": theme_names,
            "contradiction_count": contradiction_count,
        },
    }

    return {
        "analysis": analysis,
        "agent_trace": [trace_entry],
    }
