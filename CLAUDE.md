# CLAUDE.md

Entry points for working in this repo.

## What this is

`pyobs-fli` is a `pyobs` module for [FLI](http://www.flicamera.com/) cameras and filter wheels
(`FliCamera`, `FliFilterWheel`). Wraps the FLI SDK via Cython; requires the FLI kernel module
installed on the system.

## Design history and planning

This repo keeps its own implementation plans under `specs/plans/`. Design docs and ADRs that
concern `pyobs-fli` live in `pyobs-core`'s `specs/` tree instead, tagged with a `Repos:` line — see
`pyobs-core/CLAUDE.md`'s "Cross-repo docs" section for the convention.

## Tooling

- Lint: `ruff` (config in `pyproject.toml`)
- Format: `black`
- Type checking: `pyrefly` (excludes `pyobs_fli/gui.py`)
- Tests: `pytest` (`asyncio_mode = "strict"`)
