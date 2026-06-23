FROM python:3.12-slim-bookworm AS base

WORKDIR /app

# 🛠️ 核心修改：在安装 curl 的同时，加上编译 pyswisseph 所需的 gcc 和 dev 依赖
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        gcc \
        python3-dev \
        libc-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src

# ⚡ 此时进行编译安装，gcc 就会完美介入，顺利把底层 C 源码打包成 python 的 wheel 扩展
RUN pip install --no-cache-dir .

# Swiss Ephemeris data files (1800-2399 AD)
RUN mkdir -p /app/ephe \
    && curl -fsSL https://www.astro.com/ftp/swisseph/ephe/sepl_18.se1 -o /app/ephe/sepl_18.se1 \
    && curl -fsSL https://www.astro.com/ftp/swisseph/ephe/semo_18.se1 -o /app/ephe/semo_18.se1

ENV EPHE_PATH=/app/ephe
ENV HOST=0.0.0.0
ENV PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/health || exit 1

CMD ["uvicorn", "chart_facts.main:app", "--host", "0.0.0.0", "--port", "8000"]