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
    python3-dev \
    cmake \
    python3-venv \
    python3-pip \
    alien \
    wget \
    || exit $?
function install_opencl_cpu_runtime {
    TMP_DIR=$(mktemp --tmpdir --directory zivid-setup-opencl-cpu-XXXX) || exit $?
    pushd $TMP_DIR || exit $?
    wget -q https://www.dropbox.com/s/0cvg8fypylgal2m/opencl_runtime_16.1.1_x64_ubuntu_6.4.0.25.tgz || exit $?
    tar -xf opencl_runtime_16.1.1_x64_ubuntu_6.4.0.25.tgz || exit $?
    alien -i opencl_runtime_*/rpm/*.rpm || exit $?
    mkdir -p /etc/OpenCL/vendors || exit $?
    ls /opt/intel/opencl*/lib64/libintelocl.so > /etc/OpenCL/vendors/intel.icd || exit $?
    popd || exit $?
    rm -r $TMP_DIR || exit $?
}
install_opencl_cpu_runtime || exit $?

function install_www_deb {
    TMP_DIR=$(mktemp --tmpdir --directory zivid-python-install-www-deb-XXXX) || exit $?
    pushd $TMP_DIR || exit $?
    wget -q "$@" || exit $?
    apt-yes install --fix-broken ./*deb || exit $?
    popd || exit $?
    rm -r $TMP_DIR || exit $?
}

install_www_deb https://www.zivid.com/hubfs/softwarefiles/releases/1.3.0+bb9ee328-10/u18/telicam-sdk_2.0.0.1-1_amd64.deb || exit $?
install_www_deb https://www.zivid.com/hubfs/softwarefiles/releases/1.3.0+bb9ee328-10/u18/zivid_1.3.0+bb9ee328-10_amd64.deb || exit $?

pip3 install -r $SCRIPT_DIR/requirements.txt || exit $?
pip3 install -r $ROOT_DIR/requirements.txt || exit $?

echo Success! ["$(basename $0)"]
