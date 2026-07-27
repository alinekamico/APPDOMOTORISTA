import { RomaneioExecucaoHub } from "./romaneio-execucao-hub";

export default async function RomaneioExecucaoPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <RomaneioExecucaoHub romaneioId={Number(id)} />;
}
