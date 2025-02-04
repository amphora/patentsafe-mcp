#!/usr/bin/env bash

cd $(dirname $(realpath $0))
source .venv/bin/activate

./mcp-wrapper -ul logs $HOME/.local/bin/uv run --with 'mcp[cli]' mcp run patentsafe_mcp.py
