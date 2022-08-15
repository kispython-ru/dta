[![Main workflow](https://github.com/kispython-ru/dta/actions/workflows/workflow.yml/badge.svg?branch=main)](https://github.com/kispython-ru/dta/actions/workflows/workflow.yml) [![codecov](https://codecov.io/gh/kispython-ru/dta/branch/main/graph/badge.svg)](https://codecov.io/gh/kispython-ru/dta)

<br>
<a href="https://github.com/worldbeater/dta">
  <img width="160" heigth="160" src="./webapp/static/logo.svg">
</a>
<br>

## Digital Teaching Assistant

### Setting Up Development Environment

#### Ubuntu 20.04 LTS

1. Install [Python 3.10](https://docs.python.org/3/whatsnew/3.10.html). [pyenv](https://github.com/pyenv/pyenv) can help with switching among different Python versions.

2. Install [poetry](https://github.com/python-poetry/poetry) and dependencies:
```bash
pip install poetry
poetry install
```

3. Run tests, launch the app:
```bash
poetry shell
make test
make flask
```

#### Windows 10

1. Install [Python 3.10](https://docs.python.org/3/whatsnew/3.10.html). Make sure `python` is added to `PATH`. You can check this by navigating to `System (Control Panel)` -> `Advanced system settings` -> `Environment Variables` -> `System Variables` -> `PATH` -> `Edit`.

2. Install [Chocolatey](https://chocolatey.org/install).

3. Install [GNU make](https://community.chocolatey.org/packages/make):
```bash
choco install make
```

4. Install [poetry](https://github.com/python-poetry/poetry) and dependencies:
```bash
pip install poetry
poetry install
```

5. Run tests, launch the app:
```bash
poetry shell
make test
make flask-win
```

### Acknoledgements

We appreciate all people who contributed to the project. Thanks to [@Plintus-bit](https://github.com/Plintus-bit) for designing the [logo](https://github.com/kispython-ru/dta#readme)!

<a href="https://github.com/kispython-ru/dta/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=kispython-ru/dta" />
</a>

### Architecture

The architecture of the system and its components are described in the following papers:

1. Sovietov P.N., Gorchakov A.V. [**Digital Teaching Assistant for the Python Programming Course**](https://ieeexplore.ieee.org/document/9801060) // 2022 2nd International Conference on Technology Enhanced Learning in Higher Education (TELE). – IEEE, 2022. – pp. 272-276.

2. Sovietov P.N. [**Automatic Generation of Programming Exercises**](https://arxiv.org/abs/2205.11304) // 2021 1st International Conference on Technology Enhanced Learning in Higher Education (TELE). – IEEE, 2021. – pp. 111-114.

3. Andrianova E.G., Demidova L.A., Sovetov P.N. [**Pedagogical design of a digital teaching assistant in massive professional training for the digital economy**](https://www.rtj-mirea.ru/jour/article/view/518/355) // Russian Technological Journal. – 2022. – Vol. 10. – No. 3. – pp. 7-23.
