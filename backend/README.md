# Backend — KAMI CO. Romaneios

FastAPI + SQLAlchemy + Alembic + MySQL. Stack conforme a governança de TI da KAMI (Python + FastAPI, RDS MySQL em produção).

## Rodando localmente

```bash
# 1. Suba o MySQL local
docker compose up -d mysql   # (rodar na raiz do projeto, onde está o docker-compose.yml)

# 2. Ambiente Python
pip install -r requirements.txt
copy .env.example .env       # ajuste os valores conforme necessário

# 3. Migrations
python -m alembic upgrade head

# 4. Dados iniciais (sem isso ninguém consegue logar / escolher motivo de ocorrência)
python scripts/seed_admin.py --nome "Seu Nome" --email voce@kamico.com.br --senha "TrocarDepois123!"
python scripts/seed_tipos_ocorrencia.py

# 5. Rodar a API
uvicorn app.main:app --reload
```

API em `http://localhost:8000`, docs interativas em `http://localhost:8000/docs`.

## Estrutura

```
app/
  core/            config (env vars via Pydantic Settings), security (bcrypt + JWT), dependencies (auth/papel/tenant)
  db/              engine/session (SQLAlchemy)
  models/          ORM — um arquivo por entidade (ver modelo de dados no plano)
  schemas/         Pydantic (request/response)
  repositories/    tenant_scope.py — único ponto que aplica o filtro multi-tenant
  services/        regras de negócio (auth, cadastro, romaneio, pod, resequenciamento, auditoria, ocorrencia)
  routers/         endpoints HTTP — finos, delegam tudo pros services
  integrations/    adapters isolados (tms/, uno/, nps/, maps/) — ver seção abaixo
  middleware/       (reservado — isolamento de tenant hoje é feito via repository, não middleware HTTP)
  tests/           pytest — hoje cobre o heurístico de resequenciamento
alembic/           migrations
scripts/           seed_admin.py, seed_tipos_ocorrencia.py
```

## Autenticação e papéis

3 papéis: `kami_admin` (vê tudo), `transportadora_admin` (escopado à própria `transportadora_id`),
`motorista` (escopado aos próprios romaneios alocados). JWT com expiração configurável
(`JWT_EXPIRE_MINUTES`), senha com bcrypt, "esqueci senha" com token de uso único expirando em
`PASSWORD_RESET_EXPIRE_MINUTES` (30 min por padrão), enviado por e-mail via SMTP Gmail.

**Isolamento multi-tenant**: toda query de listagem passa por
`app/repositories/tenant_scope.py::escopar_por_transportadora` — nunca filtrar por
`transportadora_id` manualmente em um router, para não esquecer em algum endpoint novo.

## Integrações (adapters)

Nenhum service importa SDK de terceiro diretamente — sempre via `Protocol` em
`integrations/<nome>/interface.py`, com a implementação concreta escolhida por env var:

| Integração | Status | Env var | Observação |
|---|---|---|---|
| TMS (entrada, futuro) | stub (`StubTmsPayloadTranslator`) | — | Endpoint real: `POST /webhooks/tms/romaneios` (header `X-Tms-Token`). Só passa a ser usado quando o TMS de verdade existir. |
| Fonte de romaneio (hoje) | `manual` ou `uno_replica` | `INTEGRATION_ADAPTER_ROMANEIO_SOURCE` | Ver seção própria abaixo — substitui o TMS enquanto ele não existe. |
| Maps (distância/tempo) | `fake` (haversine) ou `google` | `INTEGRATION_ADAPTER_MAPS` | Trocar pra `google` exige `GOOGLE_MAPS_API_KEY`. Navegação turn-by-turn é sempre deep link (Waze/Google Maps), nunca embutida. |
| UNO (evidências, saída) | stub (só loga) | — | Sem API/documentação do UNO ainda (Regra 5). `eventos_entrega.uno_sync_status` permite reprocessar depois. |
| NPS (pós-entrega) | stub (só loga) | — | Recomendação: contratar provedor de CX (WhatsApp/SMS) em vez de construir internamente — ver pesquisa de mercado no plano. |

### Fonte de romaneio: réplica do UNO no Supabase

Enquanto o TMS não existe, o app precisa de algum jeito de saber quais romaneios existem.
Não há acesso direto ao UNO (ERP) — em vez disso, há uma **réplica somente-leitura do banco
do UNO hospedada no Supabase (Postgres)**. É *só o banco*, não uma API — a conexão é direta
via connection string do Postgres.

- **Código**: `app/integrations/uno_source/` (interface + `manual_adapter.py` + `supabase_adapter.py`).
- **Como funciona**: `POST /romaneios/importar-uno` (botão "Buscar romaneios do UNO" no
  frontend, só `kami_admin`) busca os romaneios pendentes na fonte configurada e cria os que
  ainda não existem — casando a transportadora pelo **CNPJ**. Duplicados (já importados) e
  CNPJ não cadastrado são reportados sem derrubar o restante do lote.
- **Configurar**: coloque a connection string do Postgres do Supabase em
  `UNO_REPLICA_DATABASE_URL` e mude `INTEGRATION_ADAPTER_ROMANEIO_SOURCE=uno_replica` no `.env`.
- **Antes de mexer na query**: os nomes de tabela/coluna em `supabase_adapter.py` são
  **placeholder** — ninguém validou contra o schema real ainda. Rode primeiro:
  ```bash
  python scripts/inspect_uno_replica.py "postgresql://usuario:senha@host:5432/postgres"
  ```
  Isso lista as tabelas/colunas reais e uma amostra de linhas — ajuste as constantes no topo
  de `supabase_adapter.py` (`TABELA_ROMANEIO`, `TABELA_PEDIDO`, `QUERY_ROMANEIOS`, `QUERY_PEDIDOS`)
  pra bater com o schema de verdade antes de usar em qualquer teste real.
- **RDS continua sendo o banco da aplicação** — a réplica do UNO é só uma fonte de leitura
  externa; nada relacionado a usuários, romaneios, POD etc. é armazenado nela.

## Checklist de segurança para revisão da TI

- [x] Sem segredo hardcoded — tudo via `.env` / variável de ambiente (`app/core/config.py`)
- [x] Senha com hash bcrypt (`passlib`), nunca armazenada em texto plano
- [x] Login via JWT com expiração configurável
- [x] Sem SQL cru — todo acesso a banco via SQLAlchemy ORM (parametrizado por construção)
- [x] Log de auditoria (`log_auditoria`) em login, login falho, CRUDs administrativos e transições de romaneio
- [x] Isolamento multi-tenant centralizado (não depende de cada endpoint lembrar de filtrar)
- [ ] **Pendente da TI**: gerar `JWT_SECRET` e `TMS_WEBHOOK_TOKEN` definitivos antes de produção (os do `.env.example` são só placeholders de desenvolvimento)
- [ ] **Pendente da TI**: trocar armazenamento de uploads (hoje disco local em `UPLOAD_DIR`) por S3 antes de rodar em múltiplas instâncias EC2
- [ ] **Pendente da TI**: HTTPS/TLS (configurado na infra, fora do escopo do código)
- [x] **Nginx**: `client_max_body_size 20M;` no `server{}` do domínio — sem isso, upload de foto/assinatura da entrega (POST multipart) é rejeitado com "Request Entity Too Large" (padrão do nginx é só 1MB). Necessário sempre que o servidor/nginx for reconfigurado do zero.
