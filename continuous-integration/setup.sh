#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR=$(realpath "$SCRIPT_DIR/..")

export DEBIAN_FRONTEND=noninteractive

function apt-yes {
    apt-get --assume-yes "$@"
}

apt-yes update || exit $?
apt-yes dist-upgrade || exit $?

apt-yes install \
    python3-pip \
    || exit $?

pip3 install -r $SCRIPT_DIR/requirements.txt || exit $?
pip3 install -r $ROOT_DIR/requirements.txt || exit $?

echo Success! ["$(basename $0)"]
