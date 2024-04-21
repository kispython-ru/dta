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

4. If you wish to seed the database, run:
```bash
poetry shell
make seed # python -m webapp.app --seed
```

#### Windows 10

1. Install [Python 3.10](https://docs.python.org/3/whatsnew/3.10.html). Do **not** use sandboxed Python [from Microsoft Store](https://github.com/python-poetry/poetry/issues/5331). Make sure `python` is added to `PATH`. You can check this by navigating to `System (Control Panel)` -> `Advanced system settings` -> `Environment Variables` -> `System Variables` -> `PATH` -> `Edit`.

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

6. If you wish to seed the database, run:
```bash
poetry shell
make seed # python -m webapp.app --seed
```

### Acknoledgements

We appreciate all people who contributed to the project. Thanks to [@Plintus-bit](https://github.com/Plintus-bit) for designing the [logo](https://github.com/kispython-ru/dta#readme)!

<a href="https://github.com/kispython-ru/dta/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=kispython-ru/dta" />
</a>

### Architecture and Implementation Details

The Digital Teaching Assistant system is described in the following papers:

1. Sovietov P.N. [**Automatic Generation of Programming Exercises**](https://arxiv.org/abs/2205.11304) // In Proceedings of the 1st International Conference on Technology Enhanced Learning in Higher Education (TELE), 2021, pp. 111-114.

2. Andrianova E.G., Demidova L.A., Sovietov P.N. [**Pedagogical Design of a Digital Teaching Assistant in Massive Professional Training for the Digital Economy**](https://www.rtj-mirea.ru/jour/article/view/518/355) // *Russian Technological Journal*. 2022, 10 (3), pp. 7-23.

3. Sovietov P.N., Gorchakov A.V. [**Digital Teaching Assistant for the Python Programming Course**](https://ieeexplore.ieee.org/document/9801060) // In Proceedings of the 2nd International Conference on Technology Enhanced Learning in Higher Education (TELE), 2022, pp. 272-276.

4. Demidova L.A., Sovietov P.N., Gorchakov A.V. [**Clustering of Program Source Text Representations Based on Markov Chains**](https://doi.org/10.21667/1995-4565-2022-81-51-64) // *Vestnik of Ryazan State Radio Engineering University*. 2022, 81, pp. 51-64.

5. Gorchakov A.V. [**A Study of the Approach to Conversion of Program Texts into Vector Representations Based on Markov Chains**](https://itstd-journal.ru/?page_id=758&volume=2&year=2023&lang=en) // *Electronic Scientific Journal "IT-Standard"*. 2023, 2, pp. 40-50.

6. Gorchakov A.V., Demidova L.A., Sovietov P.N. [**Analysis of Program Representations Based on Abstract Syntax Trees and Higher-Order Markov Chains for Source Code Classification Task**](https://www.mdpi.com/1999-5903/15/9/314) // *Future Internet*. 2023, 15 (9), p. 314.

7. Gorchakov A.V., Demidova L.A., Sovietov P.N. [**A Rule-Based Algorithm and Its Specializations for Measuring the Complexity of Software in Educational Digital Environments**](https://www.mdpi.com/2073-431X/13/3/75) // *Computers*. 2024, 13 (3), p. 75.
