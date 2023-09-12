#!/bin/bash

set -euo pipefail

cd tmp

pdm install
pdm run test
