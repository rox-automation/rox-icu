#!/bin/bash
set -e

python -m venv venv
source venv/bin/activate && pip install -r requirements.txt
