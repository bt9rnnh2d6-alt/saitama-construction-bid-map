@echo off
chcp 65001 > nul
title Cleanup Supabase Coords

echo ============================================================
echo  Supabase Cleanup: Remove Out-of-Saitama Coordinates
echo ============================================================
echo.

python -m pip install requests python-dotenv --quiet 2>nul
python cleanup_supabase_coords.py

echo.
pause
