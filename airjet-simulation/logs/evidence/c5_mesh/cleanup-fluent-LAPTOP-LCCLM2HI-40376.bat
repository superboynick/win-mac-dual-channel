echo off
set LOCALHOST=%COMPUTERNAME%
set KILL_CMD="D:\ansys\ANSYS Inc\ANSYS Student\v261\fluent/ntbin/win64/winkill.exe"

start "tell.exe" /B "D:\ansys\ANSYS Inc\ANSYS Student\v261\fluent\ntbin\win64\tell.exe" LAPTOP-LCCLM2HI 11629 CLEANUP_EXITING
timeout /t 1
"D:\ansys\ANSYS Inc\ANSYS Student\v261\fluent\ntbin\win64\kill.exe" tell.exe
if /i "%LOCALHOST%"=="LAPTOP-LCCLM2HI" (%KILL_CMD% 11292) 
if /i "%LOCALHOST%"=="LAPTOP-LCCLM2HI" (%KILL_CMD% 40376) 
if /i "%LOCALHOST%"=="LAPTOP-LCCLM2HI" (%KILL_CMD% 29468)
del "C:\Users\admin\win-mac-dual-channel\airjet-simulation\logs\evidence\c5_mesh\cleanup-fluent-LAPTOP-LCCLM2HI-40376.bat"
