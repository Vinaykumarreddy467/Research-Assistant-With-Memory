@echo off
REM ==============================================================================
REM Research Assistant with Memory - Windows Batch Launcher
REM ==============================================================================

echo =====================================================
echo    Starting Research Assistant Services on Windows
echo =====================================================

IF NOT EXIST .env (
  IF EXIST .env.example (
    echo Copying .env.example to .env...
    copy .env.example .env
  )
)

echo.
echo [1/3] Starting FastAPI Backend on port 8000...
cd backend
if not exist venv (
  echo Creating Python venv for backend...
  python -m venv venv
)
call venv\Scripts\activate.bat
pip install -q -r requirements.txt
start "Research Assistant Backend" cmd /k "venv\Scripts\activate.bat && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
cd ..

echo.
echo [2/3] Starting React Frontend on port 5173...
cd frontend
if not exist node_modules (
  echo Installing node_modules for frontend...
  call npm install
)
start "Research Assistant React Frontend" cmd /k "npm run dev"
cd ..

echo.
echo [3/3] Starting Streamlit Frontend on port 8501...
cd streamlit
if not exist venv (
  echo Creating Python venv for streamlit...
  python -m venv venv
)
call venv\Scripts\activate.bat
pip install -q -r requirements.txt
start "Research Assistant Streamlit Frontend" cmd /k "venv\Scripts\activate.bat && streamlit run app.py --server.port 8501"
cd ..

echo.
echo =====================================================
echo All services launched in separate windows!
echo   - React UI:     http://localhost:5173
echo   - Streamlit:    http://localhost:8501
echo   - FastAPI Docs: http://localhost:8000/docs
echo =====================================================
