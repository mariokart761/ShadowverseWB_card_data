#!/bin/bash

echo "================================="
echo "Shadowverse 多語言卡牌資料爬蟲"
echo "================================="
echo

# 檢查 Python 是否安裝
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "錯誤：未找到 Python，請先安裝 Python 3.7 或更高版本"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

echo "使用 Python: $PYTHON_CMD"

# 檢查 requests 套件
$PYTHON_CMD -c "import requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "正在安裝必要套件..."
    $PYTHON_CMD -m pip install requests
    if [ $? -ne 0 ]; then
        echo "錯誤：無法安裝 requests 套件"
        exit 1
    fi
fi

# 執行主程式
$PYTHON_CMD run.py

echo
echo "程式執行完畢"