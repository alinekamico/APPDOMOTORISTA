@echo off
REM Sobe o backend e o frontend automaticamente para demonstracao.
REM Nao precisa de Docker - usa um banco SQLite local (arquivo backend\dev_demo.db).
REM Duplo-clique neste arquivo sempre que quiser (re)ligar o sistema.

cd /d "%~dp0backend"

if not exist ".env" (
    echo DATABASE_URL=sqlite:///./dev_demo.db> .env
    echo JWT_SECRET=dev-demo-secret-not-for-prod>> .env
    echo JWT_ALGORITHM=HS256>> .env
    echo JWT_EXPIRE_MINUTES=480>> .env
    echo PASSWORD_RESET_EXPIRE_MINUTES=30>> .env
    echo APP_BASE_URL=http://localhost:3000>> .env
    echo SMTP_HOST=smtp.gmail.com>> .env
    echo SMTP_PORT=587>> .env
    echo SMTP_USER=>> .env
    echo SMTP_PASSWORD=>> .env
    echo SMTP_FROM_NAME=KAMI CO. Romaneios>> .env
    echo GOOGLE_MAPS_API_KEY=>> .env
    echo TMS_WEBHOOK_TOKEN=dev-demo-token>> .env
    echo INTEGRATION_ADAPTER_MAPS=fake>> .env
    echo INTEGRATION_ADAPTER_UNO=stub>> .env
    echo INTEGRATION_ADAPTER_NPS=stub>> .env
    echo UPLOAD_DIR=./uploads>> .env
)

start "KAMI Backend" cmd /k "python -m alembic upgrade head && python scripts\seed_admin.py --nome Aline --email aline@kamico.com.br --senha TrocarDepois123! && python scripts\seed_tipos_ocorrencia.py && echo. && echo Backend no ar em http://localhost:8000 && uvicorn app.main:app --host 0.0.0.0 --port 8000"

cd /d "%~dp0frontend"
set NEXT_PUBLIC_API_URL=http://localhost:8000
start "KAMI Frontend" cmd /k "npm run dev"

echo.
echo Aguardando os servidores subirem...
timeout /t 8 /nobreak >nul

start http://localhost:3000

echo.
echo ============================================
echo  Sistema disponivel em: http://localhost:3000
echo  Login:  aline@kamico.com.br
echo  Senha:  TrocarDepois123!
echo ============================================
echo.
echo Deixe as duas janelas (Backend/Frontend) abertas enquanto usar o sistema.
pause
