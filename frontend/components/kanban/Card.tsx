"use client";

import Link from "next/link";
import type { RomaneioResumo } from "./types";

export function Card({ romaneio }: { romaneio: RomaneioResumo }) {
  return (
    <Link
      href={`/romaneios/${romaneio.id}`}
      className="block rounded-lg border border-black/10 bg-white p-3 shadow-sm transition hover:border-kami-red/40 hover:shadow-md"
    >
      <div className="mb-1 flex items-center justify-between">
        <span className="text-sm font-semibold text-kami-charcoal">{romaneio.codigo}</span>
        {romaneio.qtd_pedidos !== null && (
          <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs text-kami-charcoal-light">
            {romaneio.qtd_pedidos} pedido{romaneio.qtd_pedidos === 1 ? "" : "s"}
          </span>
        )}
      </div>
      {romaneio.empresa_nome && (
        <p className="mb-1 inline-flex items-center gap-1 rounded-full bg-kami-charcoal/5 px-2 py-0.5 text-xs font-medium text-kami-charcoal">
          {romaneio.empresa_nome}
          {romaneio.empresa_uf && <span className="text-kami-charcoal-light">· {romaneio.empresa_uf}</span>}
        </p>
      )}
      <p className="text-xs text-kami-charcoal-light">
        {romaneio.transportadora_nome ??
          (romaneio.transportadora_cnpj_externo
            ? `CNPJ ${romaneio.transportadora_cnpj_externo} não cadastrado`
            : "Aguardando definição")}
      </p>
      {(romaneio.motorista_nome || romaneio.veiculo_placa) && (
        <p className="mt-1 text-xs text-kami-charcoal-light">
          {romaneio.motorista_nome ?? "—"} · {romaneio.veiculo_placa ?? "—"}
        </p>
      )}
      {romaneio.qtd_caixas !== null && (
        <p className="mt-1 text-xs text-kami-charcoal-light">{romaneio.qtd_caixas} caixas</p>
      )}
      {romaneio.tipo_veiculo_sugerido && (
        <p className="mt-1 text-xs text-kami-charcoal-light">Veículo: {romaneio.tipo_veiculo_sugerido}</p>
      )}
      {romaneio.data_saida_prevista && (
        <p className="mt-1 text-xs text-kami-charcoal-light">
          Saída prevista: {new Date(romaneio.data_saida_prevista).toLocaleDateString("pt-BR")}
        </p>
      )}
    </Link>
  );
}
