"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useRequireRole } from "@/lib/roles";
import { useFetch } from "@/lib/use-fetch";
import { apiFetch, ApiError } from "@/lib/api-client";
import { CameraCapture } from "@/components/entrega/CameraCapture";

type FotoCarregamento = { id: number; foto_url: string; criado_em: string };
type RomaneioCarregamento = { id: number; fotos_carregamento: FotoCarregamento[] };

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

export function CarregamentoForm({ romaneioId }: { romaneioId: number }) {
  const { carregando: carregandoAuth } = useRequireRole(["motorista"]);
  const { data: romaneio, carregando, recarregar } = useFetch<RomaneioCarregamento>(
    carregandoAuth ? null : `/romaneios/${romaneioId}`
  );
  const [enviandoFoto, setEnviandoFoto] = useState(false);
  const [finalizando, setFinalizando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const router = useRouter();

  async function handleCapturar(arquivo: File) {
    setErro(null);
    setEnviandoFoto(true);
    try {
      const formData = new FormData();
      formData.append("foto", arquivo);
      await apiFetch(`/romaneios/${romaneioId}/carregamento/foto`, {
        method: "POST",
        body: formData,
        isFormData: true,
      });
      recarregar();
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível registrar a foto.");
    } finally {
      setEnviandoFoto(false);
    }
  }

  async function handleFinalizar() {
    setErro(null);
    setFinalizando(true);
    try {
      await apiFetch(`/romaneios/${romaneioId}/carregamento/finalizar`, { method: "POST" });
      router.push(`/romaneio/${romaneioId}`);
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível finalizar o carregamento.");
    } finally {
      setFinalizando(false);
    }
  }

  if (carregandoAuth || carregando) return null;

  const fotos = romaneio?.fotos_carregamento ?? [];

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-lg font-semibold text-kami-charcoal">Fim do carregamento</h1>
      <p className="text-sm text-kami-charcoal-light">
        Registre quantas fotos precisar mostrando a carga finalizada no veículo. Quando terminar,
        confirme o fim do carregamento para seguir para a rota.
      </p>

      <CameraCapture label="Adicionar foto do carregamento" onCapture={handleCapturar} />
      {enviandoFoto && <p className="text-xs text-kami-charcoal-light">Enviando foto...</p>}

      {fotos.length > 0 && (
        <div className="flex flex-col gap-2">
          <span className="text-sm font-medium text-kami-charcoal">
            Fotos registradas ({fotos.length})
          </span>
          <div className="grid grid-cols-3 gap-2">
            {fotos.map((foto) => (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                key={foto.id}
                src={`${API_BASE_URL}${foto.foto_url}`}
                alt="Foto do carregamento"
                className="h-24 w-full rounded-lg object-cover"
              />
            ))}
          </div>
        </div>
      )}

      {erro && <p className="text-sm text-kami-red">{erro}</p>}

      <button
        onClick={handleFinalizar}
        disabled={finalizando || fotos.length === 0}
        className="rounded-xl bg-kami-red px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
      >
        {finalizando
          ? "Finalizando..."
          : fotos.length === 0
            ? "Registre ao menos uma foto para finalizar"
            : "OK, carregamento finalizado"}
      </button>
    </div>
  );
}
