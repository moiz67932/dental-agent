###############################################################################
# ──────────────── 1. Build stage – install wheels into /install ─────────────
###############################################################################
FROM python:3.10-slim-bookworm AS build

# Runtime libs for ffmpeg / audio
RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg libsndfile1 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Leverage Docker-layer caching: copy lock/reqs first
COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

###############################################################################
# ───────────── 2. Runtime stage – only what we really need ──────────────────
###############################################################################
FROM python:3.10-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Copy site-packages from build layer
COPY --from=build /install /usr/local

# Copy project source
COPY . /app

# Non-root user for security
RUN addgroup --system agent && adduser --system --ingroup agent agent
USER agent

WORKDIR /app

# (Optional) expose the UDP port LiveKit will open
EXPOSE 5060/udp

# Cheap always-on health endpoint (adjust to something real later)
HEALTHCHECK CMD wget --spider -q http://127.0.0.1:9102/metrics || exit 1

# ----------  start the voice-agent worker  ----------
# JSON array syntax **is mandatory** here
ENTRYPOINT ["python", "agent.py"]
