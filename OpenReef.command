#!/bin/zsh
# Double-click in Finder, or drop a dataset folder onto this file.

set -eu

launcher="/Users/rof011/Desktop/LC_timelapse/openreef.sh"
default_dataset="/Users/rof011/Desktop/LC_timelapse/cervicornis"

if [[ ! -x "$launcher" ]]; then
    print -u2 "OpenReef launcher was not found at: $launcher"
    print -u2 "Press Return to close."
    read -r
    exit 1
fi

if (( $# > 0 )); then
    exec "$launcher" "$1"
elif [[ -d "$default_dataset" ]]; then
    exec "$launcher" "$default_dataset"
else
    exec "$launcher"
fi
