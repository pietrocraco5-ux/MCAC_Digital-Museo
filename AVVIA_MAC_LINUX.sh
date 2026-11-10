#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
python3 seed.py
python3 server.py
