#!/bin/bash

# Install Python dependencies
if [ -f requirements.txt ]; then
    pip3 install --user -r requirements.txt
else
    echo "No requirements.txt file found."
fi

# Run pip install -e . to install the package in editable mode
pip install -e .

# Install Rust
curl https://sh.rustup.rs -sSf | sh
