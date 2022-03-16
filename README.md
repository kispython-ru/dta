[![Main workflow](https://github.com/worldbeater/dta/actions/workflows/workflow.yml/badge.svg?branch=main)](https://github.com/worldbeater/dta/actions/workflows/workflow.yml) [![codecov](https://codecov.io/gh/worldbeater/dta/branch/main/graph/badge.svg)](https://codecov.io/gh/worldbeater/dta)

### Digital Teaching Assistant UI

Use `poetry install` in order to install all the required dependencies. If you are using [code](https://code.visualstudio.com/), press `Ctrl+Shift+P` in order to activate poetry virtual environment after installation. Run unit tests via `make test`, run the app via `make flask`, run the linter as `make lint`. If you prefer to use containers, there are `make image` and `make container` scripts that will build a Docker image and run the app inside the image. A sample run script for production might look like as follows:

```sh
# Use the following if you'd like to seed the database:
# export SEED=1 && sh start.sh
# Don't forget to do this after seeding: unset SEED
export CONFIG_PATH=/home/app/webapp/config
. /home/app/.cache/pypoetry/virtualenvs/app-_h2eKbNq-py3.10/bin/activate
cd src/webapp
waitress-serve --port 8080 --call 'app:create_app'
```
