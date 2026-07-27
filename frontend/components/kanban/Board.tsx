import { Column } from "./Column";
import { COLUNAS, type RomaneioResumo } from "./types";

export function Board({ romaneios }: { romaneios: RomaneioResumo[] }) {
  return (
    <div className="flex gap-3 overflow-x-auto pb-4">
      {COLUNAS.map((coluna) => (
        <Column
          key={coluna.status}
          titulo={coluna.titulo}
          responsavel={coluna.responsavel}
          romaneios={romaneios.filter((r) => r.status === coluna.status)}
        />
      ))}
    </div>
  );
}
