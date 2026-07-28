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
  aguardando_transportadora: string[];
  reatribuidos: string[];
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
  const [busca, setBusca] = useState("");

  const buscaNormalizada = busca.trim().toLowerCase();
  const romaneiosFiltrados = romaneios?.filter(
    (r) => !buscaNormalizada || r.codigo.toLowerCase().includes(buscaNormalizada)
  );

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
              title="A sincronização com o UNO já roda automaticamente a cada 10 minutos — use isso só pra forçar agora"
              className="rounded-lg border border-kami-red/40 px-3 py-1.5 text-sm font-medium text-kami-red hover:bg-kami-red/5 disabled:opacity-60"
            >
              {importando ? "Sincronizando..." : "Forçar sincronização com o UNO"}
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
          {resultadoImportacao.reatribuidos.length > 0 && (
            <p className="mt-1 text-kami-charcoal">
              {resultadoImportacao.reatribuidos.length} romaneio(s) que estavam aguardando transportadora
              já foram movidos pra definição de transporte: {resultadoImportacao.reatribuidos.join(", ")}
            </p>
          )}
          {resultadoImportacao.aguardando_transportadora.length > 0 && (
            <p className="mt-1 text-kami-charcoal">
              {resultadoImportacao.aguardando_transportadora.length} romaneio(s) aguardando definição de
              transportadora: {resultadoImportacao.aguardando_transportadora.join(", ")}
            </p>
          )}
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

      <div className="mb-4">
        <input
          type="text"
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
          placeholder="Pesquisar romaneio pelo código..."
          className="w-full max-w-xs rounded-lg border border-black/10 bg-white px-3 py-1.5 text-sm text-kami-charcoal placeholder:text-kami-charcoal-light/70 focus:border-kami-red focus:outline-none"
        />
        {buscaNormalizada && (
          <p className="mt-1 text-xs text-kami-charcoal-light">
            {romaneiosFiltrados?.length ?? 0} romaneio(s) encontrado(s) para &quot;{busca}&quot;
          </p>
        )}
      </div>

      {carregando && <p className="text-sm text-kami-charcoal-light">Carregando...</p>}
      {erro && <p className="text-sm text-kami-red">{erro}</p>}
      {romaneiosFiltrados && <Board romaneios={romaneiosFiltrados} />}
    </div>
  );
}
