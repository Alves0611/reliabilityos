FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install \
    $(python -c "import tomllib; deps=tomllib.load(open('pyproject.toml','rb'))['project']['dependencies']; print(' '.join(deps))")

FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

COPY . .
RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
