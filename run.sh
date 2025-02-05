#!/usr/bin/env bash

cd $(dirname $(realpath $0))
source .venv/bin/activate

./mcp-wrapper -ul logs python3 patentsafe_mcp.py "$@"
