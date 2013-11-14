#!/bin/bash

set -e

HERE=$(echo $(dirname $(readlink -f $0)))
if [ "$(pwd)" != "$HERE" ]; then
    echo "This script must be run from $HERE. Aborting."
    exit 1
fi

[ -z "$(which sshd)" ] && sudo apt-get install openssh-server
[ -z "$(which pip)" ] && sudo apt-get install python-pip
[ -z "$(which fab)" ] && sudo pip install Fabric requests
