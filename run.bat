@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Creating Python environment...
  py -3.14 -m venv .venv 2>nul || py -3 -m venv .venv
)
call ".venv\Scripts\activate.bat"
python -m pip install -r requirements.txt
start "" http://127.0.0.1:8000
python -m uvicorn app:app --host 127.0.0.1 --port 8000
endlocal
