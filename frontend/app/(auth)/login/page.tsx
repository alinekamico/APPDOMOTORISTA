"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { homePorPapel } from "@/lib/roles";
import { ApiError } from "@/lib/api-client";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [mostrarSenha, setMostrarSenha] = useState(false);
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
        <div className="relative">
          <input
            type={mostrarSenha ? "text" : "password"}
            required
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
            className="w-full rounded-lg border border-black/10 px-3 py-2 pr-10 outline-none focus:border-kami-red"
          />
          <button
            type="button"
            onClick={() => setMostrarSenha((v) => !v)}
            aria-label={mostrarSenha ? "Ocultar senha" : "Mostrar senha"}
            className="absolute inset-y-0 right-0 flex items-center px-3 text-kami-charcoal-light hover:text-kami-charcoal"
          >
            {mostrarSenha ? (
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M17.94 17.94A10.94 10.94 0 0 1 12 19c-7 0-11-7-11-7a21.86 21.86 0 0 1 5.06-6.06M9.9 4.24A10.94 10.94 0 0 1 12 4c7 0 11 7 11 7a21.86 21.86 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                <line x1="1" y1="1" x2="23" y2="23" />
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7Z" />
                <circle cx="12" cy="12" r="3" />
              </svg>
            )}
          </button>
        </div>
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
