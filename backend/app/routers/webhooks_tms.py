from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.integrations.tms.stub_adapter import get_tms_translator
from app.models.enums import OrigemRomaneio
from app.models.romaneio import Romaneio
from app.schemas.romaneio import RomaneioOut
from app.services import romaneio_service

router = APIRouter(prefix="/webhooks/tms", tags=["webhooks"])
settings = get_settings()


def _verificar_token(x_tms_token: str | None = Header(default=None)) -> None:
    if not x_tms_token or x_tms_token != settings.tms_webhook_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token do TMS inválido")


@router.post("/romaneios", response_model=RomaneioOut, status_code=status.HTTP_201_CREATED)
def receber_romaneio(
    payload: dict,
    db: Session = Depends(get_db),
    _token_ok: None = Depends(_verificar_token),
) -> Romaneio:
    translator = get_tms_translator()
    comando = translator.to_romaneio_command(payload)

    try:
        return romaneio_service.criar_de_comando(
            db, comando=comando, origem=OrigemRomaneio.WEBHOOK_TMS, usuario_atual=None
        )
    except romaneio_service.RomaneioDuplicadoError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except romaneio_service.TransportadoraInvalidaError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
