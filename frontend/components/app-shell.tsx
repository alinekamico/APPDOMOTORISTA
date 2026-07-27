"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth, type Papel } from "@/lib/auth-context";

function IconRomaneios() {
  return (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" className="h-5 w-5">
      <rect x="2.5" y="3.5" width="4" height="13" rx="1" />
      <rect x="8" y="3.5" width="4" height="8" rx="1" />
      <rect x="13.5" y="3.5" width="4" height="10.5" rx="1" />
    </svg>
  );
}

function IconTransportadoras() {
  return (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" className="h-5 w-5">
      <path d="M3 16.5V5.5a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v11" strokeLinejoin="round" />
      <path d="M11 8.5h4a1 1 0 0 1 1 1v7" strokeLinejoin="round" />
      <path d="M1.5 16.5h17" />
      <path d="M5.5 7.5h1M5.5 10.5h1M5.5 13.5h1" />
    </svg>
  );
}

function IconOcorrencias() {
  return (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" className="h-5 w-5">
      <path d="M10 2.5 18 16.5H2Z" strokeLinejoin="round" />
      <path d="M10 8v3.5" strokeLinecap="round" />
      <circle cx="10" cy="13.8" r="0.9" fill="currentColor" stroke="none" />
    </svg>
  );
}

function IconVeiculos() {
  return (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" className="h-5 w-5">
      <path d="M2 12.5V6a1 1 0 0 1 1-1h7v7.5" strokeLinejoin="round" />
      <path d="M10 8.5h4.5l2.5 3v1h-2" strokeLinejoin="round" />
      <path d="M2 12.5h1.5" />
      <circle cx="6" cy="13.5" r="1.6" />
      <circle cx="14.5" cy="13.5" r="1.6" />
    </svg>
  );
}

function IconMotoristas() {
  return (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" className="h-5 w-5">
      <circle cx="10" cy="6.5" r="3" />
      <path d="M3.5 17c0-3.3 2.9-6 6.5-6s6.5 2.7 6.5 6" strokeLinecap="round" />
    </svg>
  );
}

function IconMinhaRota() {
  return (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" className="h-5 w-5">
      <path d="M10 18s6-5.5 6-10a6 6 0 0 0-12 0c0 4.5 6 10 6 10Z" strokeLinejoin="round" />
      <circle cx="10" cy="8" r="2" />
    </svg>
  );
}

const NAV_ITEMS: { href: string; label: string; papeis: Papel[]; Icon: () => React.JSX.Element }[] = [
  { href: "/romaneios", label: "Romaneios", papeis: ["kami_admin", "transportadora_admin"], Icon: IconRomaneios },
  { href: "/transportadoras", label: "Transportadoras", papeis: ["kami_admin"], Icon: IconTransportadoras },
  { href: "/ocorrencias", label: "Ocorrências", papeis: ["kami_admin"], Icon: IconOcorrencias },
  { href: "/veiculos", label: "Veículos", papeis: ["kami_admin", "transportadora_admin"], Icon: IconVeiculos },
  { href: "/motoristas", label: "Motoristas", papeis: ["kami_admin", "transportadora_admin"], Icon: IconMotoristas },
  { href: "/minha-rota", label: "Minha rota", papeis: ["motorista"], Icon: IconMinhaRota },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const { usuario, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const [menuAberto, setMenuAberto] = useState(false);

  const itensVisiveis = usuario ? NAV_ITEMS.filter((item) => item.papeis.includes(usuario.papel)) : [];

  function handleLogout() {
    logout();
    router.push("/login");
  }

  const conteudoSidebar = (
    <div className="flex h-full flex-col bg-kami-charcoal text-white">
      <Link href="/" className="flex items-center gap-2 px-4 py-4">
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-kami-red text-sm font-bold text-white">
          K
        </span>
        <span className="text-sm font-semibold text-white">KAMI CO. · Romaneios</span>
      </Link>

      <nav className="flex flex-1 flex-col gap-1 px-3 py-2">
        {itensVisiveis.map((item) => {
          const ativo = pathname === item.href || pathname?.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setMenuAberto(false)}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition ${
                ativo ? "bg-kami-red text-white" : "text-white/70 hover:bg-white/10 hover:text-white"
              }`}
            >
              <item.Icon />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-white/10 px-4 py-3">
        {usuario && <p className="mb-2 truncate text-sm text-white/70">{usuario.nome}</p>}
        <button
          onClick={handleLogout}
          className="w-full rounded-lg px-3 py-2 text-left text-sm font-medium text-white/70 transition hover:bg-white/10 hover:text-white"
        >
          Sair
        </button>
      </div>
    </div>
  );

  return (
    <div className="flex min-h-screen">
      {/* Sidebar fixa (desktop) */}
      <aside className="hidden w-60 shrink-0 sm:block">{conteudoSidebar}</aside>

      {/* Topbar + drawer (mobile) */}
      <div className="flex flex-1 flex-col">
        <header className="flex items-center gap-3 bg-kami-charcoal px-4 py-3 sm:hidden">
          <button
            onClick={() => setMenuAberto(true)}
            aria-label="Abrir menu"
            className="flex h-9 w-9 items-center justify-center rounded-lg text-white hover:bg-white/10"
          >
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-5 w-5">
              <path d="M3 5.5h14M3 10h14M3 14.5h14" strokeLinecap="round" />
            </svg>
          </button>
          <span className="text-sm font-semibold text-white">KAMI CO. · Romaneios</span>
        </header>

        {menuAberto && (
          <div className="fixed inset-0 z-50 sm:hidden">
            <div className="absolute inset-0 bg-black/30" onClick={() => setMenuAberto(false)} />
            <aside className="absolute inset-y-0 left-0 w-64 shadow-xl">{conteudoSidebar}</aside>
          </div>
        )}

        <main className="flex-1 bg-zinc-50 px-4 py-6 sm:px-6">{children}</main>
      </div>
    </div>
  );
}
