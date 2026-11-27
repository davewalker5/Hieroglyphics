#!/usr/bin/env bash

set -euo pipefail

project_root="$(cd "$(dirname "$0")/.." && pwd)"
python_command=python3
if [[ -x "$project_root/venv/bin/python" ]]; then
    python_command="$project_root/venv/bin/python"
fi

if [[ $# -eq 0 || "$1" == --output ]]; then
    set -- "$project_root/data/catalogue-content.txt" "$project_root/data/Unikemet.txt" "$@"
fi

export PYTHONPATH="$project_root/src${PYTHONPATH:+:$PYTHONPATH}"
exec "$python_command" -m hieroglyphics.catalogue.signs "$@"
