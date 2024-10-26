@echo on

REM ova skripta pokrenuti WSL i skriptu 'start.sh', koja ce migrirati tabelu krstena i vencanja i pokrenuti aplikaciju
REM kojoj se pristupa preko http://localhost:8000
REM tako da sve jednim klikom bude spremno za stampu

REM Start WSL, navigate to the directory, run start.sh, wait for 15 seconds, and open the browser
wsl --shutdown
wsl -e bash -c "source /home/sasa/.python_venv/bin/activate &&  cd /home/sasa/crkva && ./start.sh > start_log.txt && sleep 15 && powershell.exe -c start 'http://localhost:8000'"
wsl --list --running
