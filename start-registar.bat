@echo on

REM izvrsava se na crkvenom laptopu da bi se startovala aplikacija
REM ova skripta ce pokrenuti WSL i skriptu './start.sh', koja ce migrirati tabelu krstenja i vencanja i pokrenuti aplikaciju
REM kojoj se pristupa preko http://localhost:8000
REM tako da sve jednim klikom bude spremno za stampu

REM Start WSL, navigate to the directory, run start.sh, wait for 15 seconds, and open the browser
wsl --shutdown

REM wsl -e bash -c "source /home/sasa/.python_venv/bin/activate &&  cd /home/sasa/crkva && ./start.sh  && sleep 15 && powershell.exe -c start 'http://localhost:8000'"
powershell.exe -c start 'http://localhost:8000'

REM "Osvezi tab 'http://localhost:8000' u browser-u za 15 sekundi..."
wsl -e bash -c "source /home/sasa/.python_venv/bin/activate &&  cd /home/sasa/crkva && ./start.sh"
REM wsl --list --running
