"use client";

import { useCallback, useState } from "react";

type Coordenadas = { lat: number; lng: number };

export function useGeolocation() {
  const [coordenadas, setCoordenadas] = useState<Coordenadas | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [capturando, setCapturando] = useState(false);

  const capturar = useCallback((): Promise<Coordenadas | null> => {
    return new Promise((resolve) => {
      if (typeof navigator === "undefined" || !navigator.geolocation) {
        setErro("Geolocalização não disponível neste dispositivo.");
        resolve(null);
        return;
      }
      setCapturando(true);
      navigator.geolocation.getCurrentPosition(
        (posicao) => {
          const coords = { lat: posicao.coords.latitude, lng: posicao.coords.longitude };
          setCoordenadas(coords);
          setCapturando(false);
          resolve(coords);
        },
        () => {
          setErro("Não foi possível obter sua localização. Verifique a permissão do navegador.");
          setCapturando(false);
          resolve(null);
        },
        { enableHighAccuracy: true, timeout: 10000 }
      );
    });
  }, []);

  return { coordenadas, erro, capturando, capturar };
}
