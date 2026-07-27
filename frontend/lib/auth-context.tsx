"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { apiFetch, ApiError, getStoredToken, setStoredToken } from "@/lib/api-client";

export type Papel = "kami_admin" | "transportadora_admin" | "motorista";

export type Usuario = {
  id: number;
  nome: string;
  email: string;
  papel: Papel;
  transportadora_id: number | null;
  departamento: string | null;
};

type AuthContextValue = {
  usuario: Usuario | null;
  carregando: boolean;
  login: (email: string, senha: string) => Promise<Usuario>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [carregando, setCarregando] = useState(true);

  const carregarUsuarioAtual = useCallback(async () => {
    const token = getStoredToken();
    if (!token) {
      setUsuario(null);
      setCarregando(false);
      return;
    }
    try {
      const me = await apiFetch<Usuario>("/auth/me");
      setUsuario(me);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setStoredToken(null);
      }
      setUsuario(null);
    } finally {
      setCarregando(false);
    }
  }, []);

  useEffect(() => {
    carregarUsuarioAtual();
  }, [carregarUsuarioAtual]);

  const login = useCallback(async (email: string, senha: string) => {
    const resposta = await apiFetch<{
      access_token: string;
      papel: Papel;
      nome: string;
      transportadora_id: number | null;
    }>("/auth/login", { method: "POST", body: { email, senha }, auth: false });

    setStoredToken(resposta.access_token);
    const me = await apiFetch<Usuario>("/auth/me");
    setUsuario(me);
    return me;
  }, []);

  const logout = useCallback(() => {
    setStoredToken(null);
    setUsuario(null);
  }, []);

  const value = useMemo(
    () => ({ usuario, carregando, login, logout }),
    [usuario, carregando, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth precisa estar dentro de um AuthProvider");
  return context;
}
