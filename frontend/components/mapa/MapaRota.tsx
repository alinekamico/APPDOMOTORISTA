"use client";

import { useEffect } from "react";
import { MapContainer, Marker, Polyline, TileLayer, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

export type PontoRota = {
  id: number;
  sequencia_atual: number;
  cliente_nome: string;
  lat: number;
  lng: number;
  entregue: boolean;
};

function criarIcone(texto: string, cor: string) {
  return L.divIcon({
    className: "",
    html: `<div style="background:${cor};color:#fff;border-radius:9999px;width:26px;height:26px;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:600;border:2px solid #fff;box-shadow:0 1px 3px rgba(0,0,0,0.4)">${texto}</div>`,
    iconSize: [26, 26],
    iconAnchor: [13, 13],
  });
}

function AjustarLimites({ pontos }: { pontos: { lat: number; lng: number }[] }) {
  const map = useMap();

  useEffect(() => {
    if (pontos.length === 0) return;
    if (pontos.length === 1) {
      map.setView([pontos[0].lat, pontos[0].lng], 15);
      return;
    }
    const bounds = L.latLngBounds(pontos.map((p) => [p.lat, p.lng] as [number, number]));
    map.fitBounds(bounds, { padding: [24, 24] });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [map, JSON.stringify(pontos)]);

  return null;
}

export function MapaRota({
  pedidos,
  posicaoAtual,
}: {
  pedidos: PontoRota[];
  posicaoAtual?: { lat: number; lng: number } | null;
}) {
  const pontosComCoordenada = pedidos.filter(
    (p) => typeof p.lat === "number" && typeof p.lng === "number"
  );

  if (pontosComCoordenada.length === 0) {
    return (
      <div className="flex h-56 items-center justify-center rounded-xl border border-dashed border-black/15 bg-zinc-50 text-center text-xs text-kami-charcoal-light">
        Nenhuma parada com coordenadas geocodificadas para mostrar no mapa.
      </div>
    );
  }

  const todosOsPontos = posicaoAtual ? [posicaoAtual, ...pontosComCoordenada] : pontosComCoordenada;
  const caminho = pontosComCoordenada
    .slice()
    .sort((a, b) => a.sequencia_atual - b.sequencia_atual)
    .map((p): [number, number] => [p.lat, p.lng]);

  return (
    <div className="h-56 w-full overflow-hidden rounded-xl border border-black/10">
      <MapContainer
        center={[pontosComCoordenada[0].lat, pontosComCoordenada[0].lng]}
        zoom={13}
        scrollWheelZoom
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <AjustarLimites pontos={todosOsPontos} />

        {posicaoAtual && (
          <Marker
            position={[posicaoAtual.lat, posicaoAtual.lng]}
            icon={criarIcone("●", "#463D3F")}
          />
        )}

        {pontosComCoordenada.map((p) => (
          <Marker
            key={p.id}
            position={[p.lat, p.lng]}
            icon={criarIcone(String(p.sequencia_atual), p.entregue ? "#16a34a" : "#E2032A")}
          />
        ))}

        {posicaoAtual && caminho.length > 0 && (
          <Polyline
            positions={[[posicaoAtual.lat, posicaoAtual.lng], ...caminho]}
            color="#E2032A"
            opacity={0.7}
            weight={3}
          />
        )}
      </MapContainer>
    </div>
  );
}
