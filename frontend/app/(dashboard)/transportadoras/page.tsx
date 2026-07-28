"use client";

import { Fragment, useState } from "react";
import { useRequireRole } from "@/lib/roles";
import { useFetch } from "@/lib/use-fetch";
import { apiFetch, ApiError } from "@/lib/api-client";
import { PasswordInput } from "@/components/PasswordInput";

type Transportadora = {
  id: number;
  razao_social: string;
  nome_fantasia: string;
  cnpj: string;
  ativo: boolean;
};

const CAMPOS_ADMIN_INICIAIS = { nome: "", email: "", senha: "", departamento: "" };

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

  const [sincronizando, setSincronizando] = useState(false);
  const [resultadoSync, setResultadoSync] = useState<{
    criadas: string[];
    ja_existentes: string[];
    descartadas: string[];
  } | null>(null);
  const [erroSync, setErroSync] = useState<string | null>(null);

  async function handleSincronizarUno() {
    setErroSync(null);
    setResultadoSync(null);
    setSincronizando(true);
    try {
      const resultado = await apiFetch<{ criadas: string[]; ja_existentes: string[]; descartadas: string[] }>(
        "/transportadoras/sincronizar-uno",
        { method: "POST" }
      );
      setResultadoSync(resultado);
      recarregar();
    } catch (err) {
      setErroSync(err instanceof ApiError ? err.detail : "Não foi possível sincronizar com o UNO.");
    } finally {
      setSincronizando(false);
    }
  }

  const [transportadoraAdminId, setTransportadoraAdminId] = useState<number | null>(null);
  const [camposAdmin, setCamposAdmin] = useState(CAMPOS_ADMIN_INICIAIS);
  const [erroAdmin, setErroAdmin] = useState<string | null>(null);
  const [sucessoAdmin, setSucessoAdmin] = useState<string | null>(null);
  const [enviandoAdmin, setEnviandoAdmin] = useState(false);

  function setCampoAdmin<K extends keyof typeof CAMPOS_ADMIN_INICIAIS>(campo: K, valor: string) {
    setCamposAdmin((atual) => ({ ...atual, [campo]: valor }));
  }

  function handleAbrirCriarAdmin(transportadoraId: number) {
    setTransportadoraAdminId(transportadoraId);
    setCamposAdmin(CAMPOS_ADMIN_INICIAIS);
    setErroAdmin(null);
    setSucessoAdmin(null);
  }

  function handleCancelarCriarAdmin() {
    setTransportadoraAdminId(null);
    setErroAdmin(null);
  }

  async function handleCriarAdmin(e: React.FormEvent, transportadoraId: number) {
    e.preventDefault();
    setErroAdmin(null);
    setEnviandoAdmin(true);
    try {
      await apiFetch(`/transportadoras/${transportadoraId}/admins`, {
        method: "POST",
        body: {
          nome: camposAdmin.nome,
          email: camposAdmin.email,
          senha: camposAdmin.senha,
          departamento: camposAdmin.departamento || null,
        },
      });
      setSucessoAdmin(`Login criado para ${camposAdmin.email}`);
      setCamposAdmin(CAMPOS_ADMIN_INICIAIS);
    } catch (err) {
      setErroAdmin(err instanceof ApiError ? err.detail : "Não foi possível criar o login.");
    } finally {
      setEnviandoAdmin(false);
    }
  }

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
        <div className="flex gap-2">
          <button
            onClick={handleSincronizarUno}
            disabled={sincronizando}
            className="rounded-lg border border-kami-red/40 px-3 py-1.5 text-sm font-medium text-kami-red hover:bg-kami-red/5 disabled:opacity-60"
          >
            {sincronizando ? "Sincronizando..." : "Sincronizar transportadoras do UNO"}
          </button>
          <button
            onClick={() => setMostrarForm((v) => !v)}
            className="rounded-lg bg-kami-red px-3 py-1.5 text-sm font-medium text-white hover:bg-kami-red-dark"
          >
            {mostrarForm ? "Cancelar" : "Nova transportadora"}
          </button>
        </div>
      </div>

      {erroSync && <p className="mb-3 text-sm text-kami-red">{erroSync}</p>}
      {resultadoSync && (
        <div className="mb-4 rounded-lg border border-black/10 bg-white p-3 text-sm">
          <p className="text-kami-charcoal">
            {resultadoSync.criadas.length} transportadora(s) cadastrada(s)
            {resultadoSync.criadas.length > 0 && `: ${resultadoSync.criadas.join(", ")}`}
          </p>
          {resultadoSync.ja_existentes.length > 0 && (
            <p className="mt-1 text-kami-charcoal-light">
              {resultadoSync.ja_existentes.length} já cadastrada(s) anteriormente
            </p>
          )}
          {resultadoSync.descartadas.length > 0 && (
            <p className="mt-1 text-kami-charcoal-light">
              {resultadoSync.descartadas.length} descartada(s) por serem registro de teste/CNPJ inválido:{" "}
              {resultadoSync.descartadas.join(", ")}
            </p>
          )}
        </div>
      )}

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
              <th className="px-4 py-2" />
            </tr>
          </thead>
          <tbody>
            {transportadoras?.map((t) => (
              <Fragment key={t.id}>
                <tr className="border-t border-black/5">
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
                  <td className="px-4 py-2 text-right">
                    <button
                      onClick={() => handleAbrirCriarAdmin(t.id)}
                      className="text-xs font-medium text-kami-charcoal-light hover:text-kami-red"
                    >
                      Criar login de admin
                    </button>
                  </td>
                </tr>
                {transportadoraAdminId === t.id && (
                  <tr className="border-t border-black/5 bg-zinc-50">
                    <td colSpan={5} className="px-4 py-4">
                      <form
                        onSubmit={(e) => handleCriarAdmin(e, t.id)}
                        className="flex flex-col gap-3"
                      >
                        <p className="text-xs text-kami-charcoal-light">
                          Novo login de <strong>transportadora_admin</strong> para{" "}
                          <strong>{t.nome_fantasia}</strong>
                        </p>
                        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                          <label className="flex flex-col gap-1 text-sm">
                            Nome
                            <input
                              required
                              value={camposAdmin.nome}
                              onChange={(e) => setCampoAdmin("nome", e.target.value)}
                              className="rounded-lg border border-black/10 px-3 py-2 text-sm outline-none focus:border-kami-red"
                            />
                          </label>
                          <label className="flex flex-col gap-1 text-sm">
                            E-mail
                            <input
                              type="email"
                              required
                              value={camposAdmin.email}
                              onChange={(e) => setCampoAdmin("email", e.target.value)}
                              className="rounded-lg border border-black/10 px-3 py-2 text-sm outline-none focus:border-kami-red"
                            />
                          </label>
                          <label className="flex flex-col gap-1 text-sm">
                            Senha provisória
                            <PasswordInput
                              required
                              minLength={8}
                              value={camposAdmin.senha}
                              onChange={(v) => setCampoAdmin("senha", v)}
                            />
                          </label>
                          <label className="flex flex-col gap-1 text-sm">
                            Departamento (opcional)
                            <input
                              value={camposAdmin.departamento}
                              onChange={(e) => setCampoAdmin("departamento", e.target.value)}
                              className="rounded-lg border border-black/10 px-3 py-2 text-sm outline-none focus:border-kami-red"
                            />
                          </label>
                        </div>
                        {erroAdmin && <p className="text-xs text-kami-red">{erroAdmin}</p>}
                        {sucessoAdmin && <p className="text-xs text-green-700">{sucessoAdmin}</p>}
                        <div className="flex gap-2">
                          <button
                            type="submit"
                            disabled={enviandoAdmin}
                            className="self-start rounded-lg bg-kami-red px-3 py-1.5 text-xs font-medium text-white hover:bg-kami-red-dark disabled:opacity-60"
                          >
                            {enviandoAdmin ? "Criando..." : "Criar login"}
                          </button>
                          <button
                            type="button"
                            onClick={handleCancelarCriarAdmin}
                            disabled={enviandoAdmin}
                            className="self-start rounded-lg border border-black/10 px-3 py-1.5 text-xs font-medium text-kami-charcoal disabled:opacity-60"
                          >
                            Fechar
                          </button>
                        </div>
                      </form>
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
            {transportadoras?.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-kami-charcoal-light">
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
