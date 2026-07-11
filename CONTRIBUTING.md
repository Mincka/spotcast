# Contributing to Spotcast

Thank you for considering a contribution to Spotcast! This document explains how the project is organized and what is expected from a pull request.

## Branch model

- `main` — stable branch; releases are tagged from here.
- `dev` — integration branch; **open your pull requests against `dev`**.
- Use descriptive branch names such as `feature/<topic>`, `bugfix/<topic>` or `chore/<topic>`.

## Development setup

The project uses [uv](https://docs.astral.sh/uv/) for dependency management and [Task](https://taskfile.dev/) as a task runner (both optional, but convenient):

```bash
git clone https://github.com/Mincka/spotcast.git
cd spotcast
uv sync
```

Common tasks:

```bash
task test        # run the unit tests
task coverage    # run the tests with branch coverage
```

Without `task`/`uv`, the equivalent commands are:

```bash
python -m unittest discover -s ./test -p "test_*.py"
coverage run --branch --omit=./test/* -m unittest discover -s ./test -p "test_*.py"
```

A set of container definitions is available under `container/` (`compose.stable.yaml`, `compose.dev.yaml`, `compose.beta.yaml`, `compose.custom_version.yaml`) to test the integration against different Home Assistant versions with `podman-compose` (e.g. `task podman:stable`).

## Quality gates

Pull requests must pass the CI workflows before they can be merged:

- **Tests**: all unit tests must pass, and new code must come with full test coverage. The overall coverage gate is 70%, but aim to fully cover the code you add or change.
- **Lint**: `pylint` on `custom_components` must score **9/10 or higher** (`pylint --fail-under 9 custom_components`).
- **hassfest / HACS validation**: the integration must remain valid for Home Assistant and HACS.

## Documentation

If your change adds or modifies an action, entity or WebSocket endpoint, update the matching page under `docs/` and the tables in `README.md`.

## Releases

Versioning is handled with `bump2version` (see `.bumpversion.cfg`); it keeps `manifest.json`, `custom_components/spotcast/__init__.py` and `pyproject.toml` in sync. Maintainers cut releases as git tags with GitHub Releases.
