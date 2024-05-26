#!/bin/bash

# Ensure the build tools are installed
pip install setuptools

# Proceed with the usual installation
pip install --disable-pip-version-check --target . --upgrade -r requirements.txt
