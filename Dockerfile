FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    TZ=Europe/Warsaw \
    UV_SYSTEM_PYTHON=1 \
    UV_NO_SYNC=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl tini \
  && rm -rf /var/lib/apt/lists/*

# install uv
RUN pip install --no-cache-dir uv

# copy dependency manifests first (cache-friendly)
COPY pyproject.toml uv.lock ./

# install deps (locked, deterministic)
RUN uv sync --frozen --no-dev

# copy app
COPY . .

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/usr/bin/tini","--","/entrypoint.sh"]
CMD ["uv","run","python","main.py"]