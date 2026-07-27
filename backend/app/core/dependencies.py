from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.enums import Papel
from app.models.usuario import Usuario

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    try:
        payload = decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas ou expiradas",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    usuario_id = payload.get("sub")
    usuario = db.get(Usuario, int(usuario_id)) if usuario_id else None
    if usuario is None or not usuario.ativo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário inválido ou inativo")
    return usuario


def require_roles(*papeis: Papel) -> Callable[[Usuario], Usuario]:
    def _checker(usuario: Usuario = Depends(get_current_user)) -> Usuario:
        if usuario.papel not in papeis:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário não tem permissão para esta ação",
            )
        return usuario

    return _checker


def tenant_scope(usuario: Usuario) -> int | None:
    """Retorna o transportadora_id para escopo de query, ou None se o usuário enxerga tudo (kami_admin)."""
    if usuario.papel == Papel.KAMI_ADMIN:
        return None
    return usuario.transportadora_id
