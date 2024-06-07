@echo off
REM cywin_installer.bat - windows script to install cywin on the local machine
REM                       with an option list of specific components.
REM
REM author: richard.t.jones at uconn.edu
REM version: june 7, 2024

setlocal

if "%1"=="" (
    echo usage: "cywin_installer <install_prefix> [ <cygwin_package_1> ... ]"
    exit /b 1
)

REM Define the URL for the Cygwin setup executable
set CYGWIN_SETUP_URL=https://cygwin.com/setup-x86_64.exe

REM Define the path where the setup executable will be saved
set INSTALL_DIR=%1
set CYGWIN_SETUP_PATH=%INSTALL_DIR%\bin\setup-x86_64.exe

REM URL of the Cygwin mirror
set CYGWIN_MIRROR_URL=http://cygwin.mirror.constant.com

REM Directory where Cygwin is installed
set CYGWIN_ROOT=%INSTALL_DIR%

REM Check if curl is available, otherwise use bitsadmin
echo Checking for curl...
curl --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Downloading Cygwin setup executable using curl...
    curl -L -o %CYGWIN_SETUP_PATH% %CYGWIN_SETUP_URL%
) else (
    echo Curl not found. Using bitsadmin to download the Cygwin setup executable...
    bitsadmin /transfer "DownloadCygwinSetup" /priority normal %CYGWIN_SETUP_URL% %CYGWIN_SETUP_PATH%
)

REM Verify the download
if exist %CYGWIN_SETUP_PATH% (
    echo Cygwin setup executable downloaded successfully to %CYGWIN_SETUP_PATH%.
) else (
    echo Failed to download the Cygwin setup executable.
    exit /b 1
)

REM Check if the setup executable exists
if not exist "%CYGWIN_SETUP_PATH%" (
    echo Cygwin setup executable not found at %CYGWIN_SETUP_PATH%.
    exit /b 1
)

REM Install the packages using the Cygwin setup executable
shift
if "%1"=="" goto end_install_packages

echo Installing %PACKAGE% package...
"%CYGWIN_SETUP_PATH%" -q -P %1 -s %CYGWIN_MIRROR_URL% -R %CYGWIN_ROOT%

REM Verify the installation
echo Verifying the installation of %1 package...
%CYGWIN_ROOT%\bin\cygcheck -c %1

echo Installation of %1 package completed successfully.

endlocal
