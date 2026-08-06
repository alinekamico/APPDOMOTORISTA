export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-white px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center gap-2">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-kami-charcoal text-xl font-bold text-white">
            K
            <span className="ml-0.5 inline-block h-2 w-2 rounded-full bg-kami-red" />
          </div>
          <p className="text-sm font-medium tracking-wide text-kami-charcoal-light">
            KAMI CO. · Romaneios
          </p>
        </div>
        <div className="rounded-2xl border border-black/10 bg-white p-6 shadow-sm">{children}</div>
      </div>
    </div>
  );
}
