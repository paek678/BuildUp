@echo off
setlocal

set "ROOT=%~dp0.."
set "SERVER="

for /d %%D in ("%ROOT%\Library\PackageCache\com.gamelovers.mcp-unity@*") do (
    if exist "%%~fD\Server~\build\index.js" (
        set "SERVER=%%~fD\Server~\build\index.js"
        goto run
    )
)

echo MCP Unity server build not found. 1>&2
echo Open this Unity project once so Package Manager downloads com.gamelovers.mcp-unity. 1>&2
echo If the package is present but the build folder is missing, open Tools ^> MCP Unity ^> Server Window and run Force Install Server. 1>&2
exit /b 1

:run
node "%SERVER%" %*
