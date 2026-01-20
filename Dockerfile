# Use Python 3.12 slim image
FROM python:3.12-slim-bookworm

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Set workdir
WORKDIR /app

# Install system dependencies (Playwright + Django + Pillow + PostgreSQL)
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
    curl \
    wget \
    ca-certificates \
    fonts-liberation \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libxdamage1 \
    libxfixes3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libatspi2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip tooling
RUN pip install --upgrade pip setuptools wheel

# Copy only requirements first (better cache usage)
COPY requirements.txt .

# Install Python dependencies
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Install Playwright browsers (Chromium, Firefox, WebKit)
RUN python -m playwright install --with-deps

# Copy application source
COPY . .

# Entrypoint permissions
RUN chmod +x entrypoint.sh

# Expose Django port
EXPOSE 8000

# Start container
CMD ["./entrypoint.sh"]
