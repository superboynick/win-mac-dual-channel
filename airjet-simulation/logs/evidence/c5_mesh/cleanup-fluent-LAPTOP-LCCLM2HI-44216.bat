echo off
set LOCALHOST=%COMPUTERNAME%
set KILL_CMD="D:\ansys\ANSYS Inc\ANSYS Student\v261\fluent/ntbin/win64/winkill.exe"

start "tell.exe" /B "D:\ansys\ANSYS Inc\ANSYS Student\v261\fluent\ntbin\win64\tell.exe" LAPTOP-LCCLM2HI 10110 CLEANUP_EXITING
timeout /t 1
"D:\ansys\ANSYS Inc\ANSYS Student\v261\fluent\ntbin\win64\kill.exe" tell.exe
if /i "%LOCALHOST%"=="LAPTOP-LCCLM2HI" (%KILL_CMD% 45760) 
if /i "%LOCALHOST%"=="LAPTOP-LCCLM2HI" (%KILL_CMD% 44216) 
if /i "%LOCALHOST%"=="LAPTOP-LCCLM2HI" (%KILL_CMD% 44124)
del "C:\Users\admin\win-mac-dual-channel\airjet-simulation\logs\evidence\c5_mesh\cleanup-fluent-LAPTOP-LCCLM2HI-44216.bat"
