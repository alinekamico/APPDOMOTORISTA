"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useRequireRole } from "@/lib/roles";
import { useFetch } from "@/lib/use-fetch";
import { apiFetch, ApiError } from "@/lib/api-client";

type TipoOcorrencia = { id: number; descricao: string };

export function OcorrenciaForm({ romaneioId }: { romaneioId: number }) {
  const { carregando: carregandoAuth } = useRequireRole(["motorista"]);
  const router = useRouter();
  const { data: tipos } = useFetch<TipoOcorrencia[]>("/tipos-ocorrencia?categoria=problema_romaneio");

  const [statusAlvo, setStatusAlvo] = useState<"romaneio_incompleto" | "romaneio_com_problema">("romaneio_com_problema");
  const [tipoOcorrenciaId, setTipoOcorrenciaId] = useState("");
  const [observacao, setObservacao] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function handleEnviar(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    if (!tipoOcorrenciaId) return setErro("Selecione o motivo.");
    if (!observacao) return setErro("Descreva o que aconteceu.");

    setEnviando(true);
    try {
      await apiFetch(`/romaneios/${romaneioId}/reportar-problema`, {
        method: "POST",
        body: { status: statusAlvo, tipo_ocorrencia_id: Number(tipoOcorrenciaId), observacao },
      });
      router.push("/minha-rota");
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível registrar a ocorrência.");
    } finally {
      setEnviando(false);
    }
  }

  if (carregandoAuth) return null;

  return (
    <form onSubmit={handleEnviar} className="flex flex-col gap-4">
      <div>
        <h1 className="text-lg font-semibold text-kami-charcoal">Reportar problema no romaneio</h1>
        <p className="text-sm text-kami-charcoal-light">
          Use isso apenas quando não for possível continuar a rota normalmente.
        </p>
      </div>

      <div className="flex flex-col gap-2">
        <label className="flex items-start gap-2 rounded-lg border border-black/10 p-3 text-sm">
          <input
            type="radio"
            name="status"
            checked={statusAlvo === "romaneio_incompleto"}
            onChange={() => setStatusAlvo("romaneio_incompleto")}
            className="mt-0.5"
          />
          <span>
            <strong>Romaneio incompleto</strong> — entreguei parte dos pedidos, mas uma pane no veículo ou
            problema de saúde me impede de continuar.
          </span>
        </label>
        <label className="flex items-start gap-2 rounded-lg border border-black/10 p-3 text-sm">
          <input
            type="radio"
            name="status"
            checked={statusAlvo === "romaneio_com_problema"}
            onChange={() => setStatusAlvo("romaneio_com_problema")}
            className="mt-0.5"
          />
          <span>
            <strong>Romaneio com problema</strong> — outra ocorrência grave (acidente, furto/roubo, etc.).
          </span>
        </label>
      </div>

      <label className="flex flex-col gap-1 text-sm">
        Motivo
        <select
          required
          value={tipoOcorrenciaId}
          onChange={(e) => setTipoOcorrenciaId(e.target.value)}
          className="rounded-lg border border-black/10 px-3 py-2 outline-none focus:border-kami-red"
        >
          <option value="">Selecione...</option>
          {tipos?.map((t) => (
            <option key={t.id} value={t.id}>
              {t.descricao}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col gap-1 text-sm">
        Descreva o que aconteceu
        <textarea
          required
          value={observacao}
          onChange={(e) => setObservacao(e.target.value)}
          rows={4}
          className="rounded-lg border border-black/10 px-3 py-2 outline-none focus:border-kami-red"
        />
      </label>

      {erro && <p className="text-sm text-kami-red">{erro}</p>}

      <button
        type="submit"
        disabled={enviando}
        className="rounded-xl bg-kami-charcoal px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
      >
        {enviando ? "Enviando..." : "Confirmar ocorrência"}
      </button>
    </form>
  );
}
