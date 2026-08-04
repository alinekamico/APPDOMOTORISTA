"use client";

import Link from "next/link";
import dynamic from "next/dynamic";
import { useRequireRole } from "@/lib/roles";
import { useFetch } from "@/lib/use-fetch";
import { apiFetch, ApiError } from "@/lib/api-client";
import { useGeolocation } from "@/hooks/useGeolocation";
import { linkGoogleMaps, linkWaze } from "@/lib/navegacao";
import { calcularDistanciaKm, formatarDistancia } from "@/lib/distancia";
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

type TipoOcorrencia = { id: number; descricao: string; exige_observacao: boolean };

const LABEL_ENTREGA: Record<string, string> = {
  pendente: "Pendente",
  em_rota: "Em rota",
  entregue: "Entregue",
  nao_entregue: "Não entregue",
  cancelado: "Cancelado",
};

const MENSAGEM_FINALIZADO: Record<string, string> = {
  concluido: "Romaneio concluído — todos os pedidos foram entregues.",
  romaneio_incompleto: "Romaneio incompleto — há pedido(s) não entregues. A KAMI vai avaliar as pendências.",
  romaneio_com_problema: "Romaneio com problema reportado. A KAMI vai avaliar.",
};

export function RomaneioExecucaoHub({ romaneioId }: { romaneioId: number }) {
  const { carregando: carregandoAuth } = useRequireRole(["motorista"]);
  const { data: romaneio, carregando, erro, recarregar } = useFetch<RomaneioExecucao>(
    carregandoAuth ? null : `/romaneios/${romaneioId}`
  );
  const { data: tiposNaoEntrega } = useFetch<TipoOcorrencia[]>("/tipos-ocorrencia?categoria=nao_entrega");
  const { data: tiposProblema } = useFetch<TipoOcorrencia[]>("/tipos-ocorrencia?categoria=problema_romaneio");
  const [enviando, setEnviando] = useState(false);
  const [acaoErro, setAcaoErro] = useState<string | null>(null);
  const [mostrarFormFinalizar, setMostrarFormFinalizar] = useState(false);
  const [tipoOcorrenciaFinalId, setTipoOcorrenciaFinalId] = useState("");
  const [observacaoFinal, setObservacaoFinal] = useState("");
  const [respostaContinuarHoje, setRespostaContinuarHoje] = useState<"sim" | "nao" | "">("");
  const { coordenadas, capturar } = useGeolocation();

  const tipoSelecionadoEhProblema = tiposProblema?.some((t) => String(t.id) === tipoOcorrenciaFinalId) ?? false;

  function resetarFormFinalizar() {
    setMostrarFormFinalizar(false);
    setTipoOcorrenciaFinalId("");
    setObservacaoFinal("");
    setRespostaContinuarHoje("");
  }

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

  async function handleReordenarRota() {
    setAcaoErro(null);
    setEnviando(true);
    try {
      const posicao = await capturar();
      if (!posicao) {
        setAcaoErro("Não foi possível obter sua localização atual.");
        return;
      }
      await apiFetch(`/romaneios/${romaneioId}/resequenciar`, {
        method: "POST",
        body: { posicao_lat: posicao.lat, posicao_lng: posicao.lng },
      });
      recarregar();
    } catch (err) {
      setAcaoErro(err instanceof ApiError ? err.detail : "Não foi possível reordenar a rota.");
    } finally {
      setEnviando(false);
    }
  }

  async function finalizar(body: { tipo_ocorrencia_id?: number; observacao?: string }) {
    setAcaoErro(null);
    setEnviando(true);
    try {
      await apiFetch(`/romaneios/${romaneioId}/finalizar`, { method: "POST", body });
      recarregar();
    } catch (err) {
      setAcaoErro(err instanceof ApiError ? err.detail : "Não foi possível finalizar o romaneio.");
    } finally {
      setEnviando(false);
    }
  }

  function handleCliqueFinalizar(pendentes: Pedido[]) {
    if (pendentes.length === 0) {
      finalizar({});
      return;
    }
    setMostrarFormFinalizar(true);
  }

  function handleRespostaContinuarHoje(resposta: "sim" | "nao") {
    if (resposta === "sim") {
      // Segue rodando normalmente — o romaneio continua em trânsito, nada é enviado.
      resetarFormFinalizar();
      return;
    }
    setRespostaContinuarHoje("nao");
  }

  function handleConfirmarFinalizarComPendentes() {
    setAcaoErro(null);
    if (!tipoOcorrenciaFinalId) return setAcaoErro("Selecione o motivo dos pedidos não entregues.");
    const tipo = tiposNaoEntrega?.find((t) => String(t.id) === tipoOcorrenciaFinalId);
    if (tipo?.exige_observacao && !observacaoFinal) return setAcaoErro("Este motivo exige uma descrição.");
    finalizar({ tipo_ocorrencia_id: Number(tipoOcorrenciaFinalId), observacao: observacaoFinal || undefined });
  }

  function handleConfirmarProblemaRomaneio() {
    setAcaoErro(null);
    const tipo = tiposProblema?.find((t) => String(t.id) === tipoOcorrenciaFinalId);
    if (tipo?.exige_observacao && !observacaoFinal) return setAcaoErro("Descreva o que aconteceu.");
    finalizar({ tipo_ocorrencia_id: Number(tipoOcorrenciaFinalId), observacao: observacaoFinal || undefined });
  }

  if (carregandoAuth || carregando) return <p className="text-sm text-kami-charcoal-light">Carregando...</p>;
  if (erro) return <p className="text-sm text-kami-red">{erro}</p>;
  if (!romaneio) return null;

  const pedidosOrdenados = romaneio.pedidos.slice().sort((a, b) => a.sequencia_atual - b.sequencia_atual);
  const pendentes = pedidosOrdenados.filter((p) => p.status_entrega === "pendente" || p.status_entrega === "em_rota");
  const proximoPendente = pendentes[0];

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
        <>
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
          <button
            onClick={handleReordenarRota}
            disabled={enviando}
            className="rounded-lg border border-dashed border-kami-red/40 px-3 py-2 text-center text-sm font-medium text-kami-red disabled:opacity-60"
          >
            {enviando ? "Recalculando..." : "Reordenar rota a partir da minha posição"}
          </button>
        </>
      )}

      {romaneio.status === "em_transito" && !mostrarFormFinalizar && (
        <button
          onClick={() => handleCliqueFinalizar(pendentes)}
          disabled={enviando}
          className="rounded-xl bg-kami-red px-4 py-3 text-center text-sm font-medium text-white disabled:opacity-60"
        >
          {enviando ? "Finalizando..." : "Finalizar romaneio"}
        </button>
      )}

      {romaneio.status === "em_transito" && mostrarFormFinalizar && (
        <div className="flex flex-col gap-3 rounded-xl border border-kami-red/30 bg-kami-red/5 p-3">
          <p className="text-sm font-medium text-kami-charcoal">
            {pendentes.length} pedido(s) ainda não confirmado(s):
          </p>
          <ul className="flex flex-col gap-1 text-xs text-kami-charcoal-light">
            {pendentes.map((p) => (
              <li key={p.id}>
                {p.sequencia_atual}. {p.cliente_nome} — {p.cliente_endereco}
              </li>
            ))}
          </ul>

          <label className="flex flex-col gap-1 text-sm">
            Motivo
            <select
              value={tipoOcorrenciaFinalId}
              onChange={(e) => {
                setTipoOcorrenciaFinalId(e.target.value);
                setRespostaContinuarHoje("");
                setObservacaoFinal("");
              }}
              className="rounded-lg border border-black/10 px-3 py-2 outline-none focus:border-kami-red"
            >
              <option value="">Selecione...</option>
              <optgroup label="Pedido não entregue">
                {tiposNaoEntrega?.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.descricao}
                  </option>
                ))}
              </optgroup>
              <optgroup label="Problema no romaneio">
                {tiposProblema?.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.descricao}
                  </option>
                ))}
              </optgroup>
            </select>
          </label>

          {tipoOcorrenciaFinalId && tipoSelecionadoEhProblema ? (
            <>
              <p className="text-sm font-medium text-kami-charcoal">
                Você vai conseguir continuar as entregas hoje?
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => handleRespostaContinuarHoje("sim")}
                  className={`flex-1 rounded-lg border px-3 py-2 text-sm font-medium ${
                    respostaContinuarHoje === "sim"
                      ? "border-kami-red bg-kami-red/10 text-kami-red"
                      : "border-black/10 text-kami-charcoal"
                  }`}
                >
                  Sim, vou continuar
                </button>
                <button
                  onClick={() => handleRespostaContinuarHoje("nao")}
                  className={`flex-1 rounded-lg border px-3 py-2 text-sm font-medium ${
                    respostaContinuarHoje === "nao"
                      ? "border-kami-red bg-kami-red/10 text-kami-red"
                      : "border-black/10 text-kami-charcoal"
                  }`}
                >
                  Não, preciso parar
                </button>
              </div>

              {respostaContinuarHoje === "nao" && (
                <>
                  <p className="text-xs text-kami-charcoal-light">
                    O romaneio vai passar pra responsabilidade da transportadora, que vai reagendar as
                    entregas restantes pro dia seguinte ou pedir que você devolva a mercadoria.
                  </p>
                  <label className="flex flex-col gap-1 text-sm">
                    Detalhes
                    <textarea
                      value={observacaoFinal}
                      onChange={(e) => setObservacaoFinal(e.target.value)}
                      rows={3}
                      placeholder="Descreva o que aconteceu"
                      className="rounded-lg border border-black/10 px-3 py-2 outline-none focus:border-kami-red"
                    />
                  </label>
                  <div className="flex gap-2">
                    <button
                      onClick={resetarFormFinalizar}
                      disabled={enviando}
                      className="flex-1 rounded-lg border border-black/10 px-3 py-2 text-sm font-medium text-kami-charcoal"
                    >
                      Cancelar
                    </button>
                    <button
                      onClick={handleConfirmarProblemaRomaneio}
                      disabled={enviando}
                      className="flex-1 rounded-lg bg-kami-red px-3 py-2 text-sm font-medium text-white disabled:opacity-60"
                    >
                      {enviando ? "Enviando..." : "Confirmar e transferir pra transportadora"}
                    </button>
                  </div>
                </>
              )}
            </>
          ) : (
            <>
              <label className="flex flex-col gap-1 text-sm">
                Detalhes
                <textarea
                  value={observacaoFinal}
                  onChange={(e) => setObservacaoFinal(e.target.value)}
                  rows={3}
                  placeholder="Descreva o que aconteceu com esses pedidos"
                  className="rounded-lg border border-black/10 px-3 py-2 outline-none focus:border-kami-red"
                />
              </label>

              <div className="flex gap-2">
                <button
                  onClick={resetarFormFinalizar}
                  disabled={enviando}
                  className="flex-1 rounded-lg border border-black/10 px-3 py-2 text-sm font-medium text-kami-charcoal"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleConfirmarFinalizarComPendentes}
                  disabled={enviando}
                  className="flex-1 rounded-lg bg-kami-red px-3 py-2 text-sm font-medium text-white disabled:opacity-60"
                >
                  {enviando ? "Finalizando..." : "Confirmar e finalizar"}
                </button>
              </div>
            </>
          )}
        </div>
      )}

      {MENSAGEM_FINALIZADO[romaneio.status] && (
        <p className="rounded-xl bg-zinc-100 px-4 py-3 text-center text-sm text-kami-charcoal-light">
          {MENSAGEM_FINALIZADO[romaneio.status]}
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
          const distanciaKm =
            coordenadas && pedido.cliente_lat !== null && pedido.cliente_lng !== null
              ? calcularDistanciaKm(coordenadas, { lat: pedido.cliente_lat, lng: pedido.cliente_lng })
              : null;
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
                  {(pedido.peso_kg || pedido.qtd_volumes || distanciaKm !== null) && (
                    <p className="text-xs text-kami-charcoal-light">
                      {pedido.peso_kg ? `${pedido.peso_kg} kg` : null}
                      {pedido.peso_kg && pedido.qtd_volumes ? " · " : null}
                      {pedido.qtd_volumes ? `${pedido.qtd_volumes} ${pedido.especie_volume ?? "volume(s)"}` : null}
                      {(pedido.peso_kg || pedido.qtd_volumes) && distanciaKm !== null ? " · " : null}
                      {distanciaKm !== null ? `${formatarDistancia(distanciaKm)} daqui` : null}
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
