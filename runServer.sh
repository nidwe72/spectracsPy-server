#!/usr/bin/env bash
# Launch the local Spectracs Pyro5 server for development.
# --local drops the NAT host and binds nameserver:8090 + daemon:8091 to the LAN IP
# (NetworkUtil picks the wlp*/eth0* interface). Reuses the app venv (no server venv exists).
# Needs ../spectracsPy on the path too: it imports logic.spectral.util.SpectralLineMasterDataUtil
# from the app repo.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"
export PYTHONPATH=".:../spectracsPy:../spectracsPy-model:../spectracsPy-base"
exec ../spectracsPy/venv/bin/python spectracsPyServer.py --local "$@"
