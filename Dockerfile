FROM ubuntu:20.04

ENV PYENV_ROOT /root/.pyenv
ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH
ENV PYTHONDONTWRITEBYTECODE true
ENV PYTHON_VERSION 3.10.0
ENV PYTHONPATH /data/app
ENV CONFIG_PATH /data/app/webapp

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
RUN git clone https://gitee.com/mirrors/pyenv.git /root/.pyenv \
    && cd /root/.pyenv \
    && git checkout `git describe --abbrev=0 --tags` \
    && echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bashrc \
    && echo 'eval "$(pyenv init -)"' >> ~/.bashrc

RUN pyenv install $PYTHON_VERSION
RUN pyenv global $PYTHON_VERSION

# Install poetry.
ENV POETRY_VERSION 1.6.1
RUN pip install "poetry==$POETRY_VERSION"

# Install packages without venvs.
WORKDIR /data/app
COPY ./pyproject.toml /data/app/pyproject.toml
COPY ./poetry.lock /data/app/poetry.lock
ENV POETRY_VIRTUALENVS_CREATE 0
RUN poetry install

# Copy the application code.
COPY ./webapp /data/app/webapp

# Run flask.
ENV FLASK_APP webapp/app.py
ENV FLASK_ENV development
WORKDIR /data/app/webapp

CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]
