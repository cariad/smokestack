#!/bin/env bash
set -euo pipefail

# This script is never run in CI. This is just a convenience for humans.

./lint-shell

./lint-black
./lint-flake8
./lint-isort
./lint-package-types
./lint-test-types
./lint-yaml
