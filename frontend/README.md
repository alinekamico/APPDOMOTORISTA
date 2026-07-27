# Frontend — KAMI CO. Romaneios

Next.js 16 (App Router) + Tailwind, PWA (instalável no celular do motorista). Stack conforme a governança de TI da KAMI (React + Next.js + Tailwind, web responsivo).

## Rodando localmente

```bash
npm install
npm run dev
```

Abre em [http://localhost:3000](http://localhost:3000). Precisa do backend rodando em `http://localhost:8000` (ver `backend/README.md`) — configurável via `NEXT_PUBLIC_API_URL`.

Copie `.env.example` para `.env.local` e preencha `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` para habilitar o mapa embutido da rota (opcional — sem a chave, o app funciona normalmente, só o mapa embutido fica com uma mensagem de placeholder; os deep links de navegação continuam funcionando sempre).

## Estrutura

```
app/
  (auth)/          login, esqueci-senha, redefinir-senha — layout próprio, sem navegação
  (dashboard)/      romaneios, transportadoras, veiculos, motoristas, ocorrencias, minha-rota
                     — todas as telas de KAMI/transportadora, com AppShell (nav) comum
  romaneio/[id]/    fluxo mobile de execução do motorista (carregamento, entrega, ocorrência)
                     — layout minimalista, sem a navegação do dashboard
components/
  kanban/           Board, Column, Card do quadro de romaneios
  entrega/          CameraCapture (input com capture=environment), AssinaturaCanvas
  mapa/             MapaRota — mapa embutido (Google Maps JS API via @vis.gl/react-google-maps),
                     mostra paradas pendentes/entregues e a posição atual do motorista. Convive
                     com os deep links de navegação (Waze/Google Maps), não os substitui.
lib/
  api-client.ts     fetch wrapper com JWT (localStorage) e tratamento de erro
  auth-context.tsx  estado de sessão (usuário logado, login/logout)
  roles.ts          guarda de rota client-side (a autorização real é sempre no backend)
hooks/
  useGeolocation.ts captura de posição do motorista (Regras 1/4)
public/
  sw.js, manifest    PWA — cache básico de assets estáticos, nunca cacheia chamadas de API
```

## Papéis e rotas

Não há route groups por papel — uma mesma URL (ex. `/romaneios`) serve tanto `kami_admin`
quanto `transportadora_admin`; o backend já filtra os dados por tenant, e o componente ajusta
o que mostra/permite com base em `useAuth().usuario.papel`. Isso evita colisão de rotas do
Next.js (dois `page.tsx` resolvendo pro mesmo path) e evita duplicar telas quase idênticas.

## Câmera, assinatura e geolocalização

Tudo via APIs padrão do navegador (sem SDK nativo):
- Foto: `<input type="file" accept="image/*" capture="environment">` — abre a câmera nativa do celular.
- Assinatura: `<canvas>` com Pointer Events, exportado como PNG (`components/entrega/AssinaturaCanvas.tsx`).
- Localização: `navigator.geolocation.getCurrentPosition` (`hooks/useGeolocation.ts`).

## Mapa embutido vs. deep link (Regra 4)

Duas coisas coexistem na tela de execução do motorista (`/romaneio/[id]`), por decisão explícita:
- **Mapa embutido** (`components/mapa/MapaRota.tsx`): visão geral da rota — paradas numeradas
  (vermelho = pendente, verde = entregue), posição atual do motorista, linha ligando os pontos
  na ordem vigente. Só aparece com `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` configurada e paradas com
  coordenadas (`cliente_lat`/`cliente_lng`).
- **Deep link** (`waze.com/ul` / `google.com/maps/dir`): abre o app nativo de navegação
  turn-by-turn pra próxima parada — é o que o motorista realmente usa pra dirigir.

O mapa embutido é só visão geral/contexto; a navegação de verdade sempre sai pro app nativo.

## Pendências conhecidas para produção

- Trocar o ícone placeholder (`public/icons/*.png`, gerado programaticamente) pelo logo oficial da KAMI CO. quando disponível em alta resolução.
- `NEXT_PUBLIC_API_URL` precisa apontar para a URL real da API (EC2) em produção.
- `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY`: restringir por domínio/referrer no Google Cloud Console antes de produção (é uma chave client-side, visível no bundle — a restrição por domínio é o que a protege de uso indevido, não o sigilo do valor).
- Romaneios criados manualmente sem latitude/longitude não aparecem no mapa embutido nem participam do resequenciamento automático (Regras 1/4/7) — em produção, o TMS real deve enviar coordenadas já geocodificadas.
