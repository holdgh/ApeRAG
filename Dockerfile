FROM python:3.11.3-slim

RUN --mount=type=cache,target=/var/cache/apt \
    apt update && \
    apt install --no-install-recommends -y build-essential

COPY requirements.txt /requirements.txt

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r /requirements.txt && pip cache purge

COPY . /app

WORKDIR /app

ENTRYPOINT ["/app/scripts/entrypoint.sh"]
