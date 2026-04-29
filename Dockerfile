FROM python:3.12-alpine

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /confp

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --all-extras --no-install-project

COPY src ./src
COPY README.md ./

RUN uv sync --frozen --no-dev --all-extras

ENTRYPOINT ["uv", "run", "python", "-m", "confp"]
