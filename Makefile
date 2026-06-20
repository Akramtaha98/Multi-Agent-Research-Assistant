.PHONY: install test api ui run

install:
	pip install -r requirements.txt

test:
	python test_pipeline.py

api:
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

ui:
	streamlit run ui/app.py

run:
	@echo "Starting FastAPI in background..."
	uvicorn api.main:app --host 0.0.0.0 --port 8000 &
	@echo "Starting Streamlit..."
	streamlit run ui/app.py
