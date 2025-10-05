@echo off
chcp 65001 >nul
echo ========================================
echo   Business Database - Деплой обновлений
echo ========================================
echo.

REM Переход в директорию проекта
cd /d C:\soft\business.db
if %ERRORLEVEL% NEQ 0 (
    echo [ОШИБКА] Не удалось перейти в C:\soft\business.db
    pause
    exit /b 1
)

echo [1/4] Проверка Git...
git --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ОШИБКА] Git не установлен!
    echo Установите Git: winget install --id Git.Git -e
    pause
    exit /b 1
)

echo [2/4] Обновление кода из GitHub...
git branch --set-upstream-to=origin/master master >nul 2>&1
git pull origin master
if %ERRORLEVEL% NEQ 0 (
    echo [ОШИБКА] Не удалось обновить код из GitHub
    pause
    exit /b 1
)

echo.
echo [3/4] Перезапуск Flask сервиса...
C:\nssm\win64\nssm.exe restart FlaskBusinessDB
if %ERRORLEVEL% NEQ 0 (
    echo [ОШИБКА] Не удалось перезапустить сервис
    pause
    exit /b 1
)

echo.
echo [4/4] Проверка статуса сервиса...
timeout /t 2 /nobreak >nul
C:\nssm\win64\nssm.exe status FlaskBusinessDB

echo.
echo ========================================
echo   Деплой завершен!
echo ========================================
echo.
echo Откройте https://businessdb.ru/ для проверки
echo.
pause
