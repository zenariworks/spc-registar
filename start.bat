@echo off
chcp 65001 >/dev/null
REM Покреће SPC Регистар локално преко Docker Desktop-а (Windows, WSL2).
docker compose --profile standalone up -d --build
if errorlevel 1 goto err
echo.
echo SPC Регистар ради на: http://localhost:8000
echo Прва пријава: admin / admin
echo Заустављање: docker compose --profile standalone down
goto end
:err
echo.
echo Грешка при покретању. Да ли је Docker Desktop покренут?
:end
pause
