# =============================================================================
# EVOLVER Tools — Docker Image
# Multi-stage build for minimal image size
# =============================================================================

# ---- Stage 1: Build ----
FROM python:3.12-slim AS builder

WORKDIR /build

# Copy only what's needed for installation
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Build and install the package
RUN pip install --no-cache-dir --user .

# ---- Stage 2: Runtime ----
FROM python:3.12-slim

# Copy installed package from builder
COPY --from=builder /root/.local /root/.local

# Ensure local bin is in PATH
ENV PATH=/root/.local/bin:$PATH

# Set working directory
WORKDIR /data

# Entry point: evtool command
ENTRYPOINT ["evtool"]
CMD ["--help"]
