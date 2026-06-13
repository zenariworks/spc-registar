@echo off
chcp 65001 >/dev/null
REM Покреће SPC Регистар локално преко Docker Desktop-а (Windows, WSL2).
docker compose -f docker-compose.yml -f docker-compose.standalone.yml up -d --build
if errorlevel 1 goto err
echo.
echo SPC Регистар ради на: http://localhost:8000
echo Прва пријава: admin / admin
echo Заустављање: docker compose -f docker-compose.yml -f docker-compose.standalone.yml down
goto end
:err
echo.
echo Грешка при покретању. Да ли је Docker Desktop покренут?
:end
pause
