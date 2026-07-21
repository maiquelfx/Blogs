@echo off
cd /d "%~dp0"

python image_uploader.py
if errorlevel 1 (
    py image_uploader.py
)

echo.
echo (janela fechada pelo programa ou Ctrl+C para sair)
pause
