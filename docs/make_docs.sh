#!/bin/zsh -f

source ../venv/bin/activate
PROJECTDIR=${0:a:h}/..
export PYTHONPATH="$PROJECTDIR/src:$PROJECTDIR/tests"
echo "Python path is set to: $PYTHONPATH"
make html
deactivate
