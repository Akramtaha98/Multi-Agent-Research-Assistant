"""
Hugging Face Spaces entry point.
HF Spaces (Streamlit SDK) looks for app.py at the repo root.
This file starts both FastAPI and Streamlit in a single process using threads,
because HF Spaces only exposes one port (7860).
"""

import threading
import uvicorn
import streamlit.web.cli as stcli
import sys
import os

os.environ.setdefault("API_BASE_URL", "http://localhost:8000")


def start_api():
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, log_level="warning")


def start_ui():
    sys.argv = ["streamlit", "run", "ui/app.py", "--server.port=7860", "--server.address=0.0.0.0"]
    stcli.main()


if __name__ == "__main__":
    api_thread = threading.Thread(target=start_api, daemon=True)
    api_thread.start()

    # Streamlit blocks — runs in main thread
    start_ui()
