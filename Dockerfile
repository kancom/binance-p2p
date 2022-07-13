FROM python:3.9-slim  AS base

RUN DEBIAN_FRONTEND=noninteractive apt-get update \
  && apt install -y curl build-essential vim

RUN pip install pipenv

WORKDIR /app
COPY ./Pipfile /app
COPY ./Pipfile.lock /app

RUN pipenv install

FROM base AS pkts

COPY ./ /app

RUN pipenv run pip install -e .
