"""
Search Agent — queries arXiv for each sub-query and returns structured paper results.
"""

import arxiv
from graph.state import ResearchState, AgentTraceEntry


MAX_RESULTS_PER_QUERY = 5


def search_node(state: ResearchState) -> dict:
    client = arxiv.Client()
    all_results: list[dict] = []
    seen_ids: set[str] = set()

    for sub_query in state["sub_queries"]:
        search = arxiv.Search(
            query=sub_query,
            max_results=MAX_RESULTS_PER_QUERY,
            sort_by=arxiv.SortCriterion.Relevance,
        )

        for paper in client.results(search):
            arxiv_id = paper.entry_id.split("/")[-1]
            if arxiv_id in seen_ids:
                continue
            seen_ids.add(arxiv_id)

            all_results.append(
                {
                    "id": arxiv_id,
                    "title": paper.title,
                    "authors": [a.name for a in paper.authors[:3]],
                    "abstract": paper.summary.replace("\n", " "),
                    "url": paper.entry_id,
                    "published": paper.published.strftime("%Y-%m-%d") if paper.published else "unknown",
                    "sub_query": sub_query,
                }
            )

    if not all_results:
        return {
            "search_results": [],
            "sources": [],
            "agent_trace": [
                {
                    "agent": "Search Agent",
                    "message": "No papers found on arXiv for the given queries.",
                    "data": {"sub_queries": state["sub_queries"]},
                }
            ],
            "error": "No papers found. Try a different or broader research question.",
        }

    trace_entry: AgentTraceEntry = {
        "agent": "Search Agent",
        "message": f"Retrieved {len(all_results)} unique papers from arXiv across {len(state['sub_queries'])} sub-queries.",
        "data": {
            "paper_count": len(all_results),
            "titles": [r["title"] for r in all_results],
        },
    }

    # Sources list is the clean citation-ready version
    sources = [
        {
            "id": r["id"],
            "title": r["title"],
            "authors": r["authors"],
            "url": r["url"],
            "published": r["published"],
        }
        for r in all_results
    ]

    return {
        "search_results": all_results,
        "sources": sources,
        "agent_trace": [trace_entry],
    }
