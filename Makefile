.PHONY: install backend frontend test seed docker-up docker-down
install:
	python -m pip install -r backend/requirements.txt
	cd frontend && npm install
backend:
	cd backend && uvicorn app.main:app --reload --port 8000
frontend:
	cd frontend && npm run dev
test:
	cd backend && pytest -q --cov=app --cov-report=term-missing
seed:
	cd backend && python -m app.seed
docker-up:
	docker compose up --build
docker-down:
	docker compose down

