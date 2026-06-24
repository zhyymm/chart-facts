FROM python:3.12-slim-bookworm AS base

WORKDIR /app

# 🛠️ 终极修复：把 g++ 也加进编译大礼包
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        gcc \
        g++ \
        python3-dev \
        libc-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md VERSION ./
COPY src ./src

# ⚡ 这次 gcc + g++ 双剑合璧，绝对能把二进制 wheel 编译下来
RUN pip install --no-cache-dir .



ENV EPHE_PATH=/app/ephe
ENV HOST=0.0.0.0
ENV PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/health || exit 1

CMD ["uvicorn", "chart_facts.main:app", "--host", "0.0.0.0", "--port", "8000"]