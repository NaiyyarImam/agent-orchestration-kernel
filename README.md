# JARVIS Kernel

Stable Kernel Architecture: orchestration, policy, execution, lifecycle,
recovery, observability, context, and memory coordination.

## Development

### Create a virtual environment

```sh
python3 -m venv .venv
source .venv/bin/activate
```

### Install dependencies

```sh
python -m pip install -r requirements.txt
```

### Run tests

```sh
python -m pytest
```

### Run ruff

```sh
python -m ruff check .
```

### Run coverage

```sh
python -m pytest --cov=kernel
```

### Run formatting

```sh
python -m ruff format .
```

### Run mypy (optional)

```sh
python -m mypy kernel
```

Note: mypy is installed and runs, but the codebase is not type-clean at
the stable baseline; the command is provided for convenience only.
