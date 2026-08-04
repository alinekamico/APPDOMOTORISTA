from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.dependencies import require_roles
from app.db.session import get_db
from app.models.enums import OrigemResequenciamento, OrigemRomaneio, Papel
from app.models.motorista import Motorista
from app.models.romaneio import Romaneio
from app.models.usuario import Usuario
from app.repositories.tenant_scope import escopar_por_transportadora
from app.schemas.romaneio import (
    AlocarVeiculoMotoristaRequest,
    AlterarTransportadoraRequest,
    DefinirTransportadoraRequest,
    DevolverParaTransporteRequest,
    InserirPedidosRequest,
    ReportarProblemaRequest,
    ResequenciarRequest,
    RomaneioCriarRequest,
    RomaneioOut,
    RomaneioResumoOut,
)
from app.services import resequenciamento_service, romaneio_service, storage_service

router = APIRouter(prefix="/romaneios", tags=["romaneios"])

_EAGER_RELACIONAMENTOS = (
    joinedload(Romaneio.transportadora),
    joinedload(Romaneio.veiculo),
    joinedload(Romaneio.motorista).joinedload(Motorista.usuario),
)


def _buscar_romaneio_do_tenant(db: Session, romaneio_id: int, usuario_atual: Usuario) -> Romaneio:
    romaneio = db.get(Romaneio, romaneio_id)
    if romaneio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Romaneio não encontrado")
    if usuario_atual.papel != Papel.KAMI_ADMIN and romaneio.transportadora_id != usuario_atual.transportadora_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Romaneio não encontrado")
    return romaneio


@router.get("", response_model=list[RomaneioResumoOut])
def listar(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(require_roles(Papel.KAMI_ADMIN, Papel.TRANSPORTADORA_ADMIN)),
) -> list[Romaneio]:
    query = escopar_por_transportadora(
        select(Romaneio).options(*_EAGER_RELACIONAMENTOS), Romaneio.transportadora_id, usuario_atual
    )
    return list(db.scalars(query.order_by(Romaneio.criado_em.desc())).unique().all())


@router.get("/minha-rota", response_model=list[RomaneioResumoOut])
def minha_rota(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(require_roles(Papel.MOTORISTA)),
) -> list[Romaneio]:
    motorista = db.scalar(select(Motorista).where(Motorista.usuario_id == usuario_atual.id))
    if motorista is None:
        return []
    return romaneio_service.listar_para_motorista(db, motorista_id=motorista.id)


@router.post("/importar-uno")
def importar_uno(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(require_roles(Papel.KAMI_ADMIN)),
) -> dict:
    """Força uma sincronização imediata com a fonte externa (réplica do UNO no Supabase,
    enquanto o TMS não existe) — a sincronização automática já roda sozinha a cada 10
    minutos (ver `uno_sync_scheduler`); este endpoint é só pra não esperar o próximo ciclo."""
    resultado = romaneio_service.importar_de_fonte_externa(db, usuario_atual=usuario_atual)
    return resultado.to_dict()


@router.get("/{romaneio_id}", response_model=RomaneioOut)
def detalhar(
    romaneio_id: int,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(require_roles(Papel.KAMI_ADMIN, Papel.TRANSPORTADORA_ADMIN, Papel.MOTORISTA)),
) -> Romaneio:
    romaneio = romaneio_service.buscar_com_pedidos(db, romaneio_id)
    if romaneio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Romaneio não encontrado")
    if usuario_atual.papel != Papel.KAMI_ADMIN and romaneio.transportadora_id != usuario_atual.transportadora_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Romaneio não encontrado")
    if usuario_atual.papel == Papel.MOTORISTA:
        motorista = db.scalar(select(Motorista).where(Motorista.usuario_id == usuario_atual.id))
        if motorista is None or romaneio.motorista_id != motorista.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Romaneio não encontrado")
    return romaneio


@router.post("", response_model=RomaneioOut, status_code=status.HTTP_201_CREATED)
def criar_manual(
    payload: RomaneioCriarRequest,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(require_roles(Papel.KAMI_ADMIN)),
) -> Romaneio:
    """Simula a criação de romaneio pelo TMS — usado enquanto a integração real não existe."""
    try:
        return romaneio_service.criar_de_comando(
            db, comando=payload, origem=OrigemRomaneio.MANUAL_TESTE, usuario_atual=usuario_atual
        )
    except romaneio_service.RomaneioDuplicadoError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except romaneio_service.TransportadoraInvalidaError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.patch("/{romaneio_id}/transportadora", response_model=RomaneioOut)
