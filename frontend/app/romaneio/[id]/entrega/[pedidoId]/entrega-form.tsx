"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useRequireRole } from "@/lib/roles";
import { useFetch } from "@/lib/use-fetch";
import { apiFetch, ApiError } from "@/lib/api-client";
import { useGeolocation } from "@/hooks/useGeolocation";
import { CameraCapture } from "@/components/entrega/CameraCapture";
import { AssinaturaCanvas, type AssinaturaCanvasHandle } from "@/components/entrega/AssinaturaCanvas";
import { linkGoogleMaps, linkWaze } from "@/lib/navegacao";

type Pedido = {
  id: number;
  cliente_nome: string;
  cliente_endereco: string;
  cliente_lat: number | null;
  cliente_lng: number | null;
  cliente_whatsapp: string | null;
  cliente_email: string | null;
};

type RomaneioComPedidos = { pedidos: Pedido[] };

type TipoOcorrencia = { id: number; descricao: string; exige_observacao: boolean; exige_foto: boolean };

export function EntregaForm({ romaneioId, pedidoId }: { romaneioId: number; pedidoId: number }) {
  const { carregando: carregandoAuth } = useRequireRole(["motorista"]);
  const router = useRouter();

  const { data: romaneio } = useFetch<RomaneioComPedidos>(carregandoAuth ? null : `/romaneios/${romaneioId}`);
  const pedido = romaneio?.pedidos.find((p) => p.id === pedidoId);

  const { data: tiposOcorrencia } = useFetch<TipoOcorrencia[]>("/tipos-ocorrencia?categoria=nao_entrega");
  const { data: tiposDesvio } = useFetch<TipoOcorrencia[]>("/tipos-ocorrencia?categoria=desvio_rota");
  const { coordenadas, capturar } = useGeolocation();

  const [modo, setModo] = useState<"entrega" | "nao_entrega">("entrega");
  const assinaturaRef = useRef<AssinaturaCanvasHandle>(null);
  const [foto, setFoto] = useState<File | null>(null);
  const [nomeRecebedor, setNomeRecebedor] = useState("");
  const [whatsapp, setWhatsapp] = useState("");
  const [email, setEmail] = useState("");
  const [precisaJustificarDesvio, setPrecisaJustificarDesvio] = useState(false);
  const [tipoDesvioId, setTipoDesvioId] = useState("");
  const [mercadoriaConferida, setMercadoriaConferida] = useState<"sim" | "nao" | "">("");

  const [tipoOcorrenciaId, setTipoOcorrenciaId] = useState("");
  const [observacao, setObservacao] = useState("");
  const [fotoOcorrencia, setFotoOcorrencia] = useState<File | null>(null);

  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const erroRef = useRef<HTMLParagraphElement>(null);

  useEffect(() => {
    capturar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // No celular, o formulário é mais alto que a tela — sem isso, o erro aparece
  // fora da área visível quando o motorista confirma rolado até o botão no final.
  useEffect(() => {
    if (erro) erroRef.current?.scrollIntoView({ block: "center" });
  }, [erro]);

  useEffect(() => {
    if (pedido) {
      setWhatsapp(pedido.cliente_whatsapp ?? "");
      setEmail(pedido.cliente_email ?? "");
    }
  }, [pedido]);

  async function handleConfirmarEntrega() {
    setErro(null);
    if (!foto) return setErro("Tire uma foto da entrega.");
    if (!assinaturaRef.current?.temAssinatura()) return setErro("Colete a assinatura do cliente.");
    if (!nomeRecebedor) return setErro("Informe o nome de quem recebeu.");
    if (!mercadoriaConferida) return setErro("Informe se o cliente conferiu a mercadoria.");
    if (precisaJustificarDesvio && !tipoDesvioId) return setErro("Selecione o motivo do desvio de sequência.");

    setEnviando(true);
    try {
      const assinatura = await assinaturaRef.current.obterAssinatura();
      if (!assinatura) throw new Error("Falha ao capturar assinatura");

      const formData = new FormData();
      formData.append("foto", foto);
      formData.append("assinatura", assinatura);
      formData.append("nome_recebedor", nomeRecebedor);
      formData.append("mercadoria_conferida_na_entrega", String(mercadoriaConferida === "sim"));
      if (whatsapp) formData.append("cliente_whatsapp", whatsapp);
      if (email) formData.append("cliente_email", email);
      if (coordenadas) {
        formData.append("geolocalizacao_lat", String(coordenadas.lat));
        formData.append("geolocalizacao_lng", String(coordenadas.lng));
      }
      if (tipoDesvioId) formData.append("tipo_ocorrencia_desvio_id", tipoDesvioId);

      await apiFetch(`/pedidos/${pedidoId}/entrega`, { method: "POST", body: formData, isFormData: true });
      router.push(`/romaneio/${romaneioId}`);
    } catch (err) {
      if (err instanceof ApiError && err.status === 422) {
        setPrecisaJustificarDesvio(true);
        setErro("Esta entrega está fora da sequência prevista — selecione o motivo do desvio abaixo e confirme novamente.");
      } else {
        setErro(err instanceof ApiError ? err.detail : "Não foi possível registrar a entrega.");
      }
    } finally {
      setEnviando(false);
    }
  }

  async function handleConfirmarNaoEntrega() {
    setErro(null);
    if (!tipoOcorrenciaId) return setErro("Selecione o motivo da não entrega.");

    setEnviando(true);
    try {
      const formData = new FormData();
      formData.append("tipo_ocorrencia_id", tipoOcorrenciaId);
      if (observacao) formData.append("observacao", observacao);
      if (fotoOcorrencia) formData.append("foto", fotoOcorrencia);
      if (coordenadas) {
        formData.append("geolocalizacao_lat", String(coordenadas.lat));
        formData.append("geolocalizacao_lng", String(coordenadas.lng));
      }

      await apiFetch(`/pedidos/${pedidoId}/nao-entrega`, { method: "POST", body: formData, isFormData: true });
      router.push(`/romaneio/${romaneioId}`);
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível registrar a não entrega.");
    } finally {
      setEnviando(false);
    }
  }

  if (carregandoAuth || !pedido) return <p className="text-sm text-kami-charcoal-light">Carregando...</p>;

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-lg font-semibold text-kami-charcoal">{pedido.cliente_nome}</h1>
        <p className="text-sm text-kami-charcoal-light">{pedido.cliente_endereco}</p>
      </div>

      <div className="flex gap-2">
        <a
          href={linkGoogleMaps(pedido)}
          target="_blank"
          rel="noopener noreferrer"
          className="flex-1 rounded-lg border border-black/10 bg-white px-3 py-2 text-center text-sm font-medium text-kami-charcoal"
        >
          Abrir no Google Maps
        </a>
        <a
          href={linkWaze(pedido)}
          target="_blank"
          rel="noopener noreferrer"
          className="flex-1 rounded-lg border border-black/10 bg-white px-3 py-2 text-center text-sm font-medium text-kami-charcoal"
        >
          Abrir no Waze
        </a>
      </div>

      <div className="flex rounded-lg bg-zinc-100 p-1 text-sm">
        <button
          onClick={() => setModo("entrega")}
          className={`flex-1 rounded-md py-1.5 font-medium ${modo === "entrega" ? "bg-white text-kami-charcoal shadow-sm" : "text-kami-charcoal-light"}`}
        >
          Confirmar entrega
        </button>
        <button
          onClick={() => setModo("nao_entrega")}
          className={`flex-1 rounded-md py-1.5 font-medium ${modo === "nao_entrega" ? "bg-white text-kami-charcoal shadow-sm" : "text-kami-charcoal-light"}`}
        >
          Não entregue
        </button>
      </div>

      {erro && (
        <p ref={erroRef} className="rounded-lg bg-kami-red/10 px-3 py-2 text-sm font-medium text-kami-red">
          {erro}
        </p>
      )}

      {modo === "entrega" ? (
        <div className="flex flex-col gap-4">
          <CameraCapture label="Foto da entrega" onCapture={setFoto} />
          <AssinaturaCanvas ref={assinaturaRef} />

          {precisaJustificarDesvio && (
            <label className="flex flex-col gap-1 text-sm">
              Motivo do desvio de sequência
              <select
                required
                value={tipoDesvioId}
                onChange={(e) => setTipoDesvioId(e.target.value)}
                className="rounded-lg border border-kami-red/50 px-3 py-2 outline-none focus:border-kami-red"
              >
                <option value="">Selecione...</option>
                {tiposDesvio?.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.descricao}
                  </option>
                ))}
              </select>
            </label>
          )}

          <label className="flex flex-col gap-1 text-sm">
            Nome de quem recebeu
            <input
              required
              value={nomeRecebedor}
              onChange={(e) => setNomeRecebedor(e.target.value)}
              className="rounded-lg border border-black/10 px-3 py-2 outline-none focus:border-kami-red"
            />
          </label>

          <div className="flex flex-col gap-1 text-sm">
            O cliente conferiu a mercadoria na hora da entrega?
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setMercadoriaConferida("sim")}
                className={`flex-1 rounded-lg border px-3 py-2 text-sm font-medium ${
                  mercadoriaConferida === "sim"
                    ? "border-kami-red bg-kami-red/10 text-kami-red"
                    : "border-black/10 text-kami-charcoal"
                }`}
              >
                Sim, conferiu na hora
              </button>
              <button
                type="button"
                onClick={() => setMercadoriaConferida("nao")}
                className={`flex-1 rounded-lg border px-3 py-2 text-sm font-medium ${
                  mercadoriaConferida === "nao"
                    ? "border-kami-red bg-kami-red/10 text-kami-red"
                    : "border-black/10 text-kami-charcoal"
                }`}
              >
                Não, vai conferir depois
              </button>
            </div>
          </div>

          <label className="flex flex-col gap-1 text-sm">
            WhatsApp do cliente
            <input
              value={whatsapp}
              onChange={(e) => setWhatsapp(e.target.value)}
              className="rounded-lg border border-black/10 px-3 py-2 outline-none focus:border-kami-red"
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            E-mail do cliente
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="rounded-lg border border-black/10 px-3 py-2 outline-none focus:border-kami-red"
            />
          </label>

          {erro && <p className="rounded-lg bg-kami-red/10 px-3 py-2 text-sm font-medium text-kami-red">{erro}</p>}

          <button
            onClick={handleConfirmarEntrega}
            disabled={enviando}
            className="rounded-xl bg-kami-red px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
          >
            {enviando ? "Enviando..." : "Confirmar entrega"}
          </button>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          <label className="flex flex-col gap-1 text-sm">
            Motivo da não entrega
            <select
              required
              value={tipoOcorrenciaId}
              onChange={(e) => setTipoOcorrenciaId(e.target.value)}
              className="rounded-lg border border-black/10 px-3 py-2 outline-none focus:border-kami-red"
            >
              <option value="">Selecione...</option>
              {tiposOcorrencia?.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.descricao}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1 text-sm">
            Observação
            <textarea
              value={observacao}
              onChange={(e) => setObservacao(e.target.value)}
              rows={3}
              className="rounded-lg border border-black/10 px-3 py-2 outline-none focus:border-kami-red"
            />
          </label>

          <CameraCapture label="Foto (opcional)" onCapture={setFotoOcorrencia} />

          <button
            onClick={handleConfirmarNaoEntrega}
            disabled={enviando}
            className="rounded-xl bg-kami-charcoal px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
          >
            {enviando ? "Enviando..." : "Registrar não entrega"}
          </button>
        </div>
      )}
    </div>
  );
}
