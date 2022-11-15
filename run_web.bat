@ECHO OFF
SET PROJECT_ROOT=%~p0
CALL %PROJECT_ROOT%\venv\Scripts\activate.bat
SET PYTHONPATH=%PROJECT_ROOT%src
SET FLASK_DEBUG=1

ECHO Project root      = %PROJECT_ROOT%
ECHO Python Path       = %PYTHONPATH%
ECHO Flask Debug       = %FLASK_DEBUG%

python -m hieroglyphics %*
ECHO ON
