#!/bin/sh
# Installs the BlocksDS toolchain (Wonderful) inside WSL, so the ROM can be
# built without Windows executables. Smart App Control blocks the Windows
# toolchain on this machine; it does not inspect Linux binaries.
#
# Run once as root:  wsl -d Ubuntu -u root -- sh tools/setup_wsl.sh
set -e

apt-get update -qq
apt-get install -y -qq make wget ca-certificates xz-utils > /dev/null

if [ ! -x /opt/wonderful/bin/wf-pacman ]; then
    mkdir -p /opt/wonderful
    wget -q -O /tmp/wf-bootstrap.tar.gz https://wonderful.asie.pl/bootstrap/wf-bootstrap-x86_64.tar.gz
    tar xzf /tmp/wf-bootstrap.tar.gz -C /opt/wonderful
    rm /tmp/wf-bootstrap.tar.gz
fi

export PATH="/opt/wonderful/bin:$PATH"

# wf-pacman updates itself on the first run, so the first sync runs twice.
wf-pacman -Syu --noconfirm --needed wf-tools
wf-pacman -Syu --noconfirm --needed wf-tools
wf-config repo enable blocksds
wf-pacman -Syu --noconfirm --needed wf-tools
wf-pacman -S --noconfirm --needed blocksds-toolchain blocksds-nitroengine blocksds-nflib

echo "Toolchain bereit: $(ls /opt/wonderful/thirdparty/blocksds/external | tr '\n' ' ')"
