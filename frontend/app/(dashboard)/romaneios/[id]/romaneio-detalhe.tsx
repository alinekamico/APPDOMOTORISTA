"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useRequireRole } from "@/lib/roles";
import { useFetch } from "@/lib/use-fetch";
import { apiFetch, ApiError } from "@/lib/api-client";
import { COLUNAS } from "@/components/kanban/types";
import { HistoricoTimeline } from "@/components/romaneio/HistoricoTimeline";

type Pedido = {
  id: number;
  sequencia_original: number;
  sequencia_atual: number;
  status_entrega: string;
  cliente_nome: string;
  cliente_endereco: string;
  cliente_whatsapp: string | null;
  cliente_email: string | null;
  peso_kg: number | null;
  qtd_volumes: number | null;
  especie_volume: string | null;
  dt_entrega_solicitada: string | null;
  entregue_em: string | null;
};

type FotoCarregamento = { id: number; foto_url: string; criado_em: string };

type RomaneioDetalheType = {
  id: number;
  codigo: string;
  transportadora_id: number | null;
  transportadora_nome: string | null;
  transportadora_cnpj_externo: string | null;
  veiculo_id: number | null;
  veiculo_placa: string | null;
  motorista_id: number | null;
  motorista_nome: string | null;
  status: string;
  qtd_caixas: number | null;
  qtd_pedidos: number | null;
  peso_total: number | null;
  tipo_veiculo_sugerido: string | null;
  data_saida_prevista: string | null;
  empresa_nome: string | null;
  empresa_uf: string | null;
  romaneio_origem_id: number | null;
  romaneio_origem_codigo: string | null;
  fotos_carregamento: FotoCarregamento[];
  pedidos: Pedido[];
};

type Veiculo = { id: number; placa: string; tipo: string };
type Motorista = { id: number; nome: string };
type Transportadora = { id: number; nome_fantasia: string };

const LABEL_STATUS: Record<string, string> = Object.fromEntries(
  COLUNAS.map((c) => [c.status, c.titulo])
);

