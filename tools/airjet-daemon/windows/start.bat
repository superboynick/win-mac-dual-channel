@echo off
start /B powershell -NoProfile -WindowStyle Hidden -ExecutionPolicy RemoteSigned -File "%~dp0\daemon.ps1"
echo Daemon started — auto-starts on next boot if installed via install.ps1
