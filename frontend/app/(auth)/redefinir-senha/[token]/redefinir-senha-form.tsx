"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiFetch, ApiError } from "@/lib/api-client";
import { PasswordInput } from "@/components/PasswordInput";

export function RedefinirSenhaForm({ token }: { token: string }) {
  const router = useRouter();
  const [novaSenha, setNovaSenha] = useState("");
  const [confirmacao, setConfirmacao] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [sucesso, setSucesso] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);

    if (novaSenha.length < 8) {
      setErro("A senha precisa ter pelo menos 8 caracteres.");
      return;
    }
    if (novaSenha !== confirmacao) {
      setErro("As senhas não coincidem.");
      return;
    }

    setEnviando(true);
    try {
      await apiFetch("/auth/redefinir-senha", {
        method: "POST",
        body: { token, nova_senha: novaSenha },
        auth: false,
      });
      setSucesso(true);
      setTimeout(() => router.push("/login"), 2000);
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível redefinir a senha.");
    } finally {
      setEnviando(false);
    }
  }

  if (sucesso) {
    return (
      <div className="text-center">
        <h1 className="text-xl font-semibold text-kami-charcoal">Senha redefinida!</h1>
        <p className="mt-2 text-sm text-kami-charcoal-light">Redirecionando para o login...</p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <h1 className="text-xl font-semibold text-kami-charcoal">Redefinir senha</h1>

      <label className="flex flex-col gap-1 text-sm">
        Nova senha
        <PasswordInput required minLength={8} value={novaSenha} onChange={setNovaSenha} />
      </label>

      <label className="flex flex-col gap-1 text-sm">
        Confirmar nova senha
        <PasswordInput required minLength={8} value={confirmacao} onChange={setConfirmacao} />
      </label>

      {erro && <p className="text-sm text-kami-red">{erro}</p>}

      <button
        type="submit"
        disabled={enviando}
        className="mt-2 rounded-lg bg-kami-red px-3 py-2 font-medium text-white transition hover:bg-kami-red-dark disabled:opacity-60"
      >
        {enviando ? "Salvando..." : "Salvar nova senha"}
      </button>

      <Link href="/login" className="text-center text-sm text-kami-charcoal-light hover:text-kami-red">
        Voltar para o login
      </Link>
    </form>
  );
}