export function RomaneioDetalhe({ romaneioId }: { romaneioId: number }) {
  const router = useRouter();
  const { usuario, carregando: carregandoAuth } = useRequireRole([
    "kami_admin",
    "transportadora_admin",
    "motorista",
  ]);

  const { data: romaneio, carregando, erro, recarregar } = useFetch<RomaneioDetalheType>(
    carregandoAuth ? null : `/romaneios/${romaneioId}`
  );

  const podeAlocar = usuario?.papel === "transportadora_admin" && romaneio?.status === "definicao_transporte";
  const { data: veiculos } = useFetch<Veiculo[]>(podeAlocar ? "/veiculos" : null);
  const { data: motoristas } = useFetch<Motorista[]>(podeAlocar ? "/motoristas" : null);

  const podeTrocarTransportadora = usuario?.papel === "kami_admin" && romaneio?.status === "definicao_transporte";
  const podeDefinirTransportadora =
    usuario?.papel === "kami_admin" && romaneio?.status === "definicao_transportadora";
  const { data: transportadoras } = useFetch<Transportadora[]>(
    podeTrocarTransportadora || podeDefinirTransportadora ? "/transportadoras" : null
  );

  const [transportadoraEscolhidaId, setTransportadoraEscolhidaId] = useState("");
  const [definindoTransportadora, setDefinindoTransportadora] = useState(false);

  const [veiculoId, setVeiculoId] = useState("");
  const [motoristaId, setMotoristaId] = useState("");
  const [acaoErro, setAcaoErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [confirmandoAlocacao, setConfirmandoAlocacao] = useState(false);

  const [novaTransportadoraId, setNovaTransportadoraId] = useState("");
  const [trocandoTransportadora, setTrocandoTransportadora] = useState(false);

  const [mostrarDevolucao, setMostrarDevolucao] = useState(false);
  const [motivoDevolucao, setMotivoDevolucao] = useState("");

  const [mostrarNovoPedido, setMostrarNovoPedido] = useState(false);
  const [novoPedidoNome, setNovoPedidoNome] = useState("");
  const [novoPedidoEndereco, setNovoPedidoEndereco] = useState("");

  const [clonando, setClonando] = useState(false);
  const [mostrarHistorico, setMostrarHistorico] = useState(false);

  function handlePedirConfirmacaoAlocar(e: React.FormEvent) {
    e.preventDefault();
    if (!veiculoId || !motoristaId) return;
    setAcaoErro(null);
    setConfirmandoAlocacao(true);
  }

  async function handleConfirmarAlocar() {
    setAcaoErro(null);
    setEnviando(true);
    try {
      await apiFetch(`/romaneios/${romaneioId}/alocar`, {
        method: "POST",
        body: { veiculo_id: Number(veiculoId), motorista_id: Number(motoristaId) },
      });
      setConfirmandoAlocacao(false);
      recarregar();
    } catch (err) {
      setAcaoErro(err instanceof ApiError ? err.detail : "Não foi possível alocar veículo/motorista.");
    } finally {
      setEnviando(false);
    }
  }

  function handleCancelarConfirmacaoAlocar() {
    setConfirmandoAlocacao(false);
  }

  async function handleTrocarTransportadora(e: React.FormEvent) {
    e.preventDefault();
    if (!novaTransportadoraId) return;
    setAcaoErro(null);
    setTrocandoTransportadora(true);
    try {
      await apiFetch(`/romaneios/${romaneioId}/transportadora`, {
        method: "PATCH",
        body: { transportadora_id: Number(novaTransportadoraId) },
      });
      setNovaTransportadoraId("");
      recarregar();
    } catch (err) {
      setAcaoErro(err instanceof ApiError ? err.detail : "Não foi possível trocar a transportadora.");
    } finally {
      setTrocandoTransportadora(false);
    }
  }

  async function handleDefinirTransportadora(e: React.FormEvent) {
    e.preventDefault();
    if (!transportadoraEscolhidaId) return;
    setAcaoErro(null);
    setDefinindoTransportadora(true);
    try {
      await apiFetch(`/romaneios/${romaneioId}/definir-transportadora`, {
        method: "POST",
        body: { transportadora_id: Number(transportadoraEscolhidaId) },
      });
      setTransportadoraEscolhidaId("");
      recarregar();
    } catch (err) {
      setAcaoErro(err instanceof ApiError ? err.detail : "Não foi possível definir a transportadora.");
    } finally {
      setDefinindoTransportadora(false);
    }
  }

  async function handleAdicionarPedido(e: React.FormEvent) {
    e.preventDefault();
    setAcaoErro(null);
    setEnviando(true);
    try {
      const maiorSequencia = Math.max(0, ...(romaneio?.pedidos.map((p) => p.sequencia_atual) ?? [0]));
      await apiFetch(`/romaneios/${romaneioId}/pedidos`, {
        method: "POST",
        body: {
          pedidos: [{ sequencia: maiorSequencia + 1, cliente_nome: novoPedidoNome, cliente_endereco: novoPedidoEndereco }],
        },
      });
      setNovoPedidoNome("");
      setNovoPedidoEndereco("");
      setMostrarNovoPedido(false);
      recarregar();
    } catch (err) {
      setAcaoErro(err instanceof ApiError ? err.detail : "Não foi possível adicionar o pedido.");
    } finally {
      setEnviando(false);
    }
  }

  async function handleConfirmarConferencia() {
    setAcaoErro(null);
    setEnviando(true);
    try {
      await apiFetch(`/romaneios/${romaneioId}/confirmar-conferencia`, { method: "POST" });
      recarregar();
    } catch (err) {
      setAcaoErro(err instanceof ApiError ? err.detail : "Não foi possível confirmar a conferência.");
    } finally {
      setEnviando(false);
    }
  }

  async function handleDevolverParaTransporte() {
    setAcaoErro(null);
    setEnviando(true);
    try {
      await apiFetch(`/romaneios/${romaneioId}/devolver-para-transporte`, {
        method: "POST",
        body: { observacao: motivoDevolucao.trim() || null },
      });
      setMostrarDevolucao(false);
      setMotivoDevolucao("");
      recarregar();
    } catch (err) {
      setAcaoErro(err instanceof ApiError ? err.detail : "Não foi possível devolver o romaneio.");
    } finally {
      setEnviando(false);
    }
  }

  async function handleClonarPendentes() {
    setAcaoErro(null);
    setClonando(true);
    try {
      const novo = await apiFetch<{ id: number; codigo: string }>(`/romaneios/${romaneioId}/clonar-pendentes`, {
        method: "POST",
      });
      router.push(`/romaneios/${novo.id}`);
    } catch (err) {
      setAcaoErro(err instanceof ApiError ? err.detail : "Não foi possível reenviar os pedidos pendentes.");
    } finally {
      setClonando(false);
    }
  }

  if (carregandoAuth || carregando) return <p className="text-sm text-kami-charcoal-light">Carregando...</p>;
  if (erro) return <p className="text-sm text-kami-red">{erro}</p>;
  if (!romaneio) return null;

  return (
    <div className="mx-auto max-w-2xl">
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-lg font-semibold text-kami-charcoal">{romaneio.codigo}</h1>
          {romaneio.empresa_nome && (
            <p className="mt-0.5 inline-flex items-center gap-1 rounded-full bg-kami-charcoal/5 px-2 py-0.5 text-xs font-medium text-kami-charcoal">
              {romaneio.empresa_nome}
              {romaneio.empresa_uf && <span className="text-kami-charcoal-light">· {romaneio.empresa_uf}</span>}
            </p>
          )}
          <p className="mt-1 text-sm text-kami-charcoal-light">
            {romaneio.transportadora_nome ??
              (romaneio.transportadora_cnpj_externo
                ? `CNPJ ${romaneio.transportadora_cnpj_externo} não cadastrado`
                : "Aguardando definição da transportadora")}
          </p>
        </div>
        <span className="rounded-full bg-kami-red/10 px-3 py-1 text-xs font-medium text-kami-red">
          {LABEL_STATUS[romaneio.status] ?? romaneio.status}
        </span>
      </div>

      {romaneio.romaneio_origem_id && (
        <p className="mb-4 text-xs text-kami-charcoal-light">
          Reenvio dos pedidos pendentes do romaneio{" "}
          <Link href={`/romaneios/${romaneio.romaneio_origem_id}`} className="font-medium text-kami-red hover:underline">
            {romaneio.romaneio_origem_codigo}
          </Link>
        </p>
      )}

      <div className="mb-6 grid grid-cols-2 gap-3 rounded-xl border border-black/10 bg-white p-4 text-sm sm:grid-cols-4">
        <div>
          <p className="text-kami-charcoal-light">Pedidos</p>
          <p className="font-medium text-kami-charcoal">{romaneio.qtd_pedidos ?? "—"}</p>
        </div>
        <div>
          <p className="text-kami-charcoal-light">Caixas</p>
          <p className="font-medium text-kami-charcoal">{romaneio.qtd_caixas ?? "—"}</p>
        </div>
        <div>
          <p className="text-kami-charcoal-light">Peso</p>
          <p className="font-medium text-kami-charcoal">{romaneio.peso_total ? `${romaneio.peso_total} kg` : "—"}</p>
        </div>
        <div>
          <p className="text-kami-charcoal-light">Veículo / Motorista</p>
          <p className="font-medium text-kami-charcoal">
            {romaneio.veiculo_placa ?? "—"} · {romaneio.motorista_nome ?? "—"}
          </p>
        </div>
        {romaneio.tipo_veiculo_sugerido && (
          <div>
            <p className="text-kami-charcoal-light">Veículo sugerido</p>
            <p className="font-medium text-kami-charcoal">{romaneio.tipo_veiculo_sugerido}</p>
          </div>
        )}
        {romaneio.data_saida_prevista && (
          <div>
            <p className="text-kami-charcoal-light">Saída prevista</p>
            <p className="font-medium text-kami-charcoal">
              {new Date(romaneio.data_saida_prevista).toLocaleString("pt-BR")}
            </p>
          </div>
        )}
      </div>

      {acaoErro && <p className="mb-3 text-sm text-kami-red">{acaoErro}</p>}

      {(usuario?.papel === "kami_admin" || usuario?.papel === "transportadora_admin") &&
        ["romaneio_incompleto", "romaneio_com_problema"].includes(romaneio.status) &&
        romaneio.pedidos.some((p) => p.status_entrega !== "entregue") && (
          <div className="mb-6 flex flex-col gap-2 rounded-xl border border-black/10 bg-white p-4">
            <h2 className="text-sm font-semibold text-kami-charcoal">Reenviar pedidos pendentes</h2>
            <p className="text-sm text-kami-charcoal-light">
              Cria um novo romaneio só com os pedidos ainda não entregues, de volta em
              &ldquo;Definição de Transporte&rdquo; pra indicar outro veículo/motorista. Este romaneio (
              {romaneio.codigo}) fica como está, guardado como histórico.
            </p>
            <button
              onClick={handleClonarPendentes}
              disabled={clonando}
              className="self-start rounded-lg bg-kami-red px-3 py-1.5 text-sm font-medium text-white hover:bg-kami-red-dark disabled:opacity-60"
            >
              {clonando ? "Reenviando..." : "Reenviar pedidos pendentes"}
            </button>
          </div>
        )}

      {podeDefinirTransportadora && (
        <form
          onSubmit={handleDefinirTransportadora}
          className="mb-6 flex flex-col gap-3 rounded-xl border border-black/10 bg-white p-4"
        >
          <h2 className="text-sm font-semibold text-kami-charcoal">Definir transportadora</h2>
          <p className="text-xs text-kami-charcoal-light">
            Esse romaneio veio do UNO com um CNPJ que ainda não bate com nenhuma transportadora
            cadastrada
            {romaneio.transportadora_cnpj_externo && (
              <>
                {" "}
                (<strong>{romaneio.transportadora_cnpj_externo}</strong>)
              </>
            )}
            . Escolha manualmente qual transportadora deve atender.
          </p>
          <div className="flex flex-col gap-3 sm:flex-row">
            <select
              required
              value={transportadoraEscolhidaId}
              onChange={(e) => setTransportadoraEscolhidaId(e.target.value)}
              className="flex-1 rounded-lg border border-black/10 px-3 py-2 text-sm outline-none focus:border-kami-red"
            >
              <option value="">Selecione a transportadora...</option>
              {transportadoras?.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.nome_fantasia}
                </option>
              ))}
            </select>
            <button
              type="submit"
              disabled={definindoTransportadora}
              className="rounded-lg bg-kami-red px-3 py-1.5 text-sm font-medium text-white hover:bg-kami-red-dark disabled:opacity-60"
            >
              {definindoTransportadora ? "Definindo..." : "Definir"}
            </button>
          </div>
        </form>
      )}

      {podeTrocarTransportadora && (
        <form
          onSubmit={handleTrocarTransportadora}
          className="mb-6 flex flex-col gap-3 rounded-xl border border-black/10 bg-white p-4"
        >
          <h2 className="text-sm font-semibold text-kami-charcoal">Trocar transportadora indicada</h2>
          <div className="flex flex-col gap-3 sm:flex-row">
            <select
              required
              value={novaTransportadoraId}
              onChange={(e) => setNovaTransportadoraId(e.target.value)}
              className="flex-1 rounded-lg border border-black/10 px-3 py-2 text-sm outline-none focus:border-kami-red"
            >
              <option value="">Selecione a nova transportadora...</option>
              {transportadoras
                ?.filter((t) => t.id !== romaneio.transportadora_id)
                .map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.nome_fantasia}
                  </option>
                ))}
            </select>
            <button
              type="submit"
              disabled={trocandoTransportadora}
              className="rounded-lg bg-kami-charcoal px-3 py-1.5 text-sm font-medium text-white disabled:opacity-60"
            >
              {trocandoTransportadora ? "Trocando..." : "Trocar"}
            </button>
          </div>
        </form>
      )}

      {podeAlocar && (
        <form
          onSubmit={handlePedirConfirmacaoAlocar}
          className="mb-6 flex flex-col gap-3 rounded-xl border border-black/10 bg-white p-4"
        >
          <h2 className="text-sm font-semibold text-kami-charcoal">Alocar veículo e motorista</h2>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <select
              required
              value={veiculoId}
              onChange={(e) => setVeiculoId(e.target.value)}
              disabled={confirmandoAlocacao}
              className="rounded-lg border border-black/10 px-3 py-2 text-sm outline-none focus:border-kami-red disabled:opacity-60"
            >
              <option value="">Veículo...</option>
              {veiculos?.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.placa} — {v.tipo}
                </option>
              ))}
            </select>
            <select
              required
              value={motoristaId}
              onChange={(e) => setMotoristaId(e.target.value)}
              disabled={confirmandoAlocacao}
              className="rounded-lg border border-black/10 px-3 py-2 text-sm outline-none focus:border-kami-red disabled:opacity-60"
            >
              <option value="">Motorista...</option>
              {motoristas?.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.nome}
                </option>
              ))}
            </select>
          </div>

          {!confirmandoAlocacao ? (
            <button
              type="submit"
              className="self-start rounded-lg bg-kami-red px-3 py-1.5 text-sm font-medium text-white hover:bg-kami-red-dark disabled:opacity-60"
            >
              Enviar para conferência logística
            </button>
          ) : (
            <div className="rounded-lg bg-zinc-50 p-3">
              <p className="mb-2 text-sm text-kami-charcoal">
                Podemos enviar para a próxima etapa, que é conferência logística?
              </p>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={handleConfirmarAlocar}
                  disabled={enviando}
                  className="rounded-lg bg-kami-red px-3 py-1.5 text-sm font-medium text-white hover:bg-kami-red-dark disabled:opacity-60"
                >
                  {enviando ? "Enviando..." : "Sim, enviar"}
                </button>
                <button
                  type="button"
                  onClick={handleCancelarConfirmacaoAlocar}
                  disabled={enviando}
                  className="rounded-lg border border-black/10 px-3 py-1.5 text-sm font-medium text-kami-charcoal disabled:opacity-60"
                >
                  Não, ainda não
                </button>
              </div>
            </div>
          )}
        </form>
      )}

      {usuario?.papel === "kami_admin" && romaneio.status === "conferencia_logistica" && (
        <div className="mb-6 flex flex-col gap-3 rounded-xl border border-black/10 bg-white p-4">
          <h2 className="text-sm font-semibold text-kami-charcoal">Conferência logística</h2>
          <p className="text-sm text-kami-charcoal-light">
            Confirme que o motorista <strong>{romaneio.motorista_nome}</strong> e o veículo{" "}
            <strong>{romaneio.veiculo_placa}</strong> conferem com o indicado no portão.
          </p>
          <div className="flex gap-2">
            <button
              onClick={handleConfirmarConferencia}
              disabled={enviando}
              className="self-start rounded-lg bg-kami-red px-3 py-1.5 text-sm font-medium text-white hover:bg-kami-red-dark disabled:opacity-60"
            >
              {enviando ? "Confirmando..." : "Confirmar conferência"}
            </button>
            {!mostrarDevolucao && (
              <button
                type="button"
                onClick={() => setMostrarDevolucao(true)}
                disabled={enviando}
                className="self-start rounded-lg border border-black/10 px-3 py-1.5 text-sm font-medium text-kami-charcoal disabled:opacity-60"
              >
                Não confere — devolver p/ ajuste
              </button>
            )}
          </div>

          {mostrarDevolucao && (
            <div className="rounded-lg bg-zinc-50 p-3">
              <p className="mb-2 text-sm text-kami-charcoal">
                O romaneio volta para &ldquo;Definição de transporte&rdquo; e a transportadora{" "}
                <strong>{romaneio.transportadora_nome}</strong> poderá indicar outro veículo/motorista.
              </p>
              <textarea
                placeholder="Motivo (opcional)"
                value={motivoDevolucao}
                onChange={(e) => setMotivoDevolucao(e.target.value)}
                rows={2}
                className="mb-2 w-full rounded-lg border border-black/10 px-3 py-2 text-sm outline-none focus:border-kami-red"
              />
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={handleDevolverParaTransporte}
                  disabled={enviando}
                  className="rounded-lg bg-kami-red px-3 py-1.5 text-sm font-medium text-white hover:bg-kami-red-dark disabled:opacity-60"
                >
                  {enviando ? "Devolvendo..." : "Confirmar devolução"}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setMostrarDevolucao(false);
                    setMotivoDevolucao("");
                  }}
                  disabled={enviando}
                  className="rounded-lg border border-black/10 px-3 py-1.5 text-sm font-medium text-kami-charcoal disabled:opacity-60"
                >
                  Cancelar
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {romaneio.fotos_carregamento.length > 0 && (
        <div className="mb-6 rounded-xl border border-black/10 bg-white p-4">
          <h2 className="mb-2 text-sm font-semibold text-kami-charcoal">
            Evidências de carregamento ({romaneio.fotos_carregamento.length})
          </h2>
          <div className="grid grid-cols-3 gap-2">
            {romaneio.fotos_carregamento.map((foto) => (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                key={foto.id}
                src={`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api"}${foto.foto_url}`}
                alt="Foto do carregamento"
                className="h-28 w-full rounded-lg object-cover"
              />
            ))}
          </div>
        </div>
      )}

      {usuario?.papel === "kami_admin" && romaneio.status === "em_transito" && (
        <div className="mb-6 flex flex-col gap-3 rounded-xl border border-black/10 bg-white p-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-kami-charcoal">Inserir nova parada (Regra 7)</h2>
            <button
              onClick={() => setMostrarNovoPedido((v) => !v)}
              className="text-xs font-medium text-kami-red"
            >
              {mostrarNovoPedido ? "Cancelar" : "+ adicionar"}
            </button>
          </div>
          {mostrarNovoPedido && (
            <form onSubmit={handleAdicionarPedido} className="flex flex-col gap-2">
              <input
                required
                placeholder="Nome do cliente"
                value={novoPedidoNome}
                onChange={(e) => setNovoPedidoNome(e.target.value)}
                className="rounded-lg border border-black/10 px-3 py-2 text-sm outline-none focus:border-kami-red"
              />
              <input
                required
                placeholder="Endereço completo"
                value={novoPedidoEndereco}
                onChange={(e) => setNovoPedidoEndereco(e.target.value)}
                className="rounded-lg border border-black/10 px-3 py-2 text-sm outline-none focus:border-kami-red"
              />
              <button
                type="submit"
                disabled={enviando}
                className="self-start rounded-lg bg-kami-charcoal px-3 py-1.5 text-sm font-medium text-white disabled:opacity-60"
              >
                {enviando ? "Adicionando..." : "Adicionar parada"}
              </button>
            </form>
          )}
        </div>
      )}

      <div className="rounded-xl border border-black/10 bg-white">
        <h2 className="border-b border-black/10 px-4 py-3 text-sm font-semibold text-kami-charcoal">
          Pedidos ({romaneio.pedidos.length})
        </h2>
        <ul className="divide-y divide-black/5">
          {romaneio.pedidos
            .slice()
            .sort((a, b) => a.sequencia_atual - b.sequencia_atual)
            .map((p) => (
              <li key={p.id} className="flex items-center justify-between px-4 py-3 text-sm">
                <div>
                  <p className="font-medium text-kami-charcoal">
                    {p.sequencia_atual}. {p.cliente_nome}
                  </p>
                  <p className="text-kami-charcoal-light">{p.cliente_endereco}</p>
                  {(p.peso_kg || p.qtd_volumes) && (
                    <p className="mt-0.5 text-xs text-kami-charcoal-light">
                      {p.peso_kg ? `${p.peso_kg} kg` : null}
                      {p.peso_kg && p.qtd_volumes ? " · " : null}
                      {p.qtd_volumes ? `${p.qtd_volumes} ${p.especie_volume ?? "volume(s)"}` : null}
                    </p>
                  )}
                </div>
                <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs text-kami-charcoal-light">
                  {p.status_entrega}
                </span>
              </li>
            ))}
        </ul>
      </div>

      <div className="mt-6 rounded-xl border border-black/10 bg-white">
        <button
          onClick={() => setMostrarHistorico((v) => !v)}
          className="flex w-full items-center justify-between px-4 py-3 text-sm font-semibold text-kami-charcoal"
        >
          Histórico completo
          <span className="text-xs font-normal text-kami-charcoal-light">
            {mostrarHistorico ? "ocultar ▲" : "mostrar ▼"}
          </span>
        </button>
        {mostrarHistorico && (
          <div className="border-t border-black/10 px-4 py-4">
            <HistoricoTimeline romaneioId={romaneioId} />
          </div>
        )}
      </div>
    </div>
  );
}
