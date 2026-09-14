@echo off
rem build.cmd        -> baut waldweg.nds
rem build.cmd clean  -> loescht Build-Dateien
call "%~dp0wf.cmd" make -j8 %*
exit /b %ERRORLEVEL%
