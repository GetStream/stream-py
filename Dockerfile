# Use the official Python image as the base image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install Poetry
RUN pip install --upgrade pip && \
    pip install poetry

# Copy the pyproject.toml and poetry.lock files
COPY pyproject.toml poetry.lock ./

# Install app dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi

# Copy the entire project
COPY . .

# Make sure the 'stream' package can be imported in the container
RUN python -c 'import stream'

# Set the entrypoint for the CLI
ENTRYPOINT ["poetry", "run", "create-token"]