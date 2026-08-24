@echo off
REM ==============================================================================
REM Research Assistant with Memory - Windows Stop Script
REM ==============================================================================

echo =====================================================
echo    Stopping Research Assistant Services...
echo =====================================================

REM Terminate tasks listening on ports 8000, 5173, 8501
for %%P in (8000 5173 8501) do (
  for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":%%P" ^| findstr "LISTENING"') do (
    echo Stopping process on port %%P (PID %%a)...
    taskkill /F /PID %%a >nul 2>&1
  )
)

echo.
echo All services on ports 8000, 5173, and 8501 have been stopped.
echo =====================================================
