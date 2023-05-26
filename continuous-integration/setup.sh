#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR=$(realpath "$SCRIPT_DIR/..")

ZIVID_SDK_EXACT_VERSION=2.9.0+4dbba385-1
ZIVID_TELICAM_EXACT_VERSION=3.0.1.1-3

export DEBIAN_FRONTEND=noninteractive
source /etc/os-release || exit $?

function apt-yes {
    apt-get --assume-yes "$@"
}

function install_www_deb {
    TMP_DIR=$(mktemp --tmpdir --directory zivid-python-install-www-deb-XXXX) || exit $?
    pushd $TMP_DIR || exit $?
    wget -nv "$@" || exit $?
    apt-yes install --fix-broken ./*deb || exit $?
    popd || exit $?
    rm -r $TMP_DIR || exit $?
}

apt-yes update || exit
apt-yes dist-upgrade || exit

apt-yes install \
    python3-pip \
    wget ||
    exit $?

install_www_deb "https://downloads.zivid.com/sdk/releases/${ZIVID_SDK_EXACT_VERSION}/u${VERSION_ID:0:2}/zivid-telicam-driver_${ZIVID_TELICAM_EXACT_VERSION}_amd64.deb" || exit $?
install_www_deb "https://downloads.zivid.com/sdk/releases/${ZIVID_SDK_EXACT_VERSION}/u${VERSION_ID:0:2}/zivid_${ZIVID_SDK_EXACT_VERSION}_amd64.deb" || exit $?

python3 -m pip install --upgrade pip || exit
python3 -m pip install --requirement "$ROOT_DIR/requirements.txt" || exit

echo Success! ["$(basename $0)"]
