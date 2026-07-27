from app.core.config import get_settings
from app.integrations.maps.fake_adapter import FakeDistanceMatrixProvider
from app.integrations.maps.google_adapter import GoogleDistanceMatrixProvider
from app.integrations.maps.interface import DistanceMatrixProvider


def get_maps_provider() -> DistanceMatrixProvider:
    adapter = get_settings().integration_adapter_maps
    if adapter == "google":
        return GoogleDistanceMatrixProvider()
    return FakeDistanceMatrixProvider()
