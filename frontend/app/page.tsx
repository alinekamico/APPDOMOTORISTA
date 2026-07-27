"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { homePorPapel } from "@/lib/roles";

export default function HomePage() {
  const { usuario, carregando } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (carregando) return;
    router.replace(usuario ? homePorPapel(usuario.papel) : "/login");
  }, [usuario, carregando, router]);

  return null;
}
