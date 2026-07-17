@echo off
start "AirJet Daemon" powershell -NoProfile -NoExit -ExecutionPolicy RemoteSigned -File "%~dp0\daemon.ps1"
