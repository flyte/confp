FROM python:3.6-alpine3.7

WORKDIR /confp

COPY Pipfile* ./

RUN pip install --no-cache-dir pipenv pip-autoremove && \
    pipenv install --system --deploy && \
    pip-autoremove -y pipenv pip-autoremove && \
    rm -rf ~/.cache/pip

COPY src ./

ENTRYPOINT ["python", "-m", "confp"]
