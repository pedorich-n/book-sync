import "dev/justfile.default"

default:
    just --list

clean-venv:
    uv venv --clear

sync:
    uv sync --all-extras

run:
    uv run book-sync
