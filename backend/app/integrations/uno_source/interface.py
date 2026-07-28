from typing import Protocol

from app.integrations.uno_source.dto import RomaneioExternoDTO, TransportadoraExternaDTO


class RomaneioSource(Protocol):
    """De onde o app busca romaneios enquanto o TMS real não existe.

    Fluxo definitivo (quando o TMS estiver pronto): o TMS empurra o romaneio via
    `POST /webhooks/tms/romaneios` (ver `app/integrations/tms/`).

    Fluxo de hoje: não há acesso direto ao UNO (ERP). Em vez disso, buscamos numa réplica
    do banco do UNO hospedada no Supabase (Postgres) — ver `supabase_adapter.py`. Trocar de
    fonte é só trocar `INTEGRATION_ADAPTER_ROMANEIO_SOURCE` no `.env`, sem tocar em
    `romaneio_service`.
    """

    def buscar_romaneios_pendentes(self) -> list[RomaneioExternoDTO]: ...

    def buscar_transportadoras(self) -> list[TransportadoraExternaDTO]: ...

    def buscar_empresas_por_referencia(self, referencias: list[str]) -> dict[str, tuple[str, str | None]]:
        """Mapa `referencia_externa -> (empresa_nome, empresa_uf)`, pra preencher
        romaneios já importados antes do campo empresa existir."""
        ...
