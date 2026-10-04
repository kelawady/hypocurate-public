# One image for the web service and the worker (PRD Section 6).
# Python 3.14: dspy, litellm, statsmodels and scipy all publish releases for it (checked 2026-10-04).
#
# Stages: base -> test, and base -> runtime. The runtime stage is LAST, so a plain
# `docker build .` (what Render runs) gives the clean runtime image. The test
# stage is built only on request (`--target test`, docker compose's test service).
FROM python:3.14-slim@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151 AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore
WORKDIR /app

COPY requirements.lock ./
RUN pip install --require-hashes -r requirements.lock \
    && useradd --create-home --uid 10001 app

# Only the package and the frozen data. tests/ and docs/ hold expected answers
# and stay out of the deployed image (step 1 summary, open item 4).
COPY hypocurate/ hypocurate/
COPY data/ data/
USER app


# The regression suite, in the same base (docker compose run --rm test; GitHub Actions).
FROM base AS test
USER root
COPY requirements-dev.lock ./
RUN pip install --require-hashes -r requirements-dev.lock
COPY . .
RUN chown -R app /app
USER app
CMD ["pytest", "-q"]


# The deployed image: web service by default; the worker overrides the command.
FROM base AS runtime
USER app
EXPOSE 8000
# One process, so the in-memory login throttle is shared. Render sets PORT.
CMD ["sh", "-c", "exec uvicorn hypocurate.web.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
