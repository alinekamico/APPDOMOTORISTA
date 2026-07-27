from pydantic import BaseModel


class VeiculoCreate(BaseModel):
    placa: str
    tipo: str
    capacidade_kg: float | None = None


class VeiculoUpdate(BaseModel):
    tipo: str | None = None
    capacidade_kg: float | None = None
    ativo: bool | None = None


class VeiculoOut(BaseModel):
    id: int
    transportadora_id: int
    transportadora_nome: str
    placa: str
    tipo: str
    capacidade_kg: float | None
    ativo: bool

    model_config = {"from_attributes": True}
