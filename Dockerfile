FROM python:3.13-slim
ARG UID=1000
ARG GID=1000

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Create non-root user

RUN groupadd -g "${GID}" python \
  && useradd --create-home --no-log-init -u "${UID}" -g "${GID}" python
USER python

# Copy the application into the container.
COPY --chown=python: pyproject.toml uv.lock /app

# Install the application dependencies.
WORKDIR /app
RUN uv sync --frozen --no-cache
COPY --chown=python: . /app

# Run the application.
CMD ["/app/.venv/bin/fastapi", "run", "app/main.py", "--port", "8000", "--host", "0.0.0.0"]
