"use client";

import { useState } from "react";
import { useRequireRole } from "@/lib/roles";
import { useFetch } from "@/lib/use-fetch";
import { apiFetch, ApiError } from "@/lib/api-client";

type Transportadora = {
  id: number;
  razao_social: string;
  nome_fantasia: string;
  cnpj: string;
  ativo: boolean;
};

export default function TransportadorasPage() {
  const { carregando: carregandoAuth } = useRequireRole(["kami_admin"]);
  const { data: transportadoras, carregando, erro, recarregar } = useFetch<Transportadora[]>(
    carregandoAuth ? null : "/transportadoras"
  );

  const [mostrarForm, setMostrarForm] = useState(false);
  const [razaoSocial, setRazaoSocial] = useState("");
  const [nomeFantasia, setNomeFantasia] = useState("");
  const [cnpj, setCnpj] = useState("");
  const [erroForm, setErroForm] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function handleCriar(e: React.FormEvent) {
    e.preventDefault();
    setErroForm(null);
    setEnviando(true);
    try {
      await apiFetch("/transportadoras", {
        method: "POST",
        body: { razao_social: razaoSocial, nome_fantasia: nomeFantasia, cnpj },
      });
      setRazaoSocial("");
      setNomeFantasia("");
      setCnpj("");
      setMostrarForm(false);
      recarregar();
    } catch (err) {
      setErroForm(err instanceof ApiError ? err.detail : "Não foi possível criar a transportadora.");
    } finally {
      setEnviando(false);
    }
  }

  if (carregandoAuth) return null;

  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-lg font-semibold text-kami-charcoal">Transportadoras</h1>
        <button
          onClick={() => setMostrarForm((v) => !v)}
          className="rounded-lg bg-kami-red px-3 py-1.5 text-sm font-medium text-white hover:bg-kami-red-dark"
        >
          {mostrarForm ? "Cancelar" : "Nova transportadora"}
        </button>
      </div>

      {mostrarForm && (
        <form onSubmit={handleCriar} className="mb-6 flex flex-col gap-3 rounded-xl border border-black/10 bg-white p-4">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <label className="flex flex-col gap-1 text-sm">
              Razão social
              <input
                required
                value={razaoSocial}
                onChange={(e) => setRazaoSocial(e.target.value)}
                className="rounded-lg border border-black/10 px-3 py-2 outline-none focus:border-kami-red"
              />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              Nome fantasia
              <input
                required
                value={nomeFantasia}
                onChange={(e) => setNomeFantasia(e.target.value)}
                className="rounded-lg border border-black/10 px-3 py-2 outline-none focus:border-kami-red"
              />
            </label>
          </div>
          <label className="flex flex-col gap-1 text-sm">
            CNPJ
            <input
              required
              value={cnpj}
              onChange={(e) => setCnpj(e.target.value)}
              placeholder="00.000.000/0000-00"
              className="rounded-lg border border-black/10 px-3 py-2 outline-none focus:border-kami-red"
            />
          </label>
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
              <th className="px-4 py-2 font-medium">Nome fantasia</th>
              <th className="px-4 py-2 font-medium">Razão social</th>
              <th className="px-4 py-2 font-medium">CNPJ</th>
              <th className="px-4 py-2 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {transportadoras?.map((t) => (
              <tr key={t.id} className="border-t border-black/5">
                <td className="px-4 py-2">{t.nome_fantasia}</td>
                <td className="px-4 py-2 text-kami-charcoal-light">{t.razao_social}</td>
                <td className="px-4 py-2 text-kami-charcoal-light">{t.cnpj}</td>
                <td className="px-4 py-2">
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                      t.ativo ? "bg-green-100 text-green-700" : "bg-zinc-100 text-zinc-500"
                    }`}
                  >
                    {t.ativo ? "Ativa" : "Inativa"}
                  </span>
                </td>
              </tr>
            ))}
            {transportadoras?.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-kami-charcoal-light">
                  Nenhuma transportadora cadastrada ainda.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
