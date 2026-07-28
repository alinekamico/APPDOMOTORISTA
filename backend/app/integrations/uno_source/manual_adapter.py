from app.integrations.uno_source.dto import RomaneioExternoDTO, TransportadoraExternaDTO


class ManualRomaneioSource:
    """Sem fonte automática configurada — os romaneios de teste são criados à mão pela
    tela "Novo romaneio (simulação)". É o padrão até `UNO_REPLICA_DATABASE_URL` ser configurada.
    """

    def buscar_romaneios_pendentes(self) -> list[RomaneioExternoDTO]:
        return []

    def buscar_transportadoras(self) -> list[TransportadoraExternaDTO]:
        return []

    def buscar_empresas_por_referencia(self, referencias: list[str]) -> dict[str, tuple[str, str | None]]:
        return {}