def alterar_transportadora(
    romaneio_id: int,
    payload: AlterarTransportadoraRequest,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(require_roles(Papel.KAMI_ADMIN)),
) -> Romaneio:
    """KAMI corrige/reatribui qual transportadora vai atender o romaneio."""
    romaneio = _buscar_romaneio_do_tenant(db, romaneio_id, usuario_atual)
    try:
        return romaneio_service.alterar_transportadora(
            db,
            romaneio=romaneio,
            nova_transportadora_id=payload.transportadora_id,
            usuario_atual=usuario_atual,
        )
    except romaneio_service.TransicaoInvalidaError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except romaneio_service.TransportadoraInvalidaError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/{romaneio_id}/definir-transportadora", response_model=RomaneioOut)
def definir_transportadora(
    romaneio_id: int,
    payload: DefinirTransportadoraRequest,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(require_roles(Papel.KAMI_ADMIN)),
) -> Romaneio:
    """KAMI atribui a transportadora a um romaneio em 'definição da transportadora'."""
    romaneio = _buscar_romaneio_do_tenant(db, romaneio_id, usuario_atual)
    try:
        return romaneio_service.definir_transportadora_inicial(
            db, romaneio=romaneio, transportadora_id=payload.transportadora_id, usuario_atual=usuario_atual
        )
    except romaneio_service.TransicaoInvalidaError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except romaneio_service.TransportadoraInvalidaError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/{romaneio_id}/alocar", response_model=RomaneioOut)
def alocar(
    romaneio_id: int,
    payload: AlocarVeiculoMotoristaRequest,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(require_roles(Papel.TRANSPORTADORA_ADMIN)),
) -> Romaneio:
    romaneio = _buscar_romaneio_do_tenant(db, romaneio_id, usuario_atual)
    try:
        return romaneio_service.alocar_veiculo_motorista(
            db,
            romaneio=romaneio,
            veiculo_id=payload.veiculo_id,
            motorista_id=payload.motorista_id,
            usuario_atual=usuario_atual,
        )
    except romaneio_service.TransicaoInvalidaError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except romaneio_service.RecursoInvalidoError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/{romaneio_id}/devolver-para-transporte", response_model=RomaneioOut)
def devolver_para_transporte(
    romaneio_id: int,
    payload: DevolverParaTransporteRequest,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(require_roles(Papel.KAMI_ADMIN)),
) -> Romaneio:
    """KAMI, na conferência, devolve o romaneio para a transportadora ajustar veículo/motorista."""
    romaneio = _buscar_romaneio_do_tenant(db, romaneio_id, usuario_atual)
    try:
        return romaneio_service.devolver_para_definicao_transporte(
            db, romaneio=romaneio, usuario_atual=usuario_atual, observacao=payload.observacao
        )
    except romaneio_service.TransicaoInvalidaError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{romaneio_id}/confirmar-conferencia", response_model=RomaneioOut)
def confirmar_conferencia(
    romaneio_id: int,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(require_roles(Papel.KAMI_ADMIN)),
) -> Romaneio:
    romaneio = _buscar_romaneio_do_tenant(db, romaneio_id, usuario_atual)
    try:
        return romaneio_service.confirmar_conferencia_logistica(db, romaneio=romaneio, usuario_atual=usuario_atual)
    except romaneio_service.TransicaoInvalidaError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{romaneio_id}/carregamento/foto", response_model=RomaneioOut)
def enviar_foto_carregamento(
    romaneio_id: int,
    foto: UploadFile = File(...),
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(require_roles(Papel.MOTORISTA)),
) -> Romaneio:
    romaneio = _buscar_romaneio_do_tenant(db, romaneio_id, usuario_atual)

    motorista = db.scalar(select(Motorista).where(Motorista.usuario_id == usuario_atual.id))
    if motorista is None or romaneio.motorista_id != motorista.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Este romaneio não está alocado a você")

    foto_url = storage_service.salvar_arquivo(foto, subpasta="carregamento")
    try:
        return romaneio_service.adicionar_foto_carregamento(
            db, romaneio=romaneio, foto_url=foto_url, usuario_atual=usuario_atual
        )
    except romaneio_service.TransicaoInvalidaError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{romaneio_id}/carregamento/finalizar", response_model=RomaneioOut)
