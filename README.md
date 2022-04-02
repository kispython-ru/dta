[![Main workflow](https://github.com/worldbeater/dta/actions/workflows/workflow.yml/badge.svg?branch=main)](https://github.com/worldbeater/dta/actions/workflows/workflow.yml) [![codecov](https://codecov.io/gh/worldbeater/dta/branch/main/graph/badge.svg)](https://codecov.io/gh/worldbeater/dta)

## Digital Teaching Assistant UI

### Setting Up Development Environment

#### Ubuntu KDE

1. Install [Python 3.10](https://docs.python.org/3/whatsnew/3.10.html). [pyenv](https://github.com/pyenv/pyenv) can help with switching among different Python versions.

2. Install [poetry](https://github.com/python-poetry/poetry), install project dependencies, activate [venv](https://python-poetry.org/docs/cli/#shell):
```bash
pip install poetry
poetry install # Execute from repository root
poetry shell
```

3. Run the tests and launch the web server:
```bash
make test
make flask
```

#### Windows 10

1. Install [Python 3.10](https://docs.python.org/3/whatsnew/3.10.html). Make sure `python` is added to `PATH`. You can check this by navigating to `System (Control Panel)` -> `Advanced system settings` -> `Environment Variables` -> `System Variables` -> `PATH` -> `Edit`.

2. Install the [Chocolatey](https://chocolatey.org/install) package manager.

3. Install the [GNU make](https://community.chocolatey.org/packages/make) utility by typing:
```bash
choco install make
```

4. Install [poetry](https://github.com/python-poetry/poetry), install project dependencies, activate [venv](https://python-poetry.org/docs/cli/#shell):
```bash
pip install poetry
poetry install # Execute from repository root
poetry shell
```

5. Run the tests and launch the web server:
```bash
make test
make flask-win
```

### Fruther Steps

If you are using [code](https://code.visualstudio.com/), press `Ctrl+Shift+P` in order to activate poetry virtual environment after installation. Run unit tests via `make test`, run the app via `make flask`, run the linter as `make lint`, run linter fixes via `make fix`. If you prefer to use containers, there are `make image` and `make container` scripts that will build a Docker image and run the app inside the image. A sample run script for production might look like as follows:

```sh
# Use the following if you'd like to seed the database:
# export SEED=1 && sh start.sh
# Don't forget to do this after seeding: unset SEED
export CONFIG_PATH=/home/app/webapp/config
. /home/app/.cache/pypoetry/virtualenvs/app-_h2eKbNq-py3.10/bin/activate
cd src/webapp
waitress-serve --port 8080 --call 'app:create_app'
```
