.PHONY: setup notebooks check export deck

setup:
	uv sync

notebooks:
	uv run marimo edit notebooks/

check:
	uv run ruff check .
	uv run ruff format --check .
	uv run marimo check notebooks/

export:
	uv run marimo export html notebooks/01_data_exploration.py -o outputs/reports/01_data_exploration.html
	uv run marimo export html notebooks/02_correlations.py -o outputs/reports/02_correlations.html
	uv run marimo export html notebooks/03_predictive_modelling.py -o outputs/reports/03_predictive_modelling.html
	uv run marimo export html notebooks/04_weekend_pricing.py -o outputs/reports/04_weekend_pricing.html

deck:
	uv run python deck/export_slide_data.py
	node deck/build_deck.js
	node deck/build_approach_deck.js
