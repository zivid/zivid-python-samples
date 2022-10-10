#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR=$(realpath "$SCRIPT_DIR/..")
SOURCE_DIR=$(realpath "$ROOT_DIR/source")

python3 -m pip install --requirement "$SCRIPT_DIR/requirements.txt" || exit $?

pythonFiles=$(find "$SOURCE_DIR" -name '*.py' -not -path "*/ur_hand_eye_calibration/3rdParty*")

echo Running black on:
echo "$pythonFiles"
black --config="$ROOT_DIR/pyproject.toml" --check --diff $pythonFiles || exit $?

echo Running flake8 on:
echo "$pythonFiles"
flake8 --config="$ROOT_DIR/.flake8" $pythonFiles || exit $?

echo Running pylint on:
echo "$pythonFiles"

pylint \
    -j 0 \
    --rcfile "$ROOT_DIR/.pylintrc" \
    --dummy-variables-rgx="((^|, )(app|rgb|xyz|contrast))+$" \
    --extension-pkg-whitelist=netCDF4 \
    $pythonFiles ||
    exit $?

echo Running darglint on:
echo "$pythonFiles"
darglint $pythonFiles || exit $?

echo Success! ["$(basename $0)"]
