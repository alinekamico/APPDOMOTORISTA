"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth, type Papel } from "@/lib/auth-context";

/**
 * Guarda de rota client-side (só UX — a autorização de verdade é sempre no backend).
 * Redireciona para /login se não autenticado, ou para a home do papel correto se o papel não bate.
 */
export function useRequireRole(papeisPermitidos: Papel[]) {
  const { usuario, carregando } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (carregando) return;
    if (!usuario) {
      router.replace("/login");
      return;
    }
    if (!papeisPermitidos.includes(usuario.papel)) {
      router.replace(homePorPapel(usuario.papel));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [usuario, carregando]);

  return { usuario, carregando };
}

export function homePorPapel(papel: Papel): string {
  switch (papel) {
    case "kami_admin":
      return "/romaneios";
    case "transportadora_admin":
      return "/romaneios";
    case "motorista":
      return "/minha-rota";
    default:
      return "/login";
  }
}
