#!/bin/env bash
set -euo pipefail

# This script is never run in CI. This is just a convenience for humans.

./lint-shell.sh

./lint-black.sh
./lint-flake8.sh
./lint-isort.sh
./lint-package-types.sh
./lint-test-types.sh
./lint-yaml.sh
