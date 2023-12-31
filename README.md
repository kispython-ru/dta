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

1. Install [Python 3.10](https://docs.python.org/3/whatsnew/3.10.html). Do **not** use Python [from Microsoft Store](https://github.com/python-poetry/poetry/issues/5331). Make sure `python` is added to `PATH`. You can check this by navigating to `System (Control Panel)` -> `Advanced system settings` -> `Environment Variables` -> `System Variables` -> `PATH` -> `Edit`.

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

### Architecture

The Digital Teaching Assistant system is described in the following papers:

1. Sovietov P.N. [**Automatic Generation of Programming Exercises**](https://arxiv.org/abs/2205.11304) // In Proceedings of the 1st International Conference on Technology Enhanced Learning in Higher Education (TELE), 2021, pp. 111-114.

2. Andrianova E.G., Demidova L.A., Sovetov P.N. [**Pedagogical Design of a Digital Teaching Assistant in Massive Professional Training for the Digital Economy**](https://www.rtj-mirea.ru/jour/article/view/518/355) // *Russian Technological Journal*. **2022**, 10 (3), pp. 7-23.

3. Sovietov P.N., Gorchakov A.V. [**Digital Teaching Assistant for the Python Programming Course**](https://ieeexplore.ieee.org/document/9801060) // In Proceedings of the 2nd International Conference on Technology Enhanced Learning in Higher Education (TELE), 2022, pp. 272-276.

4. Demidova L.A., Sovietov P.N., Gorchakov A.V. [**Clustering of Program Source Text Representations Based on Markov Chains**](https://doi.org/10.21667/1995-4565-2022-81-51-64) // *Vestnik of Ryazan State Radio Engineering University*. **2022**, 81, pp. 51-64.

5. Demidova L.A., Gorchakov A.V. [**Classification of Program Texts Represented as Markov Chains with Biology-Inspired Algorithms-Enhanced Extreme Learning Machines**](https://www.mdpi.com/1999-4893/15/9/329) // *Algorithms*. **2022**, 15 (9), p. 329.

6. Gorchakov A.V., Demidova L.A., Sovietov P.N. [**Automated program text analysis using representations based on Markov chains and Extreme Learning Machines**](http://vestnik.rsreu.ru/ru/archive/2022/vypusk-82/1299-1995-4565-2022-82-89-103) // *Vestnik of Ryazan State Radio Engineering University*. **2022**, 82, pp. 89-103.

7. Gorchakov A.V., Demidova L.A., Sovietov P.N. [**Intelligent Accounting of Educational Achievements in the "Digital Teaching Assistant" System**](https://www.researchgate.net/publication/369692306_Intelligent_Accounting_of_Educational_Achievements_in_the_Digital_Teaching_Assistant_System) // *International Journal of Open Information Technologies*. **2023**, 11 (4), pp. 106-115.

8. Gorchakov A.V. [**A Study of the Approach to Conversion of Program Texts into Vector Representations Based on Markov Chains**](http://itstd-journal.ru/wp-content/uploads/2023/05/A-STUDY-OF-THE-APPROACH-TO-CONVERSION-OF-PROGRAM-.pdf) // *Electronic Scientific Journal "IT-Standard"*. **2023**, 2, pp. 40-50.
