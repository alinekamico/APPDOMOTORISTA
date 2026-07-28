"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { homePorPapel } from "@/lib/roles";
import { ApiError } from "@/lib/api-client";
import { PasswordInput } from "@/components/PasswordInput";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    setEnviando(true);
    try {
      const usuario = await login(email, senha);
      router.push(homePorPapel(usuario.papel));
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível entrar. Tente novamente.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <h1 className="text-xl font-semibold text-kami-charcoal">Entrar</h1>

      <label className="flex flex-col gap-1 text-sm">
        E-mail
        <input
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="rounded-lg border border-black/10 px-3 py-2 outline-none focus:border-kami-red"
          placeholder="voce@transportadora.com.br"
        />
      </label>

      <label className="flex flex-col gap-1 text-sm">
        Senha
        <PasswordInput required value={senha} onChange={setSenha} />
      </label>

      {erro && <p className="text-sm text-kami-red">{erro}</p>}

      <button
        type="submit"
        disabled={enviando}
        className="mt-2 rounded-lg bg-kami-red px-3 py-2 font-medium text-white transition hover:bg-kami-red-dark disabled:opacity-60"
      >
        {enviando ? "Entrando..." : "Entrar"}
      </button>

      <Link href="/esqueci-senha" className="text-center text-sm text-kami-charcoal-light hover:text-kami-red">
        Esqueci minha senha
      </Link>
    </form>
  );
}
