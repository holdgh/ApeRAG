# Build stage for dependencies
FROM python:3.11.1-slim AS builder

WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock* ./

# Install system dependencies and uv in one layer
RUN apt update && \
    apt install --no-install-recommends -y build-essential git curl && \
    curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies using uv sync
RUN /root/.local/bin/uv venv /opt/venv --python 3.11 && \
    . /opt/venv/bin/activate && \
    /root/.local/bin/uv sync --active

# Clean up
RUN apt clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Final stage
FROM python:3.11.1-slim

# MinerU dependencies, for the cv module
ARG MINERU_DEPS="libglib2.0-0 libgl1"

# LibreOffice is required by MinerU for converting docs to PDF
ARG LIBREOFFICE_DEPS="libreoffice"
# Install Chinese fonts to prevent garbled text when converting docs
ARG LIBREOFFICE_FONT_DEPS="fonts-noto-cjk fonts-wqy-zenhei fonts-wqy-microhei fontconfig"

# Install minimal system dependencies in one layer and clean up
RUN apt update && \
    apt install --no-install-recommends -y curl \
        ${MINERU_DEPS} ${LIBREOFFICE_DEPS} ${LIBREOFFICE_FONT_DEPS} && \
    apt clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /var/cache/apt/archives/*

# Copy the entire virtual environment
COPY --from=builder /opt/venv /opt/venv

# Make sure we use the virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY . /app

WORKDIR /app

# Install the application in development mode so Python can find all modules
RUN . /opt/venv/bin/activate && pip install -e .

ENTRYPOINT ["/app/scripts/entrypoint.sh"]
