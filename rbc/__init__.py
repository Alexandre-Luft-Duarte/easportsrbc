# -*- coding: utf-8 -*-
"""
Pacote RBC - Olheiro Virtual.

Sistema de Recomendacao de Contratacoes baseado em Raciocinio Baseado em Casos
(Case-Based Reasoning), aplicado ao dataset do FIFA.

Organizacao do pacote:

    config.py         parametros, caminhos e mapeamento de colunas
    modelos.py        Problema, CasoRecuperado, Avaliacao, CasoAprendido
    base_casos.py     a Case Base: carga, limpeza e consulta do dataset
    similaridade.py   normalizacao, distancia euclidiana e KNN
    ciclo/            um arquivo para cada R do ciclo
    interface/        entrada e saida de terminal
"""

__version__ = "2.0.0"
