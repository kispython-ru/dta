.PHONY: fix
fix:
	isort .

.PHONY: lint
lint:
	pycodestyle --max-line-length 119 --exclude .venv .
	isort -qc .

.PHONY: test
test:
	pytest

.PHONY: check
check: lint test

.PHONY: flask
flask:
	export FLASK_APP=webapp.app && export FLASK_ENV=development && flask run

.PHONY: seed
seed:
	rm -f web-app.db
	python -m webapp.app --seed

.PHONY: flask-win
flask-win:
	set "FLASK_APP=webapp.app" && set "FLASK_ENV=development" && flask run

.PHONY: image
image:
	docker build -t flask-app .

.PHONY: container
container:
	docker run -it --net=host flask-app

.PHONY: migration
migration:
	cd webapp && alembic revision -m "$(TITLE)"

.PHONY: coverage
coverage:
	pytest --cov-report html --cov webapp ./tests

.DEFAULT_GOAL :=