@echo off
start /B powershell -NoProfile -WindowStyle Hidden -ExecutionPolicy RemoteSigned -File "%~dp0\tray_daemon.ps1"
echo AirJet daemon started -- icon in system tray (bottom-right)
