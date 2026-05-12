# ── Stage 1: install dependencies ────────────────────────────────────────────
FROM python:3.13-alpine AS builder

RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev

COPY requirements.txt /tmp/
RUN python -m venv /venv && \
    /venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt

# ── Stage 2: runtime image ────────────────────────────────────────────────────
FROM python:3.13-alpine AS runtime

# Runtime-only shared libs needed by cryptography / SSL
RUN apk add --no-cache libffi openssl

COPY --from=builder /venv /venv
COPY pyproject.toml /app/
COPY kube_lookout/ /app/kube_lookout/

RUN /venv/bin/pip install --no-cache-dir --no-deps /app

ENTRYPOINT ["/venv/bin/python", "-u", "-m", "kube_lookout.main"]
