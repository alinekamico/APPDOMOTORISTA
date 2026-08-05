"use client";

import { useFetch } from "@/lib/use-fetch";
import { COLUNAS } from "@/components/kanban/types";

export type HistoricoEvento = {
  tipo: "etapa" | "entrega" | "nao_entregue" | "resequenciamento";
  criado_em: string;
  usuario_nome: string | null;
  papel_usuario: string | null;
  etapa_anterior: string | null;
  etapa_nova: string | null;
  observacao: string | null;
  pedido_id: number | null;
  pedido_cliente_nome: string | null;
  pedido_sequencia: number | null;
  tipo_ocorrencia_descricao: string | null;
  resequenciamento_origem: string | null;
  resequenciamento_qtd_paradas: number | null;
};

const LABEL_STATUS: Record<string, string> = Object.fromEntries(COLUNAS.map((c) => [c.status, c.titulo]));

const LABEL_ORIGEM_RESEQUENCIAMENTO: Record<string, string> = {
  divergencia_manual: "entrega fora da sequência prevista",
  ajuste_espontaneo: "recálculo manual do motorista",
  insercao_pedido: "novo pedido inserido na rota",
};

const LABEL_PAPEL: Record<string, string> = {
  kami_admin: "KAMI",
  transportadora_admin: "Transportadora",
  motorista: "Motorista",
  sistema: "Sistema",
};

function descreverEvento(e: HistoricoEvento): string {
  switch (e.tipo) {
    case "etapa":
      return e.etapa_anterior
        ? `Etapa alterada de "${LABEL_STATUS[e.etapa_anterior] ?? e.etapa_anterior}" para "${LABEL_STATUS[e.etapa_nova ?? ""] ?? e.etapa_nova}"`
        : `Romaneio criado — etapa "${LABEL_STATUS[e.etapa_nova ?? ""] ?? e.etapa_nova}"`;
    case "entrega":
      return `Pedido ${e.pedido_sequencia ?? ""}. ${e.pedido_cliente_nome} — entregue`;
    case "nao_entregue":
      return `Pedido ${e.pedido_sequencia ?? ""}. ${e.pedido_cliente_nome} — não entregue${
        e.tipo_ocorrencia_descricao ? ` (${e.tipo_ocorrencia_descricao})` : ""
      }`;
    case "resequenciamento": {
      const motivo = e.resequenciamento_origem
        ? (LABEL_ORIGEM_RESEQUENCIAMENTO[e.resequenciamento_origem] ?? e.resequenciamento_origem)
        : "";
      return `Rota recalculada (${motivo})${
        e.resequenciamento_qtd_paradas ? ` — ${e.resequenciamento_qtd_paradas} parada(s) reordenada(s)` : ""
      }`;
    }
    default:
      return e.tipo;
  }
}

export function HistoricoTimeline({ romaneioId }: { romaneioId: number }) {
  const { data: eventos, carregando, erro } = useFetch<HistoricoEvento[]>(`/romaneios/${romaneioId}/historico`);

  if (carregando) return <p className="text-sm text-kami-charcoal-light">Carregando histórico...</p>;
  if (erro) return <p className="text-sm text-kami-red">{erro}</p>;
  if (!eventos || eventos.length === 0) {
    return <p className="text-sm text-kami-charcoal-light">Nenhum evento registrado ainda.</p>;
  }

  return (
    <ul className="flex flex-col gap-3">
      {eventos
        .slice()
        .reverse()
        .map((e, idx) => (
          <li key={idx} className="border-l-2 border-kami-red/30 pl-3">
            <p className="text-sm text-kami-charcoal">{descreverEvento(e)}</p>
            <p className="text-xs text-kami-charcoal-light">
              {new Date(e.criado_em).toLocaleString("pt-BR")}
              {e.usuario_nome && ` · ${e.usuario_nome}`}
              {!e.usuario_nome && e.papel_usuario && ` · ${LABEL_PAPEL[e.papel_usuario] ?? e.papel_usuario}`}
            </p>
            {e.observacao && <p className="mt-0.5 text-xs italic text-kami-charcoal-light">&ldquo;{e.observacao}&rdquo;</p>}
          </li>
        ))}
    </ul>
  );
}
