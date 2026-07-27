from sqlalchemy import Select

from app.core.dependencies import tenant_scope
from app.models.usuario import Usuario


def escopar_por_transportadora(query: Select, coluna, usuario: Usuario) -> Select:
    """Aplica `WHERE coluna = transportadora_id` a menos que o usuário seja kami_admin (enxerga tudo).

    Centralizado aqui para que nenhuma query de listagem/detalhe precise repetir essa checagem —
    evita vazamento de dado entre transportadoras por esquecimento em algum router/service.
    """
    transportadora_id = tenant_scope(usuario)
    if transportadora_id is None:
        return query
    return query.where(coluna == transportadora_id)
