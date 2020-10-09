FROM python:3.8

LABEL project="series"

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV I_AM_IN_DOCKER 1

WORKDIR /code

COPY Pipfile Pipfile.lock /code/
RUN pip install pipenv gunicorn && pipenv install --system --ignore-pipfile
#RUN pip install pipenv gunicorn && pipenv install --system

COPY series /code/
