FROM python:3.11-alpine

# Setup environment variables:
ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  POETRY_VERSION=1.4.1 \
  RUNNING_IN_DOCKER=true \
  BASE_PATH=/

# System deps:
RUN apk add \
  --update \
  --no-cache \
  --virtual .tmp-build-deps \
  gcc libc-dev linux-headers libffi-dev

RUN pip install "poetry==$POETRY_VERSION"

# Copy only requirements to cache them in docker layer
WORKDIR /code
COPY poetry.lock pyproject.toml /code/

# Project initialization:
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi --without dev

# Creating folders, and files for a project:
COPY . /code

CMD python main.py
