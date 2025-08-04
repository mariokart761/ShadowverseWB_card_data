@echo off
chcp 65001 >nul
echo =================================
echo Shadowverse 多語言卡牌資料爬蟲
echo =================================
echo.

REM 檢查 Python 是否安裝
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 錯誤：未找到 Python，請先安裝 Python 3.7 或更高版本
    pause
    exit /b 1
)

REM 檢查 requests 套件
python -c "import requests" >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在安裝必要套件...
    python -m pip install requests
    if %errorlevel% neq 0 (
        echo 錯誤：無法安裝 requests 套件
        pause
        exit /b 1
    )
)

REM 執行主程式
python run.py

echo.
echo 程式執行完畢
pause