"use client";

import Link from "next/link";

export default function RomaneioExecucaoLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="mx-auto flex min-h-screen w-full max-w-md flex-col bg-white">
      <header className="flex items-center gap-2 border-b border-black/10 px-4 py-3">
        <Link href="/minha-rota" className="text-sm font-medium text-kami-charcoal-light hover:text-kami-red">
          ← Minha rota
        </Link>
      </header>
      <main className="flex-1 px-4 py-5">{children}</main>
    </div>
  );
}
