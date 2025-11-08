# Makefile for Grocery Management Agent

.PHONY: help install dev test lint format clean docker-up docker-down run-api run-cli

help:
	@echo "Grocery Management Agent - Make Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install       Install dependencies"
	@echo "  make dev          Install dev dependencies"
	@echo ""
	@echo "Run:"
	@echo "  make run-api      Start FastAPI server"
	@echo "  make run-cli      Start CLI interface"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up    Start all services with Docker"
	@echo "  make docker-down  Stop all services"
	@echo ""
	@echo "Development:"
	@echo "  make test         Run tests"
	@echo "  make lint         Run linters"
	@echo "  make format       Format code"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean        Clean temporary files"

install:
	pip install -r requirements.txt

dev:
	pip install -r requirements.txt
	pip install -e .

test:
	pytest -v --cov=. --cov-report=html

lint:
	flake8 .
	mypy .

format:
	black .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache htmlcov .coverage

docker-up:
	docker-compose up -d
	@echo "Services started:"
	@echo "  - API: http://localhost:8000"
	@echo "  - Docs: http://localhost:8000/docs"
	@echo "  - MongoDB: localhost:27017"
	@echo "  - Mongo Express: http://localhost:8081"

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

run-api:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

run-cli:
	python cli.py

init-db:
	python scripts/init_db.py init

check-db:
	python scripts/init_db.py check

