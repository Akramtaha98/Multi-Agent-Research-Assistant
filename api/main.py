"""
FastAPI backend — exposes the LangGraph research pipeline via REST + SSE streaming.
"""

import json
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator

from dotenv import load_dotenv

load_dotenv()

from graph.research_graph import research_graph  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm-up: graph is already compiled at import time
    yield


app = FastAPI(
    title="Multi-Agent Research Assistant",
    description="LangGraph-powered research pipeline with arXiv + Claude",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ResearchRequest(BaseModel):
    query: str

    @field_validator("query")
    @classmethod
    def query_must_not_be_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Research query cannot be empty.")
        if len(v) < 10:
            raise ValueError("Research query is too short — please be more specific.")
        if len(v) > 500:
            raise ValueError("Research query is too long (max 500 characters).")
        return v


class ResearchResponse(BaseModel):
    report: str
    sources: list[dict]
    agent_trace: list[dict]


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/research", response_model=ResearchResponse)
async def research(request: ResearchRequest):
    """
    Runs the full LangGraph pipeline and returns the complete result.
    Use /research/stream for real-time SSE output.
    """
    try:
        initial_state = {
            "query": request.query,
            "sub_queries": [],
            "search_results": [],
            "analysis": {},
            "final_report": "",
            "sources": [],
            "agent_trace": [],
            "error": "",
        }
        result = await asyncio.to_thread(research_graph.invoke, initial_state)
        return ResearchResponse(
            report=result.get("final_report", ""),
            sources=result.get("sources", []),
            agent_trace=result.get("agent_trace", []),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")


@app.post("/research/stream")
async def research_stream(request: ResearchRequest):
    """
    Streams agent trace events via Server-Sent Events (SSE) as each node completes,
    then sends a final 'done' event with the full result.
    """

    async def event_generator():
        initial_state = {
            "query": request.query,
            "sub_queries": [],
            "search_results": [],
            "analysis": {},
            "final_report": "",
            "sources": [],
            "agent_trace": [],
            "error": "",
        }

        try:
            # LangGraph supports streaming via .stream() — each yielded value is a
            # dict mapping node_name -> state_update after that node completes.
            def run_stream():
                return list(
                    research_graph.stream(initial_state, stream_mode="updates")
                )

            updates = await asyncio.to_thread(run_stream)

            final_state = initial_state.copy()
            for update in updates:
                for node_name, node_output in update.items():
                    # Merge node output into running state
                    if isinstance(node_output, dict):
                        for k, v in node_output.items():
                            if k == "agent_trace" and isinstance(v, list):
                                existing = final_state.get("agent_trace", [])
                                final_state["agent_trace"] = existing + v
                            else:
                                final_state[k] = v

                    # Emit the latest trace entry for this node as an SSE event
                    trace_entries = node_output.get("agent_trace", []) if isinstance(node_output, dict) else []
                    for entry in trace_entries:
                        payload = json.dumps({"type": "trace", "entry": entry})
                        yield f"data: {payload}\n\n"

            # Final event with full result
            final_payload = json.dumps(
                {
                    "type": "done",
                    "report": final_state.get("final_report", ""),
                    "sources": final_state.get("sources", []),
                    "agent_trace": final_state.get("agent_trace", []),
                }
            )
            yield f"data: {final_payload}\n\n"

        except Exception as e:
            error_payload = json.dumps({"type": "error", "message": str(e)})
            yield f"data: {error_payload}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
