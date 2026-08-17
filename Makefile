# Stratum AI — common tasks
.PHONY: deps lint test api portal demo clinic realestate logistics build env install start

deps:
	pip install -r requirements.txt -r requirements-dev.txt

env:
	bash scripts/setup_env.sh

install:
	bash install.sh

start:
	bash run.sh

lint:
	ruff check CORE_AGENT_INFRASTRUCTURE VERTICALS DEMOS tests web

test:
	pytest tests/ -v

api:
	uvicorn CORE_AGENT_INFRASTRUCTURE.api.main:app --reload --port 8000

demo:
	python3 DEMOS/run_demo.py all

clinic:
	python3 DEMOS/run_demo.py clinic

realestate:
	python3 DEMOS/run_demo.py realestate

logistics:
	python3 DEMOS/run_demo.py logistics

build:
	python3 _build/build.py
