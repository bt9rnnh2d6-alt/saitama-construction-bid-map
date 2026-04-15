@echo off
chcp 65001 > nul
title Push to Supabase

echo ============================================================
echo  Push bids.js to Supabase
echo ============================================================
echo.

python -m pip install requests python-dotenv --quiet 2>nul
python push_to_supabase.py

echo.
pause
