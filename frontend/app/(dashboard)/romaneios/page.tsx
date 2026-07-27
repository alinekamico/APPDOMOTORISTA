"use client";

import { useState } from "react";
import Link from "next/link";
import { useRequireRole } from "@/lib/roles";
import { useFetch } from "@/lib/use-fetch";
import { apiFetch, ApiError } from "@/lib/api-client";
import { Board } from "@/components/kanban/Board";
import type { RomaneioResumo } from "@/components/kanban/types";

type ResultadoImportacao = {
  importados: string[];
  ignorados: { codigo: string; motivo: string }[];
};

export default function RomaneiosPage() {
  const { usuario, carregando: carregandoAuth } = useRequireRole(["kami_admin", "transportadora_admin"]);
  const { data: romaneios, carregando, erro, recarregar } = useFetch<RomaneioResumo[]>(
    carregandoAuth ? null : "/romaneios"
  );

  const [importando, setImportando] = useState(false);
  const [resultadoImportacao, setResultadoImportacao] = useState<ResultadoImportacao | null>(null);
  const [erroImportacao, setErroImportacao] = useState<string | null>(null);

  async function handleBuscarUno() {
    setErroImportacao(null);
    setResultadoImportacao(null);
    setImportando(true);
    try {
      const resultado = await apiFetch<ResultadoImportacao>("/romaneios/importar-uno", { method: "POST" });
      setResultadoImportacao(resultado);
      recarregar();
    } catch (err) {
      setErroImportacao(err instanceof ApiError ? err.detail : "Não foi possível buscar romaneios do UNO.");
    } finally {
      setImportando(false);
    }
  }

  if (carregandoAuth) return null;

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-lg font-semibold text-kami-charcoal">Romaneios</h1>
        {usuario?.papel === "kami_admin" && (
          <div className="flex gap-2">
            <button
              onClick={handleBuscarUno}
              disabled={importando}
              className="rounded-lg border border-kami-red/40 px-3 py-1.5 text-sm font-medium text-kami-red hover:bg-kami-red/5 disabled:opacity-60"
            >
              {importando ? "Buscando..." : "Buscar romaneios do UNO"}
            </button>
            <Link
              href="/romaneios/novo"
              className="rounded-lg bg-kami-red px-3 py-1.5 text-sm font-medium text-white hover:bg-kami-red-dark"
            >
              Novo romaneio (simulação)
            </Link>
          </div>
        )}
      </div>

      {erroImportacao && <p className="mb-3 text-sm text-kami-red">{erroImportacao}</p>}
      {resultadoImportacao && (
        <div className="mb-4 rounded-lg border border-black/10 bg-white p-3 text-sm">
          <p className="text-kami-charcoal">
            {resultadoImportacao.importados.length} romaneio(s) importado(s)
            {resultadoImportacao.importados.length > 0 && `: ${resultadoImportacao.importados.join(", ")}`}
          </p>
          {resultadoImportacao.ignorados.length > 0 && (
            <ul className="mt-1 text-kami-charcoal-light">
              {resultadoImportacao.ignorados.map((i, idx) => (
                <li key={idx}>
                  {i.codigo}: {i.motivo}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {carregando && <p className="text-sm text-kami-charcoal-light">Carregando...</p>}
      {erro && <p className="text-sm text-kami-red">{erro}</p>}
      {romaneios && <Board romaneios={romaneios} />}
    </div>
  );
}
