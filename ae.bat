echo off
REM Default is Python 3.10

if "%1"=="3.6" goto py_36
if "%1"=="3.7" goto py_37
if "%1"=="3.8" goto py_38
if "%1"=="3.9" goto py_39

:py_310
venv-friendly-idle-3.10\scripts\activate
goto end

:py_36
venv-friendly-idle-3.6\scripts\activate
goto end

:py_37
venv-friendly-idle-3.7\scripts\activate
goto end

:py_38
venv-friendly-idle-3.8\scripts\activate
goto end

:py_39
venv-friendly-idle-3.9\scripts\activate
goto end



:end
