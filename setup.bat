@echo off
REM Windows batch script for setup

echo ========================================
echo Expense Splitter API - Setup Script
echo ========================================
echo.

REM Check Python
echo 1. Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found. Please install Python 3.10+
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do echo %% i
echo.

REM Create venv
echo 2. Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo Virtual environment created
) else (
    echo Virtual environment already exists
)
echo.

REM Activate venv
echo 3. Activating virtual environment...
call venv\Scripts\activate.bat
echo Virtual environment activated
echo.

REM Install requirements
echo 4. Installing dependencies...
pip install -r requirements.txt >nul 2>&1
echo Dependencies installed
echo.

REM Setup .env
echo 5. Setting up environment variables...
if not exist ".env" (
    copy .env.example .env
    echo .env file created
    echo WARNING: Please update .env with your database credentials
) else (
    echo .env file already exists
)
echo.

REM Initialize database
echo 6. Initializing database...
python -c "
from app.database import db_manager
try:
    db_manager.init_postgres()
    db_manager.create_tables()
    print('Database initialized successfully!')
except Exception as e:
    print(f'Database initialization failed: {e}')
"
echo.

REM Summary
echo ========================================
echo Setup complete!
echo ========================================
echo.
echo Next steps:
echo 1. Activate virtual environment:
echo    venv\Scripts\activate
echo.
echo 2. Start development server:
echo    uvicorn app.main:app --reload
echo.
echo 3. Access API documentation:
echo    http://localhost:8000/docs
echo.
echo 4. Run tests:
echo    pytest
echo.
echo Happy coding! 🚀
echo.
pause
