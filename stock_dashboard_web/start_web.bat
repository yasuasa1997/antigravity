@echo off
echo Starting Stock Dashboard Web Version...

:: Install backend dependencies
cd backend
echo Installing backend dependencies...
pip install -r requirements.txt
start "Stock Dashboard Backend" /B cmd /c "uvicorn main:app --host 0.0.0.0 --port 8000"

:: Wait for backend to start
timeout /t 5

:: Start frontend
cd ../frontend
echo Starting frontend...
npm run dev

pause
