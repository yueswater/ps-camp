init-db:
	PYTHONPATH=src python -m ps_camp.init_db
run:
	PYTHONPATH=src poetry run python -m ps_camp.app
