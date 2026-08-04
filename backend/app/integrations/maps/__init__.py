from app.core.config import get_settings
from app.integrations.maps.fake_adapter import FakeDistanceMatrixProvider
from app.integrations.maps.interface import DistanceMatrixProvider
from app.integrations.maps.openrouteservice_adapter import OpenRouteServiceDistanceMatrixProvider


def get_maps_provider() -> DistanceMatrixProvider:
    adapter = get_settings().integration_adapter_maps
    if adapter == "openrouteservice":
        return OpenRouteServiceDistanceMatrixProvider()
    return FakeDistanceMatrixProvider()
