@echo off
title Bitget Algo Trading Bot - 24/7 Runner
echo Starting Bot Supervisor...
echo This window must stay open for the bot to run.
echo.
cd /d "%~dp0"
python run_bot.py
pause
