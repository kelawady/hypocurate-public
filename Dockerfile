# One image for the web service and the worker (PRD Section 6).
# Python 3.14: dspy, litellm, statsmodels and scipy all publish releases for it (checked 2026-10-04).
FROM python:3.14-slim@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151 AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app

COPY requirements.lock ./
RUN pip install --require-hashes -r requirements.lock \
    && useradd --create-home --uid 10001 app

# Only the package and the frozen data. tests/ and docs/ hold expected answers
# and stay out of the deployed image (step 1 summary, open item 4).
COPY hypocurate/ hypocurate/
COPY data/ data/

USER app
EXPOSE 8000
# One process, so the in-memory login limit is shared. Render sets PORT.
CMD ["sh", "-c", "exec uvicorn hypocurate.web.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]


# The regression suite, run in the same image (docker compose run --rm test; GitHub Actions).
FROM runtime AS test
USER root
COPY requirements-dev.lock ./
RUN pip install --require-hashes -r requirements-dev.lock
COPY . .
RUN chown -R app /app
USER app
CMD ["pytest", "-q"]
