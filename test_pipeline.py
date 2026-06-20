"""
Quick end-to-end test — run this before starting the API/UI to confirm the pipeline works.
Usage: python test_pipeline.py
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()

from graph.research_graph import research_graph

QUERY = "What are the latest approaches to RAG for low-resource languages?"

print(f"\n{'='*60}")
print(f"Query: {QUERY}")
print(f"{'='*60}\n")

initial_state = {
    "query": QUERY,
    "sub_queries": [],
    "search_results": [],
    "analysis": {},
    "final_report": "",
    "sources": [],
    "agent_trace": [],
    "error": "",
}

result = research_graph.invoke(initial_state)

print("── Agent Trace ──────────────────────────────────────────")
for entry in result.get("agent_trace", []):
    print(f"\n[{entry['agent']}] {entry['message']}")

print("\n\n── Final Report ─────────────────────────────────────────")
print(result.get("final_report", "No report generated."))

print("\n\n── Sources ──────────────────────────────────────────────")
for i, src in enumerate(result.get("sources", []), 1):
    print(f"[{i}] {src['title']} — {src['url']}")

if result.get("error"):
    print(f"\n⚠️  Error: {result['error']}")
