import unittest

import numpy as np
import pandas as pd

from rbc.ciclo.r1_recuperacao import recuperar
from rbc.ciclo.r4_retencao import MemoriaDeCasos
from rbc.modelos import Problema


class BaseFalsa:
    COL_VALOR = "_valor"

    def __init__(self):
        self.atributos = {"velocidade": "velocidade"}
        self.df = pd.DataFrame([
            {"nome": "Jogador A", "_valor": 100.0, "velocidade": 90},
            {"nome": "Jogador B", "_valor": 100.0, "velocidade": 89},
        ])

    def __len__(self):
        return len(self.df)

    @property
    def nomes_atributos(self):
        return list(self.atributos)

    def mascara_orcamento(self, orcamento):
        return (self.df[self.COL_VALOR] <= orcamento).to_numpy()

    def nome_de(self, linha):
        return linha["nome"]

    def ficha(self, linha):
        return {}


class EspacoFalso:
    dimensoes = 1

    def vizinhos_mais_proximos(self, problema, mascara, k):
        # A comeca ligeiramente na frente de B no ranking puramente tecnico.
        return np.array([0.10, 0.11]), np.array([0, 1])


def caso_aprendido(tipo, escolhido=None, solucoes=None, nota=10):
    return {
        "tipo": tipo,
        "problema": {"perfil_desejado": {"velocidade": 90}},
        "solucao_sugerida": [
            {"nome": nome} for nome in (solucoes or [])
        ],
        "avaliacao_especialista": {
            "escolhido": escolhido,
            "nota": nota,
        },
    }


class TesteAprendizadoNaRecuperacao(unittest.TestCase):
    def setUp(self):
        self.base = BaseFalsa()
        self.espaco = EspacoFalso()
        self.problema = Problema({"velocidade": 90}, orcamento=1000.0)

    def test_aprovacao_anterior_reforca_jogador(self):
        memoria = MemoriaDeCasos()
        memoria.casos = [
            caso_aprendido("caso_de_sucesso", escolhido="Jogador B")
        ]

        resultado = recuperar(
            self.base, self.espaco, self.problema, k=2, memoria=memoria
        )

        self.assertEqual("Jogador B", resultado[0].nome)
        self.assertGreater(resultado[0].ajuste_memoria, 0)

    def test_rejeicao_anterior_penaliza_lista_que_falhou(self):
        memoria = MemoriaDeCasos()
        memoria.casos = [
            caso_aprendido("caso_de_falha", solucoes=["Jogador A"])
        ]

        resultado = recuperar(
            self.base, self.espaco, self.problema, k=2, memoria=memoria
        )

        self.assertEqual("Jogador B", resultado[0].nome)
        jogador_a = next(c for c in resultado if c.nome == "Jogador A")
        self.assertLess(jogador_a.ajuste_memoria, 0)


if __name__ == "__main__":
    unittest.main()
