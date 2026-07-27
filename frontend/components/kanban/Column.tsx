import { Card } from "./Card";
import type { RomaneioResumo } from "./types";

export function Column({
  titulo,
  responsavel,
  romaneios,
}: {
  titulo: string;
  responsavel: string;
  romaneios: RomaneioResumo[];
}) {
  return (
    <div className="flex w-72 shrink-0 flex-col rounded-xl bg-zinc-100/70 p-3">
      <div className="mb-3 flex items-center justify-between px-1">
        <div>
          <h3 className="text-sm font-semibold text-kami-charcoal">{titulo}</h3>
          <p className="text-[11px] text-kami-charcoal-light">Responsável: {responsavel}</p>
        </div>
        <span className="rounded-full bg-white px-2 py-0.5 text-xs font-medium text-kami-charcoal-light">
          {romaneios.length}
        </span>
      </div>

      <div className="flex flex-col gap-2">
        {romaneios.map((r) => (
          <Card key={r.id} romaneio={r} />
        ))}
        {romaneios.length === 0 && (
          <p className="px-1 text-xs text-kami-charcoal-light/70">Nenhum romaneio aqui.</p>
        )}
      </div>
    </div>
  );
}
