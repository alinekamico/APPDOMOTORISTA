"use client";

import { useEffect } from "react";
import { APIProvider, AdvancedMarker, Map, Pin, Polyline, useMap } from "@vis.gl/react-google-maps";

export type PontoRota = {
  id: number;
  sequencia_atual: number;
  cliente_nome: string;
  lat: number;
  lng: number;
  entregue: boolean;
};

const API_KEY = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;

function AjustarLimites({ pontos }: { pontos: { lat: number; lng: number }[] }) {
  const map = useMap();

  useEffect(() => {
    if (!map || pontos.length === 0) return;
    if (pontos.length === 1) {
      map.setCenter(pontos[0]);
      map.setZoom(15);
      return;
    }
    const bounds = new google.maps.LatLngBounds();
    pontos.forEach((p) => bounds.extend(p));
    map.fitBounds(bounds, 48);
  }, [map, pontos]);

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

  if (!API_KEY) {
    return (
      <div className="flex h-56 items-center justify-center rounded-xl border border-dashed border-black/15 bg-zinc-50 text-center text-xs text-kami-charcoal-light">
        Mapa embutido desativado — configure NEXT_PUBLIC_GOOGLE_MAPS_API_KEY para exibi-lo.
      </div>
    );
  }

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
    .map((p) => ({ lat: p.lat, lng: p.lng }));

  return (
    <APIProvider apiKey={API_KEY}>
      <div className="h-56 w-full overflow-hidden rounded-xl border border-black/10">
        <Map
          mapId="kami-romaneio-map"
          defaultCenter={pontosComCoordenada[0]}
          defaultZoom={13}
          gestureHandling="greedy"
          disableDefaultUI
        >
          <AjustarLimites pontos={todosOsPontos} />

          {posicaoAtual && (
            <AdvancedMarker position={posicaoAtual} title="Sua posição atual">
              <Pin background="#463D3F" borderColor="#463D3F" glyphColor="#FFFFFF" />
            </AdvancedMarker>
          )}

          {pontosComCoordenada.map((p) => (
            <AdvancedMarker key={p.id} position={{ lat: p.lat, lng: p.lng }} title={p.cliente_nome}>
              <Pin
                background={p.entregue ? "#16a34a" : "#E2032A"}
                borderColor={p.entregue ? "#15803d" : "#b8021f"}
                glyphColor="#FFFFFF"
                glyph={String(p.sequencia_atual)}
              />
            </AdvancedMarker>
          ))}

          {posicaoAtual && caminho.length > 0 && (
            <Polyline
              path={[posicaoAtual, ...caminho]}
              strokeColor="#E2032A"
              strokeOpacity={0.7}
              strokeWeight={3}
            />
          )}
        </Map>
      </div>
    </APIProvider>
  );
}
