"""
LangGraph StateGraph wiring all agents into the research pipeline.
"""

from langgraph.graph import StateGraph, END
from graph.state import ResearchState
from agents.orchestrator import orchestrator_node
from agents.search import search_node
from agents.analysis import analysis_node
from agents.writer import writer_node


def should_continue_after_search(state: ResearchState) -> str:
    """Skip analysis/writer if search found nothing."""
    if state.get("error"):
        return "writer"
    return "analysis"


def build_graph() -> StateGraph:
    graph = StateGraph(ResearchState)

    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("search", search_node)
    graph.add_node("analysis", analysis_node)
    graph.add_node("writer", writer_node)

    graph.set_entry_point("orchestrator")
    graph.add_edge("orchestrator", "search")
    graph.add_conditional_edges(
        "search",
        should_continue_after_search,
        {"analysis": "analysis", "writer": "writer"},
    )
    graph.add_edge("analysis", "writer")
    graph.add_edge("writer", END)

    return graph.compile()


# Singleton compiled graph
research_graph = build_graph()
