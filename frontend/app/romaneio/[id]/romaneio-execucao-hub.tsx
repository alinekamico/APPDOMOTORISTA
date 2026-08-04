"use client";

import Link from "next/link";
import dynamic from "next/dynamic";
import { useRequireRole } from "@/lib/roles";
import { useFetch } from "@/lib/use-fetch";
import { apiFetch, ApiError } from "@/lib/api-client";
import { useGeolocation } from "@/hooks/useGeolocation";
import { linkGoogleMaps, linkWaze } from "@/lib/navegacao";
import { useEffect, useState } from "react";

// Leaflet usa `window` na inicialização — precisa ficar fora do SSR.
const MapaRota = dynamic(() => import("@/components/mapa/MapaRota").then((m) => m.MapaRota), {
  ssr: false,
  loading: () => <div className="h-56 w-full animate-pulse rounded-xl bg-zinc-100" />,
});

type Pedido = {
  id: number;
  sequencia_atual: number;
  status_entrega: "pendente" | "em_rota" | "entregue" | "nao_entregue" | "cancelado";
  cliente_nome: string;
  cliente_endereco: string;
  cliente_lat: number | null;
  cliente_lng: number | null;
  peso_kg: number | null;
  qtd_volumes: number | null;
  especie_volume: string | null;
};

type RomaneioExecucao = {
  id: number;
  codigo: string;
  status: string;
  pedidos: Pedido[];
};

const LABEL_ENTREGA: Record<string, string> = {
  pendente: "Pendente",
  em_rota: "Em rota",
  entregue: "Entregue",
  nao_entregue: "Não entregue",
  cancelado: "Cancelado",
};

