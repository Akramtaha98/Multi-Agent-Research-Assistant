"""
Search Agent — queries arXiv for each sub-query in parallel and returns structured paper results.
"""

import arxiv
from concurrent.futures import ThreadPoolExecutor, as_completed
from graph.state import ResearchState, AgentTraceEntry


MAX_RESULTS_PER_QUERY = 5


def _fetch_query(sub_query: str) -> list[dict]:
    client = arxiv.Client()
    search = arxiv.Search(
        query=sub_query,
        max_results=MAX_RESULTS_PER_QUERY,
        sort_by=arxiv.SortCriterion.Relevance,
    )
    results = []
    for paper in client.results(search):
        results.append(
            {
                "id": paper.entry_id.split("/")[-1],
                "title": paper.title,
                "authors": [a.name for a in paper.authors[:3]],
                "abstract": paper.summary.replace("\n", " "),
                "url": paper.entry_id,
                "published": paper.published.strftime("%Y-%m-%d") if paper.published else "unknown",
                "sub_query": sub_query,
            }
        )
    return results


def search_node(state: ResearchState) -> dict:
    seen_ids: set[str] = set()
    all_results: list[dict] = []

    # Run all sub-queries in parallel
    with ThreadPoolExecutor(max_workers=len(state["sub_queries"])) as executor:
        futures = {executor.submit(_fetch_query, q): q for q in state["sub_queries"]}
        for future in as_completed(futures):
            for paper in future.result():
                if paper["id"] not in seen_ids:
                    seen_ids.add(paper["id"])
                    all_results.append(paper)

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
