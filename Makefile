REQUIREMENTS_DIR := requirements
PIP_COMPILE_ARGS := --generate-hashes --allow-unsafe --no-header --no-emit-index-url --verbose
PIP_COMPILE := cd $(REQUIREMENTS_DIR) && pip-compile $(PIP_COMPILE_ARGS)

.PHONY: fix
fix:
	isort .

.PHONY: lint
lint:
	ec
	flake8
	isort -qc .

.PHONY: test
test:
	pytest

.PHONY: check
check: lint test

.PHONY: compile-requirements
compile-requirements:
	pip install pip-tools
	$(PIP_COMPILE) requirements.in
	$(PIP_COMPILE) requirements.lint.in
	$(PIP_COMPILE) requirements.test.in
	test -f $(REQUIREMENTS_DIR)/requirements.local.in && $(PIP_COMPILE) requirements.local.in || exit 0

.PHONY: sync-requirements
sync-requirements:
	pip install pip-tools
	cd $(REQUIREMENTS_DIR) && pip-sync requirements.txt requirements.*.txt

.PHONY: flask
flask:
	cd webapp && export FLASK_APP=app && export FLASK_ENV=development && flask run

.PHONY: image
image:
	docker build -t flask-app .

.PHONY: container
container:
	docker run -it --net=host flask-app

.DEFAULT_GOAL :=
