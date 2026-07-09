FROM ghcr.io/astral-sh/uv:0.10.11 AS uv

FROM python:3.12-slim AS builder
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY tongji ./tongji
RUN uv sync --frozen --no-dev

FROM python:3.12-slim AS runtime
RUN useradd --create-home --uid 10001 tongji
WORKDIR /app
COPY --from=builder --chown=tongji:tongji /app /app
RUN mkdir -p /app/data && chown tongji:tongji /app/data
USER tongji
ENV PATH="/app/.venv/bin:$PATH" \
    TJ_HOST="0.0.0.0" \
    TJ_PORT="8000" \
    TJ_SESSION_STORE_PATH="/app/data/session.json"
EXPOSE 8000
VOLUME ["/app/data"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz')"
CMD ["python", "-m", "tongji", "serve"]
