type EnderecoComCoordenadas = {
  cliente_endereco: string;
  cliente_lat: number | null;
  cliente_lng: number | null;
};

export function linkGoogleMaps(pedido: EnderecoComCoordenadas): string {
  const destino =
    pedido.cliente_lat && pedido.cliente_lng
      ? `${pedido.cliente_lat},${pedido.cliente_lng}`
      : encodeURIComponent(pedido.cliente_endereco);
  return `https://www.google.com/maps/dir/?api=1&destination=${destino}&travelmode=driving`;
}

export function linkWaze(pedido: EnderecoComCoordenadas): string {
  if (pedido.cliente_lat && pedido.cliente_lng) {
    return `https://waze.com/ul?ll=${pedido.cliente_lat},${pedido.cliente_lng}&navigate=yes`;
  }
  return `https://waze.com/ul?q=${encodeURIComponent(pedido.cliente_endereco)}&navigate=yes`;
}
