.PHONY: install qa run test eval repro cost ui all clean

install:
	pip install -r requirements.txt

qa:
	python scripts/run_qa.py

phase2:
	python scripts/run_phase2_weekly.py

run:
	python scripts/run_pipeline.py --log-cost

test:
	pytest tests/ -v

eval:
	python scripts/run_eval.py

repro:
	python scripts/run_repro.py

cost:
	python scripts/log_cost.py

ui:
	streamlit run app.py

all: qa phase2 run test eval repro cost
