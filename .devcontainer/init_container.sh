#!/bin/bash

set -e

BOARD=adafruit_feather_rp2040_can

sudo circuitpython_setboard $BOARD

pre-commit install

pip install -e .
