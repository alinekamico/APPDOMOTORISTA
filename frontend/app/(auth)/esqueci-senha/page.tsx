"use client";

import { useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";

export default function EsqueciSenhaPage() {
  const [email, setEmail] = useState("");
  const [enviado, setEnviado] = useState(false);
  const [enviando, setEnviando] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setEnviando(true);
    try {
      await apiFetch("/auth/esqueci-senha", { method: "POST", body: { email }, auth: false });
    } finally {
      setEnviando(false);
      setEnviado(true);
    }
  }

  if (enviado) {
    return (
      <div className="flex flex-col gap-4 text-center">
        <h1 className="text-xl font-semibold text-kami-charcoal">Verifique seu e-mail</h1>
        <p className="text-sm text-kami-charcoal-light">
          Se {email} estiver cadastrado, você vai receber um link para redefinir sua senha
          (válido por 30 minutos).
        </p>
        <Link href="/login" className="text-sm text-kami-red hover:text-kami-red-dark">
          Voltar para o login
        </Link>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <h1 className="text-xl font-semibold text-kami-charcoal">Esqueci minha senha</h1>
      <p className="text-sm text-kami-charcoal-light">
        Informe seu e-mail cadastrado e enviaremos um link para redefinir sua senha.
      </p>

      <label className="flex flex-col gap-1 text-sm">
        E-mail
        <input
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="rounded-lg border border-black/10 px-3 py-2 outline-none focus:border-kami-red"
        />
      </label>

      <button
        type="submit"
        disabled={enviando}
        className="mt-2 rounded-lg bg-kami-red px-3 py-2 font-medium text-white transition hover:bg-kami-red-dark disabled:opacity-60"
      >
        {enviando ? "Enviando..." : "Enviar link"}
      </button>

      <Link href="/login" className="text-center text-sm text-kami-charcoal-light hover:text-kami-red">
        Voltar para o login
      </Link>
    </form>
  );
}
