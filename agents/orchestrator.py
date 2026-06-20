"""
Orchestrator Agent — breaks a user research question into focused arXiv sub-queries.
"""

import json
from langchain_core.messages import SystemMessage, HumanMessage
from agents.llm import get_llm
from graph.state import ResearchState, AgentTraceEntry


ORCHESTRATOR_SYSTEM = """You are a research orchestrator for an academic search system.
Your job is to decompose a broad research question into 1–3 precise, focused search queries
suitable for the arXiv academic paper database.

Rules:
- Each query should be short (3–7 words), specific, and search-friendly
- Queries should cover different angles of the research question
- Return ONLY a JSON array of strings, nothing else
- Example: ["RAG low-resource languages", "multilingual retrieval augmented generation", "Arabic NLP question answering"]
"""


def orchestrator_node(state: ResearchState) -> dict:
    llm = get_llm(temperature=0)

    messages = [
        SystemMessage(content=ORCHESTRATOR_SYSTEM),
        HumanMessage(content=f"Research question: {state['query']}"),
    ]

    response = llm.invoke(messages)
    raw = response.content.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    sub_queries = json.loads(raw)

    trace_entry: AgentTraceEntry = {
        "agent": "Orchestrator",
        "message": f"Decomposed query into {len(sub_queries)} sub-queries: {', '.join(sub_queries)}",
        "data": {"sub_queries": sub_queries},
    }

    return {
        "sub_queries": sub_queries,
        "agent_trace": [trace_entry],
    }
