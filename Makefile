.PHONY: fix
fix:
	isort .

.PHONY: lint
lint:
	pycodestyle ./**/*.py
	isort -qc .

.PHONY: test
test:
	pytest

.PHONY: check
check: lint test

.PHONY: flask
flask:
	cd webapp && export FLASK_APP=app && export FLASK_ENV=development && flask run

.PHONY: image
image:
	docker build -t flask-app .

.PHONY: container
container:
	docker run -it --net=host flask-app

.PHONY: migration
migration:
	cd webapp && alembic revision -m "$(TITLE)"

.DEFAULT_GOAL :=
