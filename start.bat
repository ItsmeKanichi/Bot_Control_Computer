@echo off
:: Thiet lap code page sang UTF-8 va bien moi truong Python
chcp 65001 >nul
set PYTHONIOENCODING=utf-8

title Bot Control Computer Launcher

echo ====================================================
echo          Bot Control Computer - Khoi dong
echo ====================================================
echo.

:: Kiem tra xem Python da duoc cai dat chua
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Khong tim thay Python tren he thong cua ban!
    echo.
    echo Vui long tai va cai dat Python ^(phien ban 3.10 tro len^) tai:
    echo --^> https://www.python.org/downloads/
    echo.
    echo QUAN TRONG: Nho tich chon vao o "Add Python to PATH" khi cai dat.
    echo.
    pause
    exit /b 1
)

:: Chay file run.py bang Python
python "%~dp0run.py"

if %errorlevel% neq 0 (
    echo.
    echo [INFO] Chuong trinh da dung hoac co loi xay ra.
    pause
)
