@echo off
rem Runs a command inside the Wonderful Toolchain (BlocksDS) environment, e.g.: wf.cmd make
setlocal
if not defined MSYS2_ROOT set "MSYS2_ROOT=C:\msys64"
set MSYS2_PATH_TYPE=inherit
set MSYSTEM=UCRT64
set CHERE_INVOKING=1
set BLOCKSDS=/opt/wonderful/thirdparty/blocksds/core
set BLOCKSDSEXT=/opt/wonderful/thirdparty/blocksds/external
set WONDERFUL_TOOLCHAIN=/opt/wonderful
set "PATH=%MSYS2_ROOT%\opt\wonderful\bin;%PATH%"
cd /d "%~dp0"
"%MSYS2_ROOT%\usr\bin\bash.exe" -lc "%*"
exit /b %ERRORLEVEL%
