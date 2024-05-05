FROM python:3.12-alpine

# Setup environment variables:
ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.8.2 \
    RUNNING_IN_DOCKER=true \
    # Store the venv in project directory: /app/.venv
    POETRY_VIRTUALENVS_CREATE=0 \
    # Set the cache directory for poetry and pip
    # This is useful when you want to cache dependencies between builds
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    BASE_PATH=/

# System deps:
RUN --mount=type=cache,target=/var/cache/apk \
  --update \
  --virtual .tmp-build-deps \
  gcc libc-dev linux-headers libffi-dev

RUN pip install "poetry==$POETRY_VERSION"

# Copy only requirements to cache them in docker layer
WORKDIR /code
COPY poetry.lock pyproject.toml /code/

# Project initialization:
RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install --no-interaction --no-ansi --without dev

# Creating folders, and files for a project:
COPY . /code

CMD python main.py
