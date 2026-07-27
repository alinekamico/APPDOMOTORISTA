import { EntregaForm } from "./entrega-form";

export default async function EntregaPage({
  params,
}: {
  params: Promise<{ id: string; pedidoId: string }>;
}) {
  const { id, pedidoId } = await params;
  return <EntregaForm romaneioId={Number(id)} pedidoId={Number(pedidoId)} />;
}
