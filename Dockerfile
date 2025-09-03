# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# Install system dependencies needed for building packages
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install the project into `/app`
WORKDIR /app

# # TODO: This is a hack to get the dependencies to work. We should use the lockfile and settings.
# # Enable bytecode compilation
# ENV UV_COMPILE_BYTECODE=1

# # Copy from the cache instead of linking since it's a mounted volume
# ENV UV_LINK_MODE=copy

# TODO: This is a hack to get the dependencies to work. We should use the lockfile and settings.
# # Install the project's dependencies using the lockfile and settings
# RUN --mount=type=cache,target=/root/.cache/uv \
#     --mount=type=bind,source=uv.lock,target=uv.lock \
#     --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
#     uv sync --locked --no-install-project --no-dev

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
COPY . /app
# # TODO: This is a hack to get the dependencies to work. We should use the lockfile and settings.
# RUN --mount=type=cache,target=/root/.cache/uv \
#     uv sync --locked --no-dev

RUN uv sync --no-dev

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

# Activate the virtual environment and run the application
RUN echo 'source /app/.venv/bin/activate' >> ~/.bashrc
CMD ["/app/.venv/bin/python", "app.py"]
