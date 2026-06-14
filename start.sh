#!/usr/bin/env bash
# Покреће SPC Регистар локално преко Docker-а (Linux/macOS).
# Windows: покрените start.bat.
set -e
docker compose --profile standalone up -d --build
echo
echo "SPC Регистар ради на: http://localhost:8000"
echo "Прва пријава: admin / admin"
echo "Заустављање: docker compose --profile standalone down"
