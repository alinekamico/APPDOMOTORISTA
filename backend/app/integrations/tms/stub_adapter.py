from app.schemas.romaneio import RomaneioCriarRequest


class StubTmsPayloadTranslator:
    """Assume que o payload recebido já está no formato de `RomaneioCriarRequest`.

    Usado tanto pelo webhook (POST /webhooks/tms) quanto, indiretamente, pela tela manual de
    simulação — os dois convergem no mesmo `romaneio_service.criar_de_comando`.
    """

    def to_romaneio_command(self, payload: dict) -> RomaneioCriarRequest:
        return RomaneioCriarRequest.model_validate(payload)


def get_tms_translator() -> StubTmsPayloadTranslator:
    return StubTmsPayloadTranslator()
