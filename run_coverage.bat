@ECHO OFF
SET PROJECT_ROOT=%~p0
CALL %PROJECT_ROOT%\venv\Scripts\activate.bat
SET PYTHONPATH=%PROJECT_ROOT%src

ECHO Project root      = %PROJECT_ROOT%
ECHO Python Path       = %PYTHONPATH%

python -m pytest --cov=src --cov-branch --cov-report html
ECHO ON