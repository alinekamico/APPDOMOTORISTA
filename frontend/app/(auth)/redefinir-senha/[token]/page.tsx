import { RedefinirSenhaForm } from "./redefinir-senha-form";

export default async function RedefinirSenhaPage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = await params;
  return <RedefinirSenhaForm token={token} />;
}
