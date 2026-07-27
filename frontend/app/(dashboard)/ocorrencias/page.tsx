"use client";

import { useState } from "react";
import { useRequireRole } from "@/lib/roles";
import { useFetch } from "@/lib/use-fetch";
import { apiFetch, ApiError } from "@/lib/api-client";

type Categoria = "desvio_rota" | "nao_entrega" | "problema_romaneio";

type TipoOcorrencia = {
  id: number;
  categoria: Categoria;
  codigo: string;
  descricao: string;
  exige_foto: boolean;
  exige_observacao: boolean;
  ativo: boolean;
};

const LABEL_CATEGORIA: Record<Categoria, string> = {
  desvio_rota: "Desvio de rota",
  nao_entrega: "Não entrega",
  problema_romaneio: "Problema no romaneio",
};

export default function OcorrenciasPage() {
  const { carregando: carregandoAuth } = useRequireRole(["kami_admin"]);
  const { data: tipos, carregando, erro, recarregar } = useFetch<TipoOcorrencia[]>(
    carregandoAuth ? null : "/tipos-ocorrencia?incluir_inativos=true"
  );

  const [mostrarForm, setMostrarForm] = useState(false);
  const [categoria, setCategoria] = useState<Categoria>("desvio_rota");
  const [codigo, setCodigo] = useState("");
  const [descricao, setDescricao] = useState("");
  const [exigeFoto, setExigeFoto] = useState(false);
  const [exigeObservacao, setExigeObservacao] = useState(false);
  const [erroForm, setErroForm] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function handleCriar(e: React.FormEvent) {
    e.preventDefault();
    setErroForm(null);
    setEnviando(true);
    try {
      await apiFetch("/tipos-ocorrencia", {
        method: "POST",
        body: { categoria, codigo, descricao, exige_foto: exigeFoto, exige_observacao: exigeObservacao },
      });
      setCodigo("");
      setDescricao("");
      setExigeFoto(false);
      setExigeObservacao(false);
      setMostrarForm(false);
      recarregar();
    } catch (err) {
      setErroForm(err instanceof ApiError ? err.detail : "Não foi possível criar o tipo de ocorrência.");
    } finally {
      setEnviando(false);
    }
  }

  async function handleToggleAtivo(tipo: TipoOcorrencia) {
    await apiFetch(`/tipos-ocorrencia/${tipo.id}`, { method: "PATCH", body: { ativo: !tipo.ativo } });
    recarregar();
  }

  if (carregandoAuth) return null;

  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-lg font-semibold text-kami-charcoal">Tipos de ocorrência</h1>
        <button
          onClick={() => setMostrarForm((v) => !v)}
          className="rounded-lg bg-kami-red px-3 py-1.5 text-sm font-medium text-white hover:bg-kami-red-dark"
        >
          {mostrarForm ? "Cancelar" : "Novo tipo"}
        </button>
      </div>

      {mostrarForm && (
        <form onSubmit={handleCriar} className="mb-6 flex flex-col gap-3 rounded-xl border border-black/10 bg-white p-4">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <label className="flex flex-col gap-1 text-sm">
              Categoria
              <select
                value={categoria}
                onChange={(e) => setCategoria(e.target.value as Categoria)}
                className="rounded-lg border border-black/10 px-3 py-2 outline-none focus:border-kami-red"
              >
                <option value="desvio_rota">Desvio de rota</option>
                <option value="nao_entrega">Não entrega</option>
                <option value="problema_romaneio">Problema no romaneio</option>
              </select>
            </label>
            <label className="flex flex-col gap-1 text-sm">
              Código (identificador único)
              <input
                required
                value={codigo}
                onChange={(e) => setCodigo(e.target.value)}
                placeholder="ex: cliente_ausente"
                className="rounded-lg border border-black/10 px-3 py-2 outline-none focus:border-kami-red"
              />
            </label>
          </div>
          <label className="flex flex-col gap-1 text-sm">
            Descrição (exibida ao motorista)
            <input
              required
              value={descricao}
              onChange={(e) => setDescricao(e.target.value)}
              className="rounded-lg border border-black/10 px-3 py-2 outline-none focus:border-kami-red"
            />
          </label>
          <div className="flex gap-4 text-sm">
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={exigeFoto} onChange={(e) => setExigeFoto(e.target.checked)} />
              Exige foto
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={exigeObservacao} onChange={(e) => setExigeObservacao(e.target.checked)} />
              Exige observação
            </label>
          </div>
          {erroForm && <p className="text-sm text-kami-red">{erroForm}</p>}
          <button
            type="submit"
            disabled={enviando}
            className="self-start rounded-lg bg-kami-charcoal px-3 py-1.5 text-sm font-medium text-white disabled:opacity-60"
          >
            {enviando ? "Salvando..." : "Salvar"}
          </button>
        </form>
      )}

      {carregando && <p className="text-sm text-kami-charcoal-light">Carregando...</p>}
      {erro && <p className="text-sm text-kami-red">{erro}</p>}

      {(["desvio_rota", "nao_entrega", "problema_romaneio"] as Categoria[]).map((cat) => (
        <div key={cat} className="mb-6">
          <h2 className="mb-2 text-sm font-semibold text-kami-charcoal">{LABEL_CATEGORIA[cat]}</h2>
          <div className="overflow-hidden rounded-xl border border-black/10 bg-white">
            <table className="w-full text-left text-sm">
              <tbody>
                {tipos?.filter((t) => t.categoria === cat).map((t) => (
                  <tr key={t.id} className="border-t border-black/5 first:border-t-0">
                    <td className="px-4 py-2">{t.descricao}</td>
                    <td className="px-4 py-2 text-xs text-kami-charcoal-light">
                      {t.exige_foto && "foto "}
                      {t.exige_observacao && "observação"}
                    </td>
                    <td className="px-4 py-2">
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                          t.ativo ? "bg-green-100 text-green-700" : "bg-zinc-100 text-zinc-500"
                        }`}
                      >
                        {t.ativo ? "Ativo" : "Inativo"}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-right">
                      <button
                        onClick={() => handleToggleAtivo(t)}
                        className="text-xs font-medium text-kami-charcoal-light hover:text-kami-red"
                      >
                        {t.ativo ? "Desativar" : "Ativar"}
                      </button>
                    </td>
                  </tr>
                ))}
                {tipos?.filter((t) => t.categoria === cat).length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-4 py-4 text-center text-xs text-kami-charcoal-light">
                      Nenhum tipo cadastrado nesta categoria.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </div>
  );
}
