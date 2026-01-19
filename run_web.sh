#!/bin/sh -f

export PROJECT_ROOT=$( cd "$( dirname "$0" )" && pwd )
. $PROJECT_ROOT/venv/bin/activate
export PYTHONPATH=$PROJECT_ROOT/src
export FLASK_ENV=development

echo "Project root      = $PROJECT_ROOT"
echo "Python Path       = $PYTHONPATH"
echo "Database Path     = $NATURE_RECORDER_DB"
echo "Flask Environment = $FLASK_ENV"

python -m hieroglyphics
