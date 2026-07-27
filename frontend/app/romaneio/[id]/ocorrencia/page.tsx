import { OcorrenciaForm } from "./ocorrencia-form";

export default async function OcorrenciaPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <OcorrenciaForm romaneioId={Number(id)} />;
}
