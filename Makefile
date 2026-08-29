.PHONY: install test lint typecheck check run demo

install:
	python -m pip install -r requirements-dev.txt

test:
	python -m pytest --cov --cov-report=term-missing --cov-report=xml

lint:
	ruff check .

typecheck:
	mypy

check: lint typecheck test
	python -m compileall -q app.py audit.py demo.py graph.py models.py

run:
	streamlit run app.py

demo:
	python demo.py --churn 0.91 --decision approve
