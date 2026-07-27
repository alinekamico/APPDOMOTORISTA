from app.services.resequenciamento_service import calcular_sequencia_otima


def test_sequencia_vazia_quando_sem_paradas():
    assert calcular_sequencia_otima([[0.0]]) == []


def test_parada_unica():
    matriz = [[0.0, 5.0], [5.0, 0.0]]
    assert calcular_sequencia_otima(matriz) == [1]


def test_escolhe_ordem_que_minimiza_tempo_total():
    # Posição atual (0) próxima do ponto 1 (5min), ponto 2 está longe de tudo (50min),
    # ponto 3 está entre 1 e 2. A rota ótima é 0 -> 1 -> 3 -> 2, não 0 -> 2 -> 1 -> 3.
    matriz = [
        [0.0, 5.0, 50.0, 20.0],
        [5.0, 0.0, 30.0, 10.0],
        [50.0, 30.0, 0.0, 15.0],
        [20.0, 10.0, 15.0, 0.0],
    ]

    rota = calcular_sequencia_otima(matriz)

    assert set(rota) == {1, 2, 3}

    def custo(ordem):
        pontos = [0, *ordem]
        return sum(matriz[pontos[i]][pontos[i + 1]] for i in range(len(pontos) - 1))

    # a rota encontrada não pode ser pior que a ordem "ingênua" 1,2,3
    assert custo(rota) <= custo([1, 2, 3])


def test_2opt_melhora_rota_nearest_neighbor_gulosa():
    # Caso clássico onde nearest-neighbor puro erra: 0 -> 1 é o mais perto, mas isso
    # deixa uma volta cara no final. O 2-opt deve corrigir.
    matriz = [
        [0, 1, 10, 10],
        [1, 0, 10, 2],
        [10, 10, 0, 1],
        [10, 2, 1, 0],
    ]

    rota = calcular_sequencia_otima(matriz)

    def custo(ordem):
        pontos = [0, *ordem]
        return sum(matriz[pontos[i]][pontos[i + 1]] for i in range(len(pontos) - 1))

    melhor_possivel = min(
        custo([1, 2, 3]),
        custo([1, 3, 2]),
        custo([2, 1, 3]),
        custo([2, 3, 1]),
        custo([3, 1, 2]),
        custo([3, 2, 1]),
    )
    assert custo(rota) == melhor_possivel
