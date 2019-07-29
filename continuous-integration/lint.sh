#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR=$(realpath "$SCRIPT_DIR/..")

VENV=$(mktemp --tmpdir --directory zivid-python-samples-lint-venv-XXXX) || exit $?
python -m venv "$VENV" || exit $?
source $VENV/bin/activate || exit $?

pythonFiles=$(find "$ROOT_DIR" -name '*.py')

echo Installing requirements
pip install -r "$ROOT_DIR/requirements.txt" || exit $?
pip install -r "$SCRIPT_DIR/requirements.txt" || exit $?

echo Running black on:
echo "$pythonFiles"
black --check --diff $pythonFiles || exit $?

echo Running flake8 on:
echo "$pythonFiles"
flake8 --config="$ROOT_DIR/.flake8" $pythonFiles || exit $?

echo Running pylint on:
echo "$pythonFiles"
pylint -j 0 --rcfile "$ROOT_DIR/.pylintrc" $pythonFiles || exit $?

echo Success! ["$(basename $0)"]
