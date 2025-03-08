@echo on

REM Ako se nesto menja u starom programu osim tabela krstenja i vencanja, 
REM potrebno je pokrenuti ovu skriptu na crkvenom laptopu da bi se update-ovala cela baza
REM Ova skripta ce pokrenuti WSL i skriptu './build.sh --db', koja ce migrirati sve tabele iz stare aplikacije u novu

REM Restart WSL and rebuild whole database 
wsl --shutdown
wsl -e bash -c "source /home/sasa/.python_venv/bin/activate &&  cd /home/sasa/crkva && ./build.sh --db"

