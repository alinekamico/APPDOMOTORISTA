"use client";

import { Fragment, useState } from "react";
import { useRequireRole } from "@/lib/roles";
import { useFetch } from "@/lib/use-fetch";
import { apiFetch, ApiError } from "@/lib/api-client";
import { PasswordInput } from "@/components/PasswordInput";

type Usuario = {
  id: number;
  nome: string;
  email: string;
  papel: "kami_admin" | "transportadora_admin" | "motorista";
  departamento: string | null;
  transportadora_nome: string | null;
  ativo: boolean;
  criado_em: string;
  last_login_at: string | null;
};

const LABEL_PAPEL: Record<Usuario["papel"], string> = {
  kami_admin: "KAMI",
  transportadora_admin: "Transportadora",
  motorista: "Motorista",
};

const CAMPOS_INICIAIS = { nome: "", email: "", senha: "", departamento: "" };

export default function UsuariosPage() {
  const { carregando: carregandoAuth } = useRequireRole(["kami_admin"]);
  const { data: usuarios, carregando, erro, recarregar } = useFetch<Usuario[]>(
    carregandoAuth ? null : "/usuarios"
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
      await apiFetch("/usuarios", {
        method: "POST",
        body: { ...campos, departamento: campos.departamento || null },
      });
      setCampos(CAMPOS_INICIAIS);
      setMostrarForm(false);
      recarregar();
    } catch (err) {
      setErroForm(err instanceof ApiError ? err.detail : "Não foi possível cadastrar o usuário.");
    } finally {
      setEnviando(false);
    }
  }

  function handleAbrirReset(usuarioId: number) {
    setResetandoId(usuarioId);
    setNovaSenha("");
    setErroSenha(null);
  }

  function handleCancelarReset() {
    setResetandoId(null);
    setErroSenha(null);
  }

  async function handleSalvarSenha(usuarioId: number) {
    if (novaSenha.length < 8) {
      setErroSenha("A senha precisa ter ao menos 8 caracteres.");
      return;
    }
    setErroSenha(null);
    setSalvandoSenha(true);
    try {
      await apiFetch(`/usuarios/${usuarioId}/senha`, { method: "PATCH", body: { senha: novaSenha } });
      setResetandoId(null);
      setNovaSenha("");
    } catch (err) {
      setErroSenha(err instanceof ApiError ? err.detail : "Não foi possível redefinir a senha.");
    } finally {
      setSalvandoSenha(false);
    }
  }

  if (carregandoAuth) return null;

  return (
    <div className="mx-auto max-w-4xl">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-kami-charcoal">Usuários</h1>
          <p className="text-xs text-kami-charcoal-light">
            Todos os usuários do sistema — KAMI, transportadoras e motoristas. Só a KAMI enxerga essa tela.
          </p>
        </div>
        <button
          onClick={() => setMostrarForm((v) => !v)}
          className="rounded-lg bg-kami-red px-3 py-1.5 text-sm font-medium text-white hover:bg-kami-red-dark"
        >
          {mostrarForm ? "Cancelar" : "Novo usuário KAMI"}
        </button>
      </div>

      {mostrarForm && (
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
              <PasswordInput required minLength={8} value={campos.senha} onChange={(v) => setCampo("senha", v)} />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              Departamento
              <input
                value={campos.departamento}
                onChange={(e) => setCampo("departamento", e.target.value)}
                placeholder="Tecnologia da Informação, Operações..."
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
              <th className="px-4 py-2 font-medium">Nome</th>
              <th className="px-4 py-2 font-medium">E-mail</th>
              <th className="px-4 py-2 font-medium">Papel</th>
              <th className="px-4 py-2 font-medium">Departamento / Transportadora</th>
              <th className="px-4 py-2 font-medium">Status</th>
              <th className="px-4 py-2" />
            </tr>
          </thead>
          <tbody>
            {usuarios?.map((u) => (
              <Fragment key={u.id}>
                <tr className="border-t border-black/5">
                  <td className="px-4 py-2 font-medium">{u.nome}</td>
                  <td className="px-4 py-2 text-kami-charcoal-light">{u.email}</td>
                  <td className="px-4 py-2 text-kami-charcoal-light">{LABEL_PAPEL[u.papel]}</td>
                  <td className="px-4 py-2 text-kami-charcoal-light">
                    {u.transportadora_nome ?? u.departamento ?? "—"}
                  </td>
                  <td className="px-4 py-2">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        u.ativo ? "bg-green-100 text-green-700" : "bg-amber-100 text-amber-700"
                      }`}
                    >
                      {u.ativo ? "Ativo" : "Inativo"}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-right">
                    <button
                      onClick={() => handleAbrirReset(u.id)}
                      className="text-xs font-medium text-kami-charcoal-light hover:text-kami-red"
                    >
                      Redefinir senha
                    </button>
                  </td>
                </tr>
                {resetandoId === u.id && (
                  <tr className="border-t border-black/5 bg-zinc-50">
                    <td colSpan={6} className="px-4 py-3">
                      <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                        <span className="text-xs text-kami-charcoal-light">
                          Nova senha para <strong>{u.nome}</strong>:
                        </span>
                        <PasswordInput
                          autoFocus
                          minLength={8}
                          value={novaSenha}
                          onChange={setNovaSenha}
                          placeholder="Mínimo 8 caracteres"
                          className="rounded-lg border border-black/10 px-3 py-1.5 pr-10 text-sm outline-none focus:border-kami-red"
                        />
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleSalvarSenha(u.id)}
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
            {usuarios?.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-center text-kami-charcoal-light">
                  Nenhum usuário cadastrado ainda.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
