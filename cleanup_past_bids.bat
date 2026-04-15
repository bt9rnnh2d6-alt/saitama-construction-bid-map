@echo off
chcp 65001 > nul
title Cleanup Past Bids

echo ============================================================
echo  Cleanup Past Bids (Delete bids whose bid_date has passed)
echo ============================================================
echo.

python -m pip install requests python-dotenv --quiet 2>nul
python cleanup_past_bids.py

echo.
pause
