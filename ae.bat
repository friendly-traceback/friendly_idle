echo off
REM Default is Python 3.10

if "%1"=="3.9" goto py_39

:py_310
venv-friendly-idle-3.10\scripts\activate
goto end

:py_39
venv-friendly-idle-3.9\scripts\activate
goto end

:end
