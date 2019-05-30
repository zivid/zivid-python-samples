#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR=$(realpath "$SCRIPT_DIR/..")

pythonFiles=$(find "$ROOT_DIR" -name '*.py')

echo Running black on:
echo "$pythonFiles"
black --check --diff $pythonFiles || exit $?

echo Success! ["$(basename $0)"]
