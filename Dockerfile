FROM ubuntu:20.04

ENV PYENV_ROOT /root/.pyenv
ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH
ENV PYTHONDONTWRITEBYTECODE true
ENV PYTHON_VERSION 3.10.0

RUN apt-get update -q \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        git \
        libbz2-dev \
        libreadline-dev \
        libsqlite3-dev \
        libssl-dev \
        zlib1g-dev \
        libffi-dev \
        sudo

# Install pyenv and the required python version.
RUN git clone https://github.com/yyuu/pyenv.git /root/.pyenv \
    && cd /root/.pyenv \
    && git checkout `git describe --abbrev=0 --tags` \
    && sudo echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bashrc \
    && sudo echo 'eval "$(pyenv init -)"'               >> ~/.bashrc

RUN pyenv install $PYTHON_VERSION
RUN pyenv global $PYTHON_VERSION

# Install poetry.
ENV POETRY_VERSION 1.1.12
RUN pip install "poetry==$POETRY_VERSION"

# Install packages without venvs.
WORKDIR /data/app
COPY ./pyproject.toml /data/app/pyproject.toml
COPY ./poetry.lock /data/app/poetry.lock
ENV POETRY_VIRTUALENVS_CREATE 0
RUN poetry install
COPY ./app /data/app/app

# Run flask.
ENV FLASK_APP app
ENV FLASK_ENV development
WORKDIR /data/app/app
ENTRYPOINT ["python", "-m", "flask", "run"]
