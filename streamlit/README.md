# Streamlit Frontend — Research Assistant with Memory

A pure-Python Streamlit web interface for the Research Assistant.

## Prerequisites

Make sure the FastAPI backend is running:

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Running the Streamlit App

1. Install dependencies:
```bash
cd streamlit
pip install -r requirements.txt
```

2. Start the Streamlit application:
```bash
streamlit run app.py --server.port 8501
```

3. Open your browser at `http://localhost:8501`.

## Docker Usage

```bash
docker build -t research-assistant-streamlit ./streamlit
docker run -p 8501:8501 -e BACKEND_URL=http://host.docker.internal:8000 research-assistant-streamlit
```
