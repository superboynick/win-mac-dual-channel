echo off
set LOCALHOST=%COMPUTERNAME%
set KILL_CMD="D:\ansys\ANSYS Inc\ANSYS Student\v261\fluent/ntbin/win64/winkill.exe"

start "tell.exe" /B "D:\ansys\ANSYS Inc\ANSYS Student\v261\fluent\ntbin\win64\tell.exe" LAPTOP-LCCLM2HI 9806 CLEANUP_EXITING
timeout /t 1
"D:\ansys\ANSYS Inc\ANSYS Student\v261\fluent\ntbin\win64\kill.exe" tell.exe
if /i "%LOCALHOST%"=="LAPTOP-LCCLM2HI" (%KILL_CMD% 40884) 
if /i "%LOCALHOST%"=="LAPTOP-LCCLM2HI" (%KILL_CMD% 3356) 
if /i "%LOCALHOST%"=="LAPTOP-LCCLM2HI" (%KILL_CMD% 34900)
del "C:\Users\admin\win-mac-dual-channel\airjet-simulation\logs\evidence\c5_mesh\cleanup-fluent-LAPTOP-LCCLM2HI-3356.bat"
