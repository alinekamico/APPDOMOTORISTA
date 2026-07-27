"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useRequireRole } from "@/lib/roles";
import { useFetch } from "@/lib/use-fetch";
import { apiFetch, ApiError } from "@/lib/api-client";

type Transportadora = { id: number; nome_fantasia: string };

type PedidoRascunho = {
  cliente_nome: string;
  cliente_endereco: string;
  cliente_whatsapp: string;
  cliente_email: string;
  cliente_lat: string;
  cliente_lng: string;
  peso_kg: string;
  qtd_volumes: string;
};

const PEDIDO_VAZIO: PedidoRascunho = {
  cliente_nome: "",
  cliente_endereco: "",
  cliente_whatsapp: "",
  cliente_email: "",
  cliente_lat: "",
  cliente_lng: "",
  peso_kg: "",
  qtd_volumes: "",
};

export default function NovoRomaneioPage() {
  const { carregando: carregandoAuth } = useRequireRole(["kami_admin"]);
  const { data: transportadoras } = useFetch<Transportadora[]>(carregandoAuth ? null : "/transportadoras");
  const router = useRouter();

  const [codigo, setCodigo] = useState("");
  const [transportadoraId, setTransportadoraId] = useState("");
  const [qtdCaixas, setQtdCaixas] = useState("");
  const [pesoTotal, setPesoTotal] = useState("");
  const [origemEndereco, setOrigemEndereco] = useState("");
  const [origemLat, setOrigemLat] = useState("");
  const [origemLng, setOrigemLng] = useState("");
  const [pedidos, setPedidos] = useState<PedidoRascunho[]>([{ ...PEDIDO_VAZIO }]);
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  const roteirizacaoAutomaticaHabilitada = origemLat.trim() !== "" && origemLng.trim() !== "";
  const todosPedidosComCoordenadas = pedidos.every((p) => p.cliente_lat.trim() !== "" && p.cliente_lng.trim() !== "");

  function atualizarPedido(index: number, campo: keyof PedidoRascunho, valor: string) {
    setPedidos((atual) => atual.map((p, i) => (i === index ? { ...p, [campo]: valor } : p)));
  }

  function adicionarPedido() {
    setPedidos((atual) => [...atual, { ...PEDIDO_VAZIO }]);
  }

  function removerPedido(index: number) {
    setPedidos((atual) => atual.filter((_, i) => i !== index));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);

    if (!transportadoraId) {
      setErro("Selecione a transportadora responsável.");
      return;
    }
    if (pedidos.some((p) => !p.cliente_nome || !p.cliente_endereco)) {
      setErro("Preencha nome e endereço de todos os pedidos.");
      return;
    }

    setEnviando(true);
    try {
      const romaneio = await apiFetch<{ id: number }>("/romaneios", {
        method: "POST",
        body: {
          codigo,
          transportadora_id: Number(transportadoraId),
          qtd_caixas: qtdCaixas ? Number(qtdCaixas) : null,
          peso_total: pesoTotal ? Number(pesoTotal) : null,
          origem_lat: origemLat ? Number(origemLat) : null,
          origem_lng: origemLng ? Number(origemLng) : null,
          pedidos: pedidos.map((p, i) => ({
            sequencia: i + 1,
            cliente_nome: p.cliente_nome,
            cliente_endereco: p.cliente_endereco,
            cliente_whatsapp: p.cliente_whatsapp,
            cliente_email: p.cliente_email,
            cliente_lat: p.cliente_lat ? Number(p.cliente_lat) : null,
            cliente_lng: p.cliente_lng ? Number(p.cliente_lng) : null,
            peso_kg: p.peso_kg ? Number(p.peso_kg) : null,
            qtd_volumes: p.qtd_volumes ? Number(p.qtd_volumes) : null,
          })),
        },
      });
      router.push(`/romaneios/${romaneio.id}`);
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível criar o romaneio.");
    } finally {
      setEnviando(false);
    }
  }

  if (carregandoAuth) return null;

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="mb-1 text-lg font-semibold text-kami-charcoal">Novo romaneio (simulação do TMS)</h1>
      <p className="mb-6 text-sm text-kami-charcoal-light">
        Enquanto a integração com o TMS real não existe, use esta tela para criar romaneios de teste
        — o romaneio entra direto na etapa &ldquo;Definição de transporte&rdquo;. Você só informa
        endereços e pesos; a sequência de entrega é calculada pelo sistema.
      </p>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="grid grid-cols-1 gap-3 rounded-xl border border-black/10 bg-white p-4 sm:grid-cols-2">
          <label className="flex flex-col gap-1 text-sm">
            Código do romaneio
            <input
              required
              value={codigo}
              onChange={(e) => setCodigo(e.target.value)}
              placeholder="RM-000123"
              className="rounded-lg border border-black/10 px-3 py-2 outline-none focus:border-kami-red"
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            Transportadora
            <select
              required
              value={transportadoraId}
              onChange={(e) => setTransportadoraId(e.target.value)}
              className="rounded-lg border border-black/10 px-3 py-2 outline-none focus:border-kami-red"
            >
              <option value="">Selecione...</option>
              {transportadoras?.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.nome_fantasia}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-sm">
            Qtd. caixas
            <input
              type="number"
              value={qtdCaixas}
              onChange={(e) => setQtdCaixas(e.target.value)}
              className="rounded-lg border border-black/10 px-3 py-2 outline-none focus:border-kami-red"
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            Peso total (kg)
            <input
              type="number"
              value={pesoTotal}
              onChange={(e) => setPesoTotal(e.target.value)}
              className="rounded-lg border border-black/10 px-3 py-2 outline-none focus:border-kami-red"
            />
          </label>
        </div>

        <div className="rounded-xl border border-black/10 bg-white p-4">
          <h2 className="mb-1 text-sm font-semibold text-kami-charcoal">Local de origem (saída do veículo)</h2>
          <p className="mb-3 text-xs text-kami-charcoal-light">
            Necessário pra roteirização automática — sem isso, os pedidos ficam na ordem em que
            foram digitados abaixo.
          </p>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <input
              placeholder="Endereço de origem (referência)"
              value={origemEndereco}
              onChange={(e) => setOrigemEndereco(e.target.value)}
              className="rounded-lg border border-black/10 px-3 py-2 text-sm outline-none focus:border-kami-red sm:col-span-1"
            />
            <input
              placeholder="Latitude de origem"
              type="number"
              step="any"
              value={origemLat}
              onChange={(e) => setOrigemLat(e.target.value)}
              className="rounded-lg border border-black/10 px-3 py-2 text-sm outline-none focus:border-kami-red"
            />
            <input
              placeholder="Longitude de origem"
              type="number"
              step="any"
              value={origemLng}
              onChange={(e) => setOrigemLng(e.target.value)}
              className="rounded-lg border border-black/10 px-3 py-2 text-sm outline-none focus:border-kami-red"
            />
          </div>
        </div>

        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-kami-charcoal">Pedidos ({pedidos.length})</h2>
            <button
              type="button"
              onClick={adicionarPedido}
              className="text-sm font-medium text-kami-red hover:text-kami-red-dark"
            >
              + adicionar pedido
            </button>
          </div>

          <p className="text-xs text-kami-charcoal-light">
            {roteirizacaoAutomaticaHabilitada && todosPedidosComCoordenadas
              ? "A ordem de entrega final será calculada automaticamente com base na localização — a ordem aqui embaixo não importa."
              : "Preencha a origem e a latitude/longitude de todos os pedidos pra habilitar o cálculo automático da rota. Sem isso, a ordem digitada abaixo é a que vale."}
          </p>

          {pedidos.map((pedido, index) => (
            <div key={index} className="rounded-xl border border-black/10 bg-white p-4">
              <div className="mb-2 flex items-center justify-between">
                <span className="text-xs font-semibold text-kami-charcoal-light">Parada {index + 1}</span>
                {pedidos.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removerPedido(index)}
                    className="text-xs text-kami-charcoal-light hover:text-kami-red"
                  >
                    remover
                  </button>
                )}
              </div>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <input
                  required
                  placeholder="Nome do cliente"
                  value={pedido.cliente_nome}
                  onChange={(e) => atualizarPedido(index, "cliente_nome", e.target.value)}
                  className="rounded-lg border border-black/10 px-3 py-2 text-sm outline-none focus:border-kami-red"
                />
                <input
                  required
                  placeholder="Endereço completo"
                  value={pedido.cliente_endereco}
                  onChange={(e) => atualizarPedido(index, "cliente_endereco", e.target.value)}
                  className="rounded-lg border border-black/10 px-3 py-2 text-sm outline-none focus:border-kami-red"
                />
                <input
                  placeholder="WhatsApp"
                  value={pedido.cliente_whatsapp}
                  onChange={(e) => atualizarPedido(index, "cliente_whatsapp", e.target.value)}
                  className="rounded-lg border border-black/10 px-3 py-2 text-sm outline-none focus:border-kami-red"
                />
                <input
                  placeholder="E-mail"
                  type="email"
                  value={pedido.cliente_email}
                  onChange={(e) => atualizarPedido(index, "cliente_email", e.target.value)}
                  className="rounded-lg border border-black/10 px-3 py-2 text-sm outline-none focus:border-kami-red"
                />
                <input
                  placeholder="Latitude (habilita mapa/roteirização)"
                  type="number"
                  step="any"
                  value={pedido.cliente_lat}
                  onChange={(e) => atualizarPedido(index, "cliente_lat", e.target.value)}
                  className="rounded-lg border border-black/10 px-3 py-2 text-sm outline-none focus:border-kami-red"
                />
                <input
                  placeholder="Longitude"
                  type="number"
                  step="any"
                  value={pedido.cliente_lng}
                  onChange={(e) => atualizarPedido(index, "cliente_lng", e.target.value)}
                  className="rounded-lg border border-black/10 px-3 py-2 text-sm outline-none focus:border-kami-red"
                />
                <input
                  placeholder="Peso (kg)"
                  type="number"
                  step="any"
                  value={pedido.peso_kg}
                  onChange={(e) => atualizarPedido(index, "peso_kg", e.target.value)}
                  className="rounded-lg border border-black/10 px-3 py-2 text-sm outline-none focus:border-kami-red"
                />
                <input
                  placeholder="Qtd. volumes"
                  type="number"
                  value={pedido.qtd_volumes}
                  onChange={(e) => atualizarPedido(index, "qtd_volumes", e.target.value)}
                  className="rounded-lg border border-black/10 px-3 py-2 text-sm outline-none focus:border-kami-red"
                />
              </div>
            </div>
          ))}
        </div>

        {erro && <p className="text-sm text-kami-red">{erro}</p>}

        <button
          type="submit"
          disabled={enviando}
          className="self-start rounded-lg bg-kami-red px-4 py-2 text-sm font-medium text-white hover:bg-kami-red-dark disabled:opacity-60"
        >
          {enviando ? "Criando..." : "Criar romaneio"}
        </button>
      </form>
    </div>
  );
}
