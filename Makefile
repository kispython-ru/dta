.PHONY: fix
fix:
	isort .

.PHONY: lint
lint:
	pycodestyle --max-line-length 119 .
	isort -qc .

.PHONY: lint-win
lint-win:
	cd webapp && FOR %%i in (*.py) DO pycodestyle %%i
	isort -qc .	

.PHONY: test
test:
	pytest

.PHONY: check
check: lint test

.PHONY: flask
flask:
	cd webapp && export FLASK_APP=app && export FLASK_ENV=development && flask run

.PHONY: flask-win
flask-win:
	cd webapp && set "FLASK_APP=app" && set "FLASK_ENV=development" && flask run

.PHONY: image
image:
	docker build -t flask-app .

.PHONY: container
container:
	docker run -it --net=host flask-app

.PHONY: migration
migration:
	cd webapp && alembic revision -m "$(TITLE)"

.PHONY: logo
logo:
	python logo.py

.PHONY: seed
seed:
	cd webapp && export SEED=1 && export FLASK_APP=app && export FLASK_ENV=development && flask run

.DEFAULT_GOAL :=
