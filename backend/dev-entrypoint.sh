#!/usr/bin/env bash
set -e

git config --global --add safe.directory /workspace
uv sync --frozen
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
