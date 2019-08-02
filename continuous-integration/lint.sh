#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR=$(realpath "$SCRIPT_DIR/..")

pythonFiles=$(find "$ROOT_DIR" -name '*.py')

echo Running black on:
echo "$pythonFiles"
black --check --diff $pythonFiles || exit $?

echo Running flake8 on:
echo "$pythonFiles"
flake8 --config="$ROOT_DIR/.flake8" $pythonFiles || exit $?

echo Running pylint on:
echo "$pythonFiles"
pylint -j 0 --rcfile "$ROOT_DIR/.pylintrc" --extension-pkg-whitelist=netCDF4 $pythonFiles || exit $?

echo Running darglint on:
echo "$pythonFiles"
darglint $pythonFiles || exit $?

echo Success! ["$(basename $0)"]
