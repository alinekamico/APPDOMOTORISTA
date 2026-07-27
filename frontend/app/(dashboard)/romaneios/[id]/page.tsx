import { RomaneioDetalhe } from "./romaneio-detalhe";

export default async function RomaneioDetalhePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <RomaneioDetalhe romaneioId={Number(id)} />;
}
