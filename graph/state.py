from typing import TypedDict, Annotated
import operator


class AgentTraceEntry(TypedDict):
    agent: str
    message: str
    data: dict


class ResearchState(TypedDict):
    query: str
    sub_queries: list[str]
    search_results: list[dict]
    analysis: dict
    final_report: str
    sources: list[dict]
    agent_trace: Annotated[list[AgentTraceEntry], operator.add]
    error: str
