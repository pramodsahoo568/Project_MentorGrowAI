cp .env.local .env
uvicorn server.app:app --reload --port 8000