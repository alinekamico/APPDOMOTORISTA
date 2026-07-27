import { CarregamentoForm } from "./carregamento-form";

export default async function CarregamentoPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <CarregamentoForm romaneioId={Number(id)} />;
}
