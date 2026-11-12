@echo off
setlocal
title Football Dashboard (close this window to stop)
cd /d "%~dp0"

rem First run: create the virtual environment and install dependencies.
if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    py -3 -m venv .venv 2>nul || python -m venv .venv
    if errorlevel 1 (
        echo Could not create .venv. Make sure Python 3.10+ is installed.
        pause
        exit /b 1
    )
    echo Installing dependencies...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Dependency install failed.
        pause
        exit /b 1
    )
)

rem Skip Streamlit's one-time "enter your email" prompt (same file it writes itself).
if not exist "%USERPROFILE%\.streamlit\credentials.toml" (
    if not exist "%USERPROFILE%\.streamlit" mkdir "%USERPROFILE%\.streamlit"
    (echo [general]& echo email = "") > "%USERPROFILE%\.streamlit\credentials.toml"
)

rem Pick the first free port from 8501 upward (checks IPv4 and IPv6 listeners).
set "PORT="
for /f "delims=" %%p in ('powershell -NoProfile -Command "$u=[Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().GetActiveTcpListeners().Port; (8501..8999).Where({$u -notcontains $_},'First')"') do set "PORT=%%p"

echo.
if defined PORT (
    echo Starting dashboard at http://localhost:%PORT%
) else (
    echo Starting dashboard ^(Streamlit will print the URL below^)
)
echo Close this window (or press Ctrl+C) to stop the server.
echo.
if defined PORT (
    ".venv\Scripts\python.exe" -m streamlit run app.py --server.port %PORT%
) else (
    rem Port lookup failed: let Streamlit choose, it skips busy ports itself.
    ".venv\Scripts\python.exe" -m streamlit run app.py
)

rem Keep the window open if Streamlit exits with an error so it can be read.
if errorlevel 1 pause
endlocal
