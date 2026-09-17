#!/bin/bash
echo "============================================================"
echo "  KhananRakshak: Smart Governance Platform for Coal Mines"
echo "============================================================"
echo ""

if ! command -v python3 &> /dev/null
then
    echo "[ERROR] python3 could not be found! Please install Python 3.10+."
    exit 1
fi

echo "[1/2] Installing required dependencies..."
python3 -m pip install -r requirements.txt

echo "[2/2] Launching KhananRakshak Server on http://127.0.0.1:8000..."
python3 run.py
