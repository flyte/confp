FROM python:3.6-alpine3.7

WORKDIR /confp

RUN pip install pipenv

COPY Pipfile* ./

RUN pipenv install --system --deploy

COPY src ./

CMD ["python", "-m", "confp"]
