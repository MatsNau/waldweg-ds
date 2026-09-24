@echo off
rem build.cmd        -> baut waldweg.nds
rem build.cmd clean  -> loescht Build-Dateien
rem Ist in WSL die Toolchain installiert (tools/setup_wsl.sh), wird dort gebaut -
rem Smart App Control blockiert die Windows-Toolchain. Sonst ueber wf.cmd.
wsl.exe -d Ubuntu -- test -x /opt/wonderful/bin/wf-pacman >nul 2>&1
if %ERRORLEVEL%==0 (
    wsl.exe -d Ubuntu --cd "%~dp0." -- make -j8 %*
) else (
    call "%~dp0wf.cmd" make -j8 %*
)
exit /b %ERRORLEVEL%
