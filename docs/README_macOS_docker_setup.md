# macOS Docker Setup and Running Guide

This guide helps you run the ProVoice project on macOS using Docker. The project is configured to support the `linux/amd64` platform and integrates the `uv` package manager.

## 1. Build and Create the Container

In the project root directory, use `docker-compose` to build the image and start the container:

```bash
docker-compose up --build -d
```

*   `--build`: Forces a rebuild of the image (essential after modifying code or configuration files).
*   `-d`: Runs the container in the background.
*   **Note**: The image build process automatically runs `uv sync` to synchronize the dependency environment.

## 2. Enter the Container Terminal (Interactive Debugging)

After the container starts, you can enter its internal terminal at any time for debugging or manually running the program:

```bash
docker exec -it provoice /bin/bash
```

*   `provoice` is the container name defined in `docker-compose.yml`.
*   After entering, the default working directory is `/app`.

## 3. Activate and Use the Python Environment

The project uses `uv` to manage the virtual environment, located at `/app/.venv`.

### Method A: Use `uv run` (Recommended)
No need to manually activate the environment. Execute the command directly, and `uv` will automatically point to the correct virtual environment:
```bash
# Run the main program
uv run python -m ProVoice.main
```

### Method B: Manually Activate the Virtual Environment
If you wish to use the `python` command directly in the current session:
```bash
source .venv/bin/activate
# Once activated, run directly
python -m ProVoice.main
```

## 5. Common Run Command Examples
Inside the container terminal:
```bash
# Run the main program with parameters
uv run python -m ProVoice.main participantid=001 modeltype=combined
```