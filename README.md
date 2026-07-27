# APP Motorista — KAMI CO.

Sistema de gestão de romaneios e entregas: a KAMI CO. (distribuidora) atribui romaneios a
transportadoras terceirizadas, que alocam veículo e motorista; o motorista executa a rota,
registra prova de entrega (foto, assinatura, geolocalização) e reporta ocorrências — tudo
navegando como um kanban, com auditoria completa de cada etapa.

Construído seguindo a **governança de TI da KAMI** (`Governanca_TI_KAMI_CO.pptx`): stack
obrigatória (React/Next.js/Tailwind + Python/FastAPI + MySQL), autenticação com bcrypt/JWT,
papéis de acesso, log de auditoria. Este repositório é o código pronto para a TI revisar e
subir em EC2/RDS — não inclui deploy.

## Stack

- **Frontend**: `frontend/` — Next.js 16 (App Router) + Tailwind, PWA
- **Backend**: `backend/` — FastAPI + SQLAlchemy + Alembic + MySQL
- **Banco local de desenvolvimento**: `docker-compose.yml` (MySQL 8.4)

## Quick start (desenvolvimento)

```bash
docker compose up -d mysql

cd backend
pip install -r requirements.txt
copy .env.example .env
python -m alembic upgrade head
python scripts/seed_admin.py --nome "Seu Nome" --email voce@kamico.com.br --senha "TrocarDepois123!"
python scripts/seed_tipos_ocorrencia.py
uvicorn app.main:app --reload

# em outro terminal
cd frontend
npm install
npm run dev
```

Acesse `http://localhost:3000` e entre com o e-mail/senha do `seed_admin.py`. Detalhes em
[`backend/README.md`](backend/README.md) e [`frontend/README.md`](frontend/README.md).

## Papéis

| Papel | Escopo | O que faz |
|---|---|---|
| `kami_admin` | Todas as transportadoras | Cadastra transportadoras, confere no portão (conferência logística), gerencia catálogo de ocorrências, cria romaneios de teste (stub do TMS) |
| `transportadora_admin` | Só a própria transportadora | Cadastra veículos e motoristas, aloca veículo+motorista nos romaneios recebidos |
| `motorista` | Só os romaneios alocados a ele | Executa a rota: carregamento, entrega (POD), ocorrências |

## Fluxo do romaneio (kanban)

`definicao_transporte` (transportadora aloca veículo/motorista) → `conferencia_logistica`
(KAMI confere no portão) → `carregamento` (motorista evidencia com foto) → `inicio_rota` →
`em_transito` (motorista entrega pedido a pedido) → `concluido` (automático, quando 100% dos
pedidos estão finalizados). Estados de exceção: `romaneio_incompleto` e
`romaneio_com_problema`, acionados pelo motorista quando não é possível continuar.

Detalhes de modelo de dados, regras de negócio (resequenciamento, desvio de sequência,
inserção de pedido em romaneio em andamento) e arquitetura de integrações estão documentados
inline no código (`backend/app/services/`, `backend/app/integrations/`) e no plano original
da implementação.

## O que falta para produção

Ver checklist de segurança em [`backend/README.md`](backend/README.md#checklist-de-segurança-para-revisão-da-ti).
Resumo: gerar segredos definitivos (`JWT_SECRET`, `TMS_WEBHOOK_TOKEN`), trocar upload de
arquivos locais por S3, e as integrações reais de TMS/UNO/NPS (hoje stubadas — ver tabela em
`backend/README.md`).
