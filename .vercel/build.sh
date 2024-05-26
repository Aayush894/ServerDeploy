#!/bin/bash

# Ensure the build tools are installed
python3.9 -m pip install --upgrade pip setuptools

# Proceed with the usual installation
python3.9 -m pip install --disable-pip-version-check --target . --upgrade -r requirements.txt