def finalizar_carregamento(
    romaneio_id: int,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(require_roles(Papel.MOTORISTA)),
) -> Romaneio:
    """Motorista confirma o fim do carregamento; o romaneio vai direto pra iniciar rota."""
    romaneio = _buscar_romaneio_do_tenant(db, romaneio_id, usuario_atual)

    motorista = db.scalar(select(Motorista).where(Motorista.usuario_id == usuario_atual.id))
    if motorista is None or romaneio.motorista_id != motorista.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Este romaneio não está alocado a você")

    try:
        return romaneio_service.finalizar_carregamento(db, romaneio=romaneio, usuario_atual=usuario_atual)
    except romaneio_service.TransicaoInvalidaError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except romaneio_service.EvidenciaObrigatoriaError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/{romaneio_id}/iniciar-rota", response_model=RomaneioOut)
def iniciar_rota(
    romaneio_id: int,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(require_roles(Papel.MOTORISTA)),
) -> Romaneio:
    romaneio = _buscar_romaneio_do_tenant(db, romaneio_id, usuario_atual)

    motorista = db.scalar(select(Motorista).where(Motorista.usuario_id == usuario_atual.id))
    if motorista is None or romaneio.motorista_id != motorista.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Este romaneio não está alocado a você")

    try:
        return romaneio_service.iniciar_rota(db, romaneio=romaneio, usuario_atual=usuario_atual)
    except romaneio_service.TransicaoInvalidaError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{romaneio_id}/finalizar", response_model=RomaneioOut)
def finalizar_romaneio(
    romaneio_id: int,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(require_roles(Papel.MOTORISTA)),
) -> Romaneio:
    romaneio = _buscar_romaneio_do_tenant(db, romaneio_id, usuario_atual)

    motorista = db.scalar(select(Motorista).where(Motorista.usuario_id == usuario_atual.id))
    if motorista is None or romaneio.motorista_id != motorista.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Este romaneio não está alocado a você")

    try:
        return romaneio_service.finalizar_romaneio(db, romaneio=romaneio, usuario_atual=usuario_atual)
    except romaneio_service.TransicaoInvalidaError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except romaneio_service.PedidosPendentesError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{romaneio_id}/pedidos", response_model=RomaneioOut)
def inserir_pedidos(
    romaneio_id: int,
    payload: InserirPedidosRequest,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(require_roles(Papel.KAMI_ADMIN)),
) -> Romaneio:
    """Regra 7: insere nova(s) parada(s) em um romaneio já em andamento (simula o TMS)."""
    romaneio = _buscar_romaneio_do_tenant(db, romaneio_id, usuario_atual)
    try:
        return romaneio_service.inserir_pedidos(
            db, romaneio=romaneio, novos_pedidos=payload.pedidos, usuario_atual=usuario_atual
        )
    except romaneio_service.TransicaoInvalidaError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{romaneio_id}/resequenciar", response_model=RomaneioOut)
def resequenciar(
    romaneio_id: int,
    payload: ResequenciarRequest,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(require_roles(Papel.MOTORISTA)),
) -> Romaneio:
    """Regra 4: o motorista pede um ajuste espontâneo da rota a partir da posição atual."""
    romaneio = _buscar_romaneio_do_tenant(db, romaneio_id, usuario_atual)

    motorista = db.scalar(select(Motorista).where(Motorista.usuario_id == usuario_atual.id))
    if motorista is None or romaneio.motorista_id != motorista.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Este romaneio não está alocado a você")

    try:
        return resequenciamento_service.resequenciar_pendentes(
            db,
            romaneio=romaneio,
            usuario_atual=usuario_atual,
            origem=OrigemResequenciamento.AJUSTE_ESPONTANEO,
            posicao_atual=(payload.posicao_lat, payload.posicao_lng),
        )
    except resequenciamento_service.SemCoordenadasError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/{romaneio_id}/reportar-problema", response_model=RomaneioOut)
def reportar_problema(
    romaneio_id: int,
    payload: ReportarProblemaRequest,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(require_roles(Papel.MOTORISTA)),
) -> Romaneio:
    """Motorista aciona romaneio_incompleto (entrega parcial por pane/saúde) ou romaneio_com_problema."""
    romaneio = _buscar_romaneio_do_tenant(db, romaneio_id, usuario_atual)

    motorista = db.scalar(select(Motorista).where(Motorista.usuario_id == usuario_atual.id))
    if motorista is None or romaneio.motorista_id != motorista.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Este romaneio não está alocado a você")

    try:
        return romaneio_service.reportar_problema(
            db,
            romaneio=romaneio,
            novo_status=payload.status,
            tipo_ocorrencia_id=payload.tipo_ocorrencia_id,
            observacao=payload.observacao,
            usuario_atual=usuario_atual,
        )
    except romaneio_service.TransicaoInvalidaError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
