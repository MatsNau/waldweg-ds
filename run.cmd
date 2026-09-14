@echo off
rem Baut das Spiel und startet es in melonDS.
setlocal
if not defined MELONDS set "MELONDS=C:\Programming\tools\melonDS\melonDS.exe"
call "%~dp0build.cmd" || exit /b 1
start "" "%MELONDS%" "%~dp0waldweg.nds"
