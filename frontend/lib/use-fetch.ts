"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch, ApiError } from "@/lib/api-client";

export function useFetch<T>(path: string | null, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(true);

  const recarregar = useCallback(async () => {
    if (!path) return;
    setCarregando(true);
    setErro(null);
    try {
      const resultado = await apiFetch<T>(path);
      setData(resultado);
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Erro ao carregar dados.");
    } finally {
      setCarregando(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path, ...deps]);

  useEffect(() => {
    recarregar();
  }, [recarregar]);

  return { data, erro, carregando, recarregar };
}
