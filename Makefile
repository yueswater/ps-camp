init-db:
	PYTHONPATH=src python -m ps_camp.init_db
run:
	PYTHONPATH=src poetry run python -m ps_camp.app
predeploy:
	poetry run autoflake --in-place --remove-unused-variables --remove-all-unused-imports -r .
	poetry run isort .
	poetry run black .
	git add .
	git status
