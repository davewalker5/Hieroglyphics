#!/bin/sh -f

export PROJECT_ROOT=$( cd "$(dirname "$0")" ; pwd -P )
export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"
gunicorn --bind=0.0.0.0 --timeout 600 app:app
