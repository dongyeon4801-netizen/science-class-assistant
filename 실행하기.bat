@echo off
chcp 65001 >nul
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo [오류] 파이썬이 설치되어 있지 않습니다.
    echo https://www.python.org/downloads/ 에서 설치하고, 설치 화면에서 "Add python.exe to PATH"를 꼭 체크하세요.
    pause
    exit /b
)

if not exist ".venv\Scripts\python.exe" (
    echo 처음 실행: 필요한 프로그램을 설치합니다. 몇 분 걸릴 수 있어요...
    python -m venv .venv
)

.venv\Scripts\python.exe -m pip install -q -r requirements.txt

echo 과학 수업 설계 비서를 시작합니다. 이 창을 닫으면 프로그램이 종료됩니다.
start "" cmd /c "timeout /t 4 >nul & start http://localhost:8501"
.venv\Scripts\python.exe -m streamlit run app.py
pause
