# -*- coding: utf-8 -*-
"""
MEDIDA DE SIMILARIDADE - a matematica por tras da RECUPERACAO.

Este modulo isola tudo que diz respeito a "o quao parecidos sao dois casos".
Manter isso separado da etapa de Recuperacao tem uma razao didatica: mostra que
a metrica de similaridade e uma PECA TROCAVEL do RBC. Trocar euclidiana por
Manhattan ou por uma similaridade ponderada nao exige mexer no ciclo.
"""

import numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import MinMaxScaler

from . import config


# ==============================================================================
# POR QUE NORMALIZAR?
# ------------------------------------------------------------------------------
# A Distancia Euclidiana soma as diferencas ao quadrado em cada eixo:
#
#       d(q, c) = raiz( (q1-c1)^2 + (q2-c2)^2 + ... + (qN-cN)^2 )
#
# Se um atributo variasse de 0 a 100 e outro de 0 a 5, o primeiro dominaria a
# conta inteira e o segundo seria praticamente ignorado. Por isso levamos tudo
# ao intervalo [0, 1] com o MinMaxScaler. Como os 6 atributos do FIFA ja vao de
# 0 a 100, isso tambem garante que cada um pese exatamente o mesmo na nocao de
# "parecido" - ou seja, uma similaridade sem vies de escala.
# ==============================================================================

class EspacoDeSimilaridade:
    """
    Representa a base de casos como pontos num espaco N-dimensional
    e sabe encontrar os vizinhos mais proximos de um problema novo.
    """

    def __init__(self, base):
        self.base = base
        self.scaler = MinMaxScaler()
        # Cada caso vira um vetor normalizado - o "DNA tecnico" do jogador.
        self.matriz = self.scaler.fit_transform(base.matriz_atributos())

    @property
    def dimensoes(self):
        """Quantos eixos tem o espaco de similaridade."""
        return self.matriz.shape[1]

    def vetorizar_problema(self, problema):
        """
        Projeta o perfil desejado no MESMO espaco da base de casos.

        Usar transform (e nao fit_transform) e essencial: o problema precisa
        passar pela normalizacao ja aprendida na base, senao estariamos
        comparando escalas diferentes.
        """
        vetor = np.array([problema.como_vetor(self.base.nomes_atributos)], dtype=float)
        return self.scaler.transform(vetor)

    def vizinhos_mais_proximos(self, problema, indices_validos, k):
        """
        Executa o KNN sobre um SUBCONJUNTO da base (os casos viaveis).

        Recebe indices_validos (mascara booleana) porque a restricao de
        orcamento ja eliminou os casos inviaveis antes da busca - ver a
        explicacao na etapa de Recuperacao.

        Devolve (distancias, posicoes_no_subconjunto).
        """
        submatriz = self.matriz[indices_validos]
        k_efetivo = min(k, len(submatriz))

        modelo = NearestNeighbors(
            n_neighbors=k_efetivo,
            metric=config.METRICA,   # <<< "euclidean": o coracao da similaridade
            algorithm="auto",        # sklearn escolhe kd_tree / ball_tree / brute
        )
        modelo.fit(submatriz)

        distancias, posicoes = modelo.kneighbors(self.vetorizar_problema(problema))
        return distancias[0], posicoes[0]


# ==============================================================================
# CONVERSAO DISTANCIA -> SIMILARIDADE
# ==============================================================================

def para_similaridade(distancia):
    """
    Converte distancia em similaridade normalizada.

        similaridade = 1 / (1 + d)

    Propriedades desejaveis desta formula:
      * d = 0  (caso identico)   -> similaridade = 1.0  (100%)
      * d cresce                 -> similaridade cai suavemente rumo a 0
      * nunca divide por zero, e o resultado fica sempre em (0, 1]
    """
    return 1.0 / (1.0 + distancia)
