@echo off
REM Encerra o backend e o frontend da demonstracao (libera as portas 8000 e 3000).

echo Encerrando backend (porta 8000) e frontend (porta 3000)...

for /f "tokens=5" %%p in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do taskkill /F /PID %%p >nul 2>&1
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING') do taskkill /F /PID %%p >nul 2>&1

echo Pronto.
pause
