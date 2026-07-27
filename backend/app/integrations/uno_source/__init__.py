from app.core.config import get_settings
from app.integrations.uno_source.interface import RomaneioSource
from app.integrations.uno_source.manual_adapter import ManualRomaneioSource


def get_romaneio_source() -> RomaneioSource:
    settings = get_settings()
    if settings.integration_adapter_romaneio_source == "uno_replica":
        from app.integrations.uno_source.supabase_adapter import SupabaseUnoReplicaSource

        return SupabaseUnoReplicaSource()
    return ManualRomaneioSource()
