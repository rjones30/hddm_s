:: Downloads and installs a recent version of cmake
:: on the windows platform, tested on Windows 10.
:: After execution, the command cmake.exe is in PATH.

set cmake=cmake-3.29.2-windows-x86_64
curl -L https://github.com/Kitware/CMake/releases/download/v3.29.2/%cmake%.zip --output %cmake%.zip
tar xf %cmake%.zip
set PATH=%PATH%;%cmake%/bin
