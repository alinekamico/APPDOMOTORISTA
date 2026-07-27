"use client";

import { useState } from "react";
import { useRequireRole } from "@/lib/roles";
import { useFetch } from "@/lib/use-fetch";
import { apiFetch, ApiError } from "@/lib/api-client";

type Veiculo = {
  id: number;
  transportadora_nome: string;
  placa: string;
  tipo: string;
  capacidade_kg: number | null;
  ativo: boolean;
};

export default function VeiculosPage() {
  const { usuario, carregando: carregandoAuth } = useRequireRole(["kami_admin", "transportadora_admin"]);
  const somenteLeitura = usuario?.papel === "kami_admin";
  const { data: veiculos, carregando, erro, recarregar } = useFetch<Veiculo[]>(
    carregandoAuth ? null : "/veiculos"
  );

  const [mostrarForm, setMostrarForm] = useState(false);
  const [placa, setPlaca] = useState("");
  const [tipo, setTipo] = useState("");
  const [capacidade, setCapacidade] = useState("");
  const [erroForm, setErroForm] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function handleCriar(e: React.FormEvent) {
    e.preventDefault();
    setErroForm(null);
    setEnviando(true);
    try {
      await apiFetch("/veiculos", {
        method: "POST",
        body: { placa, tipo, capacidade_kg: capacidade ? Number(capacidade) : null },
      });
      setPlaca("");
      setTipo("");
      setCapacidade("");
      setMostrarForm(false);
      recarregar();
    } catch (err) {
      setErroForm(err instanceof ApiError ? err.detail : "Não foi possível cadastrar o veículo.");
    } finally {
      setEnviando(false);
    }
  }

  async function handleToggleAtivo(veiculo: Veiculo) {
    await apiFetch(`/veiculos/${veiculo.id}`, { method: "PATCH", body: { ativo: !veiculo.ativo } });
    recarregar();
  }

  if (carregandoAuth) return null;

  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-kami-charcoal">Veículos</h1>
          {somenteLeitura && (
            <p className="text-xs text-kami-charcoal-light">
              Visão de todas as transportadoras — só a própria transportadora pode cadastrar ou alterar.
            </p>
          )}
        </div>
        {!somenteLeitura && (
          <button
            onClick={() => setMostrarForm((v) => !v)}
            className="rounded-lg bg-kami-red px-3 py-1.5 text-sm font-medium text-white hover:bg-kami-red-dark"
          >
            {mostrarForm ? "Cancelar" : "Novo veículo"}
          </button>
        )}
      </div>

      {mostrarForm && !somenteLeitura && (
        <form onSubmit={handleCriar} className="mb-6 flex flex-col gap-3 rounded-xl border border-black/10 bg-white p-4">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <label className="flex flex-col gap-1 text-sm">
              Placa
              <input
                required
                value={placa}
                onChange={(e) => setPlaca(e.target.value.toUpperCase())}
                placeholder="ABC1D23"
                className="rounded-lg border border-black/10 px-3 py-2 outline-none focus:border-kami-red"
              />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              Tipo
              <input
                required
                value={tipo}
                onChange={(e) => setTipo(e.target.value)}
                placeholder="Van, caminhão 3/4..."
                className="rounded-lg border border-black/10 px-3 py-2 outline-none focus:border-kami-red"
              />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              Capacidade (kg)
              <input
                type="number"
                value={capacidade}
                onChange={(e) => setCapacidade(e.target.value)}
                className="rounded-lg border border-black/10 px-3 py-2 outline-none focus:border-kami-red"
              />
            </label>
          </div>
          {erroForm && <p className="text-sm text-kami-red">{erroForm}</p>}
          <button
            type="submit"
            disabled={enviando}
            className="self-start rounded-lg bg-kami-charcoal px-3 py-1.5 text-sm font-medium text-white hover:bg-kami-charcoal-light disabled:opacity-60"
          >
            {enviando ? "Salvando..." : "Salvar"}
          </button>
        </form>
      )}

      {carregando && <p className="text-sm text-kami-charcoal-light">Carregando...</p>}
      {erro && <p className="text-sm text-kami-red">{erro}</p>}

      <div className="overflow-hidden rounded-xl border border-black/10 bg-white">
        <table className="w-full text-left text-sm">
          <thead className="bg-zinc-50 text-kami-charcoal-light">
            <tr>
              {somenteLeitura && <th className="px-4 py-2 font-medium">Transportadora</th>}
              <th className="px-4 py-2 font-medium">Placa</th>
              <th className="px-4 py-2 font-medium">Tipo</th>
              <th className="px-4 py-2 font-medium">Capacidade</th>
              <th className="px-4 py-2 font-medium">Status</th>
              {!somenteLeitura && <th className="px-4 py-2" />}
            </tr>
          </thead>
          <tbody>
            {veiculos?.map((v) => (
              <tr key={v.id} className="border-t border-black/5">
                {somenteLeitura && (
                  <td className="px-4 py-2 text-kami-charcoal-light">{v.transportadora_nome}</td>
                )}
                <td className="px-4 py-2 font-medium">{v.placa}</td>
                <td className="px-4 py-2 text-kami-charcoal-light">{v.tipo}</td>
                <td className="px-4 py-2 text-kami-charcoal-light">
                  {v.capacidade_kg ? `${v.capacidade_kg} kg` : "—"}
                </td>
                <td className="px-4 py-2">
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                      v.ativo ? "bg-green-100 text-green-700" : "bg-zinc-100 text-zinc-500"
                    }`}
                  >
                    {v.ativo ? "Ativo" : "Inativo"}
                  </span>
                </td>
                {!somenteLeitura && (
                  <td className="px-4 py-2 text-right">
                    <button
                      onClick={() => handleToggleAtivo(v)}
                      className="text-xs font-medium text-kami-charcoal-light hover:text-kami-red"
                    >
                      {v.ativo ? "Desativar" : "Ativar"}
                    </button>
                  </td>
                )}
              </tr>
            ))}
            {veiculos?.length === 0 && (
              <tr>
                <td colSpan={somenteLeitura ? 5 : 5} className="px-4 py-6 text-center text-kami-charcoal-light">
                  Nenhum veículo cadastrado ainda.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
