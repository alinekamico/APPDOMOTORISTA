"use client";

import Link from "next/link";
import { useRequireRole } from "@/lib/roles";
import { useFetch } from "@/lib/use-fetch";
import { COLUNAS } from "@/components/kanban/types";
import type { RomaneioResumo } from "@/components/kanban/types";

const LABEL_STATUS: Record<string, string> = Object.fromEntries(COLUNAS.map((c) => [c.status, c.titulo]));

export default function MinhaRotaPage() {
  const { carregando: carregandoAuth } = useRequireRole(["motorista"]);
  const { data: romaneios, carregando, erro } = useFetch<RomaneioResumo[]>(
    carregandoAuth ? null : "/romaneios/minha-rota"
  );

  if (carregandoAuth) return null;

  return (
    <div className="mx-auto max-w-md">
      <h1 className="mb-4 text-lg font-semibold text-kami-charcoal">Minha rota</h1>

      {carregando && <p className="text-sm text-kami-charcoal-light">Carregando...</p>}
      {erro && <p className="text-sm text-kami-red">{erro}</p>}

      <div className="flex flex-col gap-3">
        {romaneios?.map((r) => (
          <Link
            key={r.id}
            href={`/romaneio/${r.id}`}
            className="rounded-xl border border-black/10 bg-white p-4 shadow-sm transition hover:border-kami-red/40"
          >
            <div className="flex items-center justify-between">
              <span className="font-semibold text-kami-charcoal">{r.codigo}</span>
              <span className="rounded-full bg-kami-red/10 px-2 py-0.5 text-xs font-medium text-kami-red">
                {LABEL_STATUS[r.status] ?? r.status}
              </span>
            </div>
            <p className="mt-1 text-sm text-kami-charcoal-light">
              {r.qtd_pedidos ?? 0} pedidos · {r.veiculo_placa ?? "sem veículo"}
            </p>
          </Link>
        ))}

        {romaneios?.length === 0 && (
          <p className="text-sm text-kami-charcoal-light">Nenhum romaneio atribuído a você no momento.</p>
        )}
      </div>
    </div>
  );
}
