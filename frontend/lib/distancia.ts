// Distância em linha reta (haversine) — sem depender de nenhuma API paga. É uma referência
// aproximada pro motorista ("~3.2 km"), não a distância real de rota (que exigiria uma
// chamada de API a cada atualização de posição).
export function calcularDistanciaKm(
  origem: { lat: number; lng: number },
  destino: { lat: number; lng: number }
): number {
  const raioTerraKm = 6371;
  const dLat = ((destino.lat - origem.lat) * Math.PI) / 180;
  const dLng = ((destino.lng - origem.lng) * Math.PI) / 180;
  const lat1 = (origem.lat * Math.PI) / 180;
  const lat2 = (destino.lat * Math.PI) / 180;

  const a = Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) ** 2;
  const c = 2 * Math.asin(Math.sqrt(a));
  return raioTerraKm * c;
}

export function formatarDistancia(km: number): string {
  if (km < 1) return `${Math.round(km * 1000)} m`;
  return `${km.toFixed(1)} km`;
}