export function RomaneioExecucaoHub({ romaneioId }: { romaneioId: number }) {
  const { carregando: carregandoAuth } = useRequireRole(["motorista"]);
  const { data: romaneio, carregando, erro, recarregar } = useFetch<RomaneioExecucao>(
    carregandoAuth ? null : `/romaneios/${romaneioId}`
  );
  const [enviando, setEnviando] = useState(false);
  const [acaoErro, setAcaoErro] = useState<string | null>(null);
  const { coordenadas, capturar } = useGeolocation();

  useEffect(() => {
    if (romaneio?.status === "em_transito") capturar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [romaneio?.status]);

  async function handleIniciarRota() {
    setAcaoErro(null);
    setEnviando(true);
    try {
      await apiFetch(`/romaneios/${romaneioId}/iniciar-rota`, { method: "POST" });
      recarregar();
    } catch (err) {
      setAcaoErro(err instanceof ApiError ? err.detail : "Não foi possível iniciar a rota.");
    } finally {
      setEnviando(false);
    }
  }

  if (carregandoAuth || carregando) return <p className="text-sm text-kami-charcoal-light">Carregando...</p>;
  if (erro) return <p className="text-sm text-kami-red">{erro}</p>;
  if (!romaneio) return null;

  const pedidosOrdenados = romaneio.pedidos.slice().sort((a, b) => a.sequencia_atual - b.sequencia_atual);
  const proximoPendente = pedidosOrdenados.find((p) => p.status_entrega === "pendente" || p.status_entrega === "em_rota");

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-lg font-semibold text-kami-charcoal">{romaneio.codigo}</h1>
        <p className="text-sm text-kami-charcoal-light">{pedidosOrdenados.length} pedidos</p>
      </div>

      {acaoErro && <p className="text-sm text-kami-red">{acaoErro}</p>}

      {romaneio.status === "carregamento" && (
        <Link
          href={`/romaneio/${romaneio.id}/carregamento`}
          className="rounded-xl bg-kami-red px-4 py-3 text-center text-sm font-medium text-white"
        >
          Registrar fim do carregamento
        </Link>
      )}

      {romaneio.status === "inicio_rota" && (
        <button
          onClick={handleIniciarRota}
          disabled={enviando}
          className="rounded-xl bg-kami-red px-4 py-3 text-center text-sm font-medium text-white disabled:opacity-60"
        >
          {enviando ? "Iniciando..." : "Iniciar rota"}
        </button>
      )}

      {romaneio.status === "em_transito" && (
        <MapaRota
          pedidos={pedidosOrdenados
            .filter((p) => p.cliente_lat !== null && p.cliente_lng !== null)
            .map((p) => ({
              id: p.id,
              sequencia_atual: p.sequencia_atual,
              cliente_nome: p.cliente_nome,
              lat: p.cliente_lat as number,
              lng: p.cliente_lng as number,
              entregue: p.status_entrega === "entregue" || p.status_entrega === "nao_entregue",
            }))}
          posicaoAtual={coordenadas}
        />
      )}

      {romaneio.status === "em_transito" && proximoPendente && (
        <div className="flex gap-2">
          <a
            href={linkGoogleMaps(proximoPendente)}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 rounded-lg border border-black/10 bg-white px-3 py-2 text-center text-sm font-medium text-kami-charcoal"
          >
            Abrir no Google Maps
          </a>
          <a
            href={linkWaze(proximoPendente)}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 rounded-lg border border-black/10 bg-white px-3 py-2 text-center text-sm font-medium text-kami-charcoal"
          >
            Abrir no Waze
          </a>
        </div>
      )}

      {["concluido", "romaneio_incompleto", "romaneio_com_problema"].includes(romaneio.status) && (
        <p className="rounded-xl bg-zinc-100 px-4 py-3 text-center text-sm text-kami-charcoal-light">
          Este romaneio já foi finalizado.
        </p>
      )}

      {["carregamento", "inicio_rota", "em_transito"].includes(romaneio.status) && (
        <Link
          href={`/romaneio/${romaneio.id}/ocorrencia`}
          className="text-center text-xs font-medium text-kami-charcoal-light hover:text-kami-red"
        >
          Não consigo continuar — reportar problema no romaneio
        </Link>
      )}

      <div className="flex flex-col gap-2">
        {pedidosOrdenados.map((pedido) => {
          const finalizado = pedido.status_entrega === "entregue" || pedido.status_entrega === "nao_entregue";
          const conteudo = (
            <div className="flex items-center gap-3 rounded-xl border border-black/10 bg-white p-3">
              <span
                className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${
                  finalizado ? "bg-zinc-100 text-kami-charcoal-light" : "bg-kami-red/10 text-kami-red"
                }`}
              >
                {pedido.sequencia_atual}
              </span>
              <div className="flex flex-1 items-center justify-between gap-2">
                <div>
                  <p className="text-sm font-medium text-kami-charcoal">{pedido.cliente_nome}</p>
                  <p className="text-xs text-kami-charcoal-light">{pedido.cliente_endereco}</p>
                  {(pedido.peso_kg || pedido.qtd_volumes) && (
                    <p className="text-xs text-kami-charcoal-light">
                      {pedido.peso_kg ? `${pedido.peso_kg} kg` : null}
                      {pedido.peso_kg && pedido.qtd_volumes ? " · " : null}
                      {pedido.qtd_volumes ? `${pedido.qtd_volumes} ${pedido.especie_volume ?? "volume(s)"}` : null}
                    </p>
                  )}
                </div>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                    pedido.status_entrega === "entregue"
                      ? "bg-green-100 text-green-700"
                      : pedido.status_entrega === "nao_entregue"
                        ? "bg-zinc-200 text-zinc-600"
                        : "bg-kami-red/10 text-kami-red"
                  }`}
                >
                  {LABEL_ENTREGA[pedido.status_entrega]}
                </span>
              </div>
            </div>
          );

          if (romaneio.status === "em_transito" && !finalizado) {
            return (
              <Link key={pedido.id} href={`/romaneio/${romaneio.id}/entrega/${pedido.id}`}>
                {conteudo}
              </Link>
            );
          }
          return <div key={pedido.id}>{conteudo}</div>;
        })}
      </div>
    </div>
  );
}
