export type StatusRomaneio =
  | "definicao_transportadora"
  | "definicao_transporte"
  | "conferencia_logistica"
  | "carregamento"
  | "inicio_rota"
  | "em_transito"
  | "concluido"
  | "romaneio_incompleto"
  | "romaneio_com_problema";

export type RomaneioResumo = {
  id: number;
  codigo: string;
  transportadora_id: number | null;
  transportadora_nome: string | null;
  transportadora_cnpj_externo?: string | null;
  veiculo_id: number | null;
  veiculo_placa: string | null;
  motorista_id: number | null;
  motorista_nome: string | null;
  status: StatusRomaneio;
  qtd_caixas: number | null;
  qtd_pedidos: number | null;
  peso_total: number | null;
  tipo_veiculo_sugerido: string | null;
  data_saida_prevista: string | null;
  empresa_nome?: string | null;
  empresa_uf?: string | null;
  criado_em: string;
};

export const COLUNAS: { status: StatusRomaneio; titulo: string; responsavel: string }[] = [
  { status: "definicao_transportadora", titulo: "Definição da Transportadora", responsavel: "KAMI" },
  { status: "definicao_transporte", titulo: "Definição de Transporte", responsavel: "Transportadora" },
  { status: "conferencia_logistica", titulo: "Conferência Logística", responsavel: "KAMI" },
  { status: "carregamento", titulo: "Carregamento", responsavel: "Motorista" },
  { status: "inicio_rota", titulo: "Início de Rota", responsavel: "Motorista" },
  { status: "em_transito", titulo: "Em Trânsito", responsavel: "Motorista" },
  { status: "concluido", titulo: "Concluído", responsavel: "Sistema" },
  { status: "romaneio_incompleto", titulo: "Romaneio Incompleto", responsavel: "Motorista" },
  { status: "romaneio_com_problema", titulo: "Romaneio c/ Problema", responsavel: "Motorista" },
];
