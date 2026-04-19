@echo off
setlocal

for %%I in ("%~dp0..") do set "ROOT=%%~fI"
for %%I in ("%~dp0mcp-unity-codex.cmd") do set "MCP_LAUNCHER=%%~fI"

codex -C "%ROOT%" ^
  -c "mcp_servers.mcp-unity.command='cmd'" ^
  -c "mcp_servers.mcp-unity.args=['/c','%MCP_LAUNCHER%']" ^
  %*
