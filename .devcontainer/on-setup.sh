#!/usr/bin/env bash

set -e

set_tools() {
    sudo apt-get update
    # Dev Tunnel
    curl -sL https://aka.ms/DevTunnelCliInstall | bash
}

set_dapr_config() {
    dapr uninstall # clean if needed
    dapr init
}

# Install tools
set_tools
set_dapr_config

# Prefetch dependencies
pip install -r ./src/backend/requirements.txt
