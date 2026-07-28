from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import OrigemRomaneio, StatusRomaneio


class Romaneio(Base):
    __tablename__ = "romaneios"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(60), unique=True, nullable=False, index=True)
    # Nullable: um romaneio importado do UNO com CNPJ que ainda não bate com nenhuma
    # transportadora cadastrada entra sem transportadora, na etapa "definição da
    # transportadora" — a KAMI atribui manualmente até essa etapa virar automática.
    transportadora_id: Mapped[int | None] = mapped_column(ForeignKey("transportadoras.id"), nullable=True)
    transportadora_cnpj_externo: Mapped[str | None] = mapped_column(String(20), nullable=True)
    veiculo_id: Mapped[int | None] = mapped_column(ForeignKey("veiculos.id"), nullable=True)
    motorista_id: Mapped[int | None] = mapped_column(ForeignKey("motoristas.id"), nullable=True)

    status: Mapped[StatusRomaneio] = mapped_column(
        Enum(StatusRomaneio, native_enum=False, length=32),
        nullable=False,
        default=StatusRomaneio.DEFINICAO_TRANSPORTE,
    )
    origem: Mapped[OrigemRomaneio] = mapped_column(
        Enum(OrigemRomaneio, native_enum=False, length=32), nullable=False
    )
    tms_referencia_externa: Mapped[str | None] = mapped_column(String(120), nullable=True)

    tipo_ocorrencia_id: Mapped[int | None] = mapped_column(ForeignKey("tipos_ocorrencia.id"), nullable=True)
    observacao_ocorrencia: Mapped[str | None] = mapped_column(Text, nullable=True)

    qtd_caixas: Mapped[int | None] = mapped_column(Integer, nullable=True)
    qtd_pedidos: Mapped[int | None] = mapped_column(Integer, nullable=True)
    peso_total: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    # Logística — nunca valores monetários (isso não deve ser exposto pra transportadora/motorista)
    tipo_veiculo_sugerido: Mapped[str | None] = mapped_column(String(60), nullable=True)
    data_saida_prevista: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # De qual empresa do grupo KAMI (dentro do UNO) o romaneio saiu — o UNO tem 30+ empresas
    # cadastradas, então nome + UF ajudam a identificar de longe qual delas é.
    empresa_nome: Mapped[str | None] = mapped_column(String(120), nullable=True)
    empresa_uf: Mapped[str | None] = mapped_column(String(2), nullable=True)

    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    conferencia_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    carregamento_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    inicio_rota_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    concluido_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    transportadora: Mapped["Transportadora | None"] = relationship(back_populates="romaneios")
    veiculo: Mapped["Veiculo | None"] = relationship()
    motorista: Mapped["Motorista | None"] = relationship()
    pedidos: Mapped[list["Pedido"]] = relationship(back_populates="romaneio", cascade="all, delete-orphan")
    historico_etapas: Mapped[list["HistoricoEtapa"]] = relationship(
        back_populates="romaneio", cascade="all, delete-orphan"
    )
    resequenciamentos: Mapped[list["Resequenciamento"]] = relationship(
        back_populates="romaneio", cascade="all, delete-orphan"
    )
    fotos_carregamento: Mapped[list["FotoCarregamento"]] = relationship(
        back_populates="romaneio", cascade="all, delete-orphan", order_by="FotoCarregamento.criado_em"
    )

    @property
    def transportadora_nome(self) -> str | None:
        return self.transportadora.nome_fantasia if self.transportadora else None

    @property
    def motorista_nome(self) -> str | None:
        return self.motorista.nome if self.motorista else None

    @property
    def veiculo_placa(self) -> str | None:
        return self.veiculo.placa if self.veiculo else None
