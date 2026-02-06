# Use Python 3.12 slim image
FROM python:3.12-slim-bookworm

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Set workdir
WORKDIR /app

# Install system dependencies in one layer
RUN apt-get update --yes --quiet && \
    apt-get install --yes --quiet --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libwebp-dev \
    libffi-dev \
    libssl-dev \
    gettext \
    && rm -rf /var/lib/apt/lists/*

# Install pip-tools for dependency management (optional but recommended)
RUN pip install --upgrade pip setuptools wheel

# Copy only requirements first (for better caching)
COPY requirements.txt .

# Use Docker’s build cache for pip downloads
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Install Playwright system deps + Chromium; cache browser binaries so rebuilds reuse them
RUN --mount=type=cache,target=/root/.cache/ms-playwright \
    playwright install-deps && playwright install chromium

# Copy the app source
COPY . .

# Expose Django port
EXPOSE 8000

# Start container (use sh to avoid needing chmod on host when .:/app is mounted)
CMD ["sh", "entrypoint.sh"]
