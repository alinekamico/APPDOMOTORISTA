"use client";

import { Fragment, useState } from "react";
import { useRequireRole } from "@/lib/roles";
import { useFetch } from "@/lib/use-fetch";
import { apiFetch, ApiError } from "@/lib/api-client";

type Motorista = {
  id: number;
  transportadora_nome: string;
  nome: string;
  email: string;
  cnh: string;
  cnh_categoria: string;
  telefone: string;
  ativo: boolean;
};

const CAMPOS_INICIAIS = { nome: "", email: "", senha: "", cnh: "", cnh_categoria: "", telefone: "" };

export default function MotoristasPage() {
  const { usuario, carregando: carregandoAuth } = useRequireRole(["kami_admin", "transportadora_admin"]);
  const somenteLeitura = usuario?.papel === "kami_admin";
  const { data: motoristas, carregando, erro, recarregar } = useFetch<Motorista[]>(
    carregandoAuth ? null : "/motoristas"
  );

  const [mostrarForm, setMostrarForm] = useState(false);
  const [campos, setCampos] = useState(CAMPOS_INICIAIS);
  const [erroForm, setErroForm] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  const [resetandoId, setResetandoId] = useState<number | null>(null);
  const [novaSenha, setNovaSenha] = useState("");
  const [erroSenha, setErroSenha] = useState<string | null>(null);
  const [salvandoSenha, setSalvandoSenha] = useState(false);

  function setCampo<K extends keyof typeof CAMPOS_INICIAIS>(campo: K, valor: string) {
    setCampos((atual) => ({ ...atual, [campo]: valor }));
  }

  async function handleCriar(e: React.FormEvent) {
    e.preventDefault();
    setErroForm(null);
    setEnviando(true);
    try {
      await apiFetch("/motoristas", { method: "POST", body: campos });
      setCampos(CAMPOS_INICIAIS);
      setMostrarForm(false);
      recarregar();
    } catch (err) {
      setErroForm(err instanceof ApiError ? err.detail : "Não foi possível cadastrar o motorista.");
    } finally {
      setEnviando(false);
    }
  }

  async function handleToggleAtivo(motorista: Motorista) {
    await apiFetch(`/motoristas/${motorista.id}`, { method: "PATCH", body: { ativo: !motorista.ativo } });
    recarregar();
  }

  function handleAbrirReset(motoristaId: number) {
    setResetandoId(motoristaId);
    setNovaSenha("");
    setErroSenha(null);
  }

  function handleCancelarReset() {
    setResetandoId(null);
    setNovaSenha("");
    setErroSenha(null);
  }

  async function handleSalvarSenha(motoristaId: number) {
    if (novaSenha.length < 8) {
      setErroSenha("A senha precisa ter ao menos 8 caracteres.");
      return;
    }
    setErroSenha(null);
    setSalvandoSenha(true);
    try {
      await apiFetch(`/motoristas/${motoristaId}`, { method: "PATCH", body: { senha: novaSenha } });
      setResetandoId(null);
      setNovaSenha("");
    } catch (err) {
      setErroSenha(err instanceof ApiError ? err.detail : "Não foi possível alterar a senha.");
    } finally {
      setSalvandoSenha(false);
    }
  }

  if (carregandoAuth) return null;

  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-kami-charcoal">Motoristas</h1>
          {somenteLeitura ? (
            <p className="text-xs text-kami-charcoal-light">
              Visão de todas as transportadoras — só a própria transportadora pode cadastrar ou alterar.
            </p>
          ) : (
            <p className="text-xs text-kami-charcoal-light">
              O motorista também é um usuário do sistema — ele só consegue entrar no app depois que
              você liberar o acesso dele aqui.
            </p>
          )}
        </div>
        {!somenteLeitura && (
          <button
            onClick={() => setMostrarForm((v) => !v)}
            className="rounded-lg bg-kami-red px-3 py-1.5 text-sm font-medium text-white hover:bg-kami-red-dark"
          >
            {mostrarForm ? "Cancelar" : "Novo motorista"}
          </button>
        )}
      </div>

      {mostrarForm && !somenteLeitura && (
        <form onSubmit={handleCriar} className="mb-6 flex flex-col gap-3 rounded-xl border border-black/10 bg-white p-4">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <label className="flex flex-col gap-1 text-sm">
              Nome
              <input
                required
                value={campos.nome}
                onChange={(e) => setCampo("nome", e.target.value)}
                className="rounded-lg border border-black/10 px-3 py-2 outline-none focus:border-kami-red"
              />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              E-mail
              <input
                type="email"
                required
                value={campos.email}
                onChange={(e) => setCampo("email", e.target.value)}
                className="rounded-lg border border-black/10 px-3 py-2 outline-none focus:border-kami-red"
              />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              Senha provisória
              <input
                type="password"
                required
                minLength={8}
                value={campos.senha}
                onChange={(e) => setCampo("senha", e.target.value)}
                className="rounded-lg border border-black/10 px-3 py-2 outline-none focus:border-kami-red"
              />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              Telefone
              <input
                required
                value={campos.telefone}
                onChange={(e) => setCampo("telefone", e.target.value)}
                placeholder="(11) 90000-0000"
                className="rounded-lg border border-black/10 px-3 py-2 outline-none focus:border-kami-red"
              />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              CNH
              <input
                required
                value={campos.cnh}
                onChange={(e) => setCampo("cnh", e.target.value)}
                className="rounded-lg border border-black/10 px-3 py-2 outline-none focus:border-kami-red"
              />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              Categoria CNH
              <input
                required
                value={campos.cnh_categoria}
                onChange={(e) => setCampo("cnh_categoria", e.target.value)}
                placeholder="B, D, E..."
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
              <th className="px-4 py-2 font-medium">Nome</th>
              <th className="px-4 py-2 font-medium">Contato</th>
              <th className="px-4 py-2 font-medium">CNH</th>
              <th className="px-4 py-2 font-medium">Status</th>
              {!somenteLeitura && <th className="px-4 py-2" />}
            </tr>
          </thead>
          <tbody>
            {motoristas?.map((m) => (
              <Fragment key={m.id}>
                <tr className="border-t border-black/5">
                  {somenteLeitura && (
                    <td className="px-4 py-2 text-kami-charcoal-light">{m.transportadora_nome}</td>
                  )}
                  <td className="px-4 py-2 font-medium">{m.nome}</td>
                  <td className="px-4 py-2 text-kami-charcoal-light">
                    {m.email}
                    <br />
                    {m.telefone}
                  </td>
                  <td className="px-4 py-2 text-kami-charcoal-light">
                    {m.cnh} · {m.cnh_categoria}
                  </td>
                  <td className="px-4 py-2">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        m.ativo ? "bg-green-100 text-green-700" : "bg-amber-100 text-amber-700"
                      }`}
                    >
                      {m.ativo ? "Acesso liberado" : "Aguardando liberação"}
                    </span>
                  </td>
                  {!somenteLeitura && (
                    <td className="px-4 py-2 text-right">
                      <div className="flex justify-end gap-3">
                        <button
                          onClick={() => handleAbrirReset(m.id)}
                          className="text-xs font-medium text-kami-charcoal-light hover:text-kami-red"
                        >
                          Redefinir senha
                        </button>
                        <button
                          onClick={() => handleToggleAtivo(m)}
                          className="text-xs font-medium text-kami-charcoal-light hover:text-kami-red"
                        >
                          {m.ativo ? "Bloquear acesso" : "Liberar acesso"}
                        </button>
                      </div>
                    </td>
                  )}
                </tr>
                {resetandoId === m.id && !somenteLeitura && (
                  <tr className="border-t border-black/5 bg-zinc-50">
                    <td colSpan={somenteLeitura ? 5 : 5} className="px-4 py-3">
                      <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                        <span className="text-xs text-kami-charcoal-light">
                          Nova senha para <strong>{m.nome}</strong>:
                        </span>
                        <input
                          type="password"
                          autoFocus
                          minLength={8}
                          value={novaSenha}
                          onChange={(e) => setNovaSenha(e.target.value)}
                          placeholder="Mínimo 8 caracteres"
                          className="rounded-lg border border-black/10 px-3 py-1.5 text-sm outline-none focus:border-kami-red"
                        />
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleSalvarSenha(m.id)}
                            disabled={salvandoSenha}
                            className="rounded-lg bg-kami-red px-3 py-1.5 text-xs font-medium text-white hover:bg-kami-red-dark disabled:opacity-60"
                          >
                            {salvandoSenha ? "Salvando..." : "Salvar"}
                          </button>
                          <button
                            onClick={handleCancelarReset}
                            disabled={salvandoSenha}
                            className="rounded-lg border border-black/10 px-3 py-1.5 text-xs font-medium text-kami-charcoal disabled:opacity-60"
                          >
                            Cancelar
                          </button>
                        </div>
                      </div>
                      {erroSenha && <p className="mt-1 text-xs text-kami-red">{erroSenha}</p>}
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
            {motoristas?.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-kami-charcoal-light">
                  Nenhum motorista cadastrado ainda.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
