@echo off
chcp 65001 >nul
title AI Image Generator

echo ============================================
echo   AI Image Generator - Nano Banana
echo ============================================
echo.

cd /d "%~dp0"

echo [1/2] 启动 Deno 服务器...
echo.
start "Deno Server" cmd /k "deno run --allow-read --allow-net --allow-env -A main.ts"

timeout /t 2 /nobreak >nul

echo [2/2] 打开浏览器...
start http://localhost:8000

echo.
echo ============================================
echo   服务器已启动！
echo   访问地址: http://localhost:8000
echo ============================================
echo.
echo 按任意键退出...
pause >nul
