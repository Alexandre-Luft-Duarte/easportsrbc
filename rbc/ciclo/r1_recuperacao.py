# -*- coding: utf-8 -*-
"""
================================================================================
 1o R - RECUPERACAO (Retrieve)
================================================================================

 A etapa mais importante do ciclo. Dado um problema novo, ela varre a base de
 casos e traz os K casos mais parecidos. Aqui ela tem duas partes:

  (A) FILTRAGEM POR RESTRICAO
      Antes de medir similaridade, eliminamos os casos que violam a restricao
      dura do problema: o orcamento. A literatura chama isso de "filtro" ou
      "pre-selecao".

      POR QUE ANTES DO KNN E NAO DEPOIS?
      Se filtrassemos depois, o KNN gastaria os K vizinhos com craques
      impagaveis (Mbappe, Haaland...) e sobrariam poucos - ou nenhum -
      candidatos viaveis. Filtrando antes, garantimos K sugestoes que o clube
      realmente pode contratar.

  (B) CALCULO DE SIMILARIDADE
      Cada jogador e um ponto num espaco de N dimensoes. Usamos o
      NearestNeighbors do scikit-learn com metric='euclidean' para achar os K
      pontos mais proximos de forma eficiente, e convertemos a distancia em
      um percentual de similaridade. Ver rbc/similaridade.py.
================================================================================
"""

from .. import config
from ..modelos import CasoRecuperado
from ..similaridade import para_similaridade
from ..interface import saida


def recuperar(base, espaco, problema, k=config.K_VIZINHOS, memoria=None):
    """
    Executa a etapa de Recuperacao.

    Devolve uma lista de CasoRecuperado ordenada do mais similar ao menos
    similar, ou None se nenhum caso couber no orcamento.
    """
    saida.cabecalho(">>> 1o R - RECUPERACAO (Retrieve)")

    # ==========================================================================
    # (A) FILTRO DE RESTRICAO: o orcamento
    # ==========================================================================
    mascara = base.mascara_orcamento(problema.orcamento)
    n_viaveis = int(mascara.sum())

    print("[A] Filtro de orcamento: ate " + saida.fmt_eur(problema.orcamento))
    print("    Base completa .............. " + saida.fmt_num(len(base)) + " casos")
    print("    Casos dentro do orcamento .. " + saida.fmt_num(n_viaveis) + " casos")
    print("    Descartados por preco ...... " + saida.fmt_num(len(base) - n_viaveis) + " casos")

    if n_viaveis == 0:
        print("\n    ! Nenhum jogador cabe nesse orcamento. Aumente o valor.")
        return None

    # ==========================================================================
    # (B) SIMILARIDADE VIA KNN (Distancia Euclidiana)
    # ==========================================================================
    # Recuperamos um conjunto maior quando ha memoria. O ranking tecnico e
    # entao ajustado pelo que o especialista aprovou ou rejeitou no passado.
    tamanho_pool = k
    ajustes_memoria = {}
    experiencias_usadas = 0
    if memoria is not None and len(memoria) > 0:
        tamanho_pool = k * config.FATOR_POOL_MEMORIA
        ajustes_memoria, experiencias_usadas = memoria.influencias(problema)

    distancias, posicoes = espaco.vizinhos_mais_proximos(
        problema, mascara, tamanho_pool
    )

    print("\n[B] KNN (metric='{}') analisando {} candidatos..."
          .format(config.METRICA, len(posicoes)))
    print("    Espaco de similaridade: {} dimensoes {}"
          .format(espaco.dimensoes, base.nomes_atributos))

    # As posicoes devolvidas pelo KNN sao relativas ao SUBCONJUNTO viavel,
    # entao precisamos traduzi-las de volta para as linhas da base original.
    df_viavel = base.df[mascara].reset_index(drop=True)

    recuperados = []
    for distancia, posicao in zip(distancias, posicoes):
        linha = df_viavel.iloc[posicao]
        similaridade_base = para_similaridade(float(distancia))
        nome = base.nome_de(linha)
        ajuste = ajustes_memoria.get(nome, 0.0)
        recuperados.append(
            CasoRecuperado(
                nome=nome,
                valor=float(linha[base.COL_VALOR]),
                distancia=float(distancia),
                similaridade=similaridade_base,
                atributos={p: int(linha[c]) for p, c in base.atributos.items()},
                ficha=base.ficha(linha),
                ajuste_memoria=ajuste,
            )
        )

    recuperados.sort(key=lambda caso: caso.pontuacao_ranking, reverse=True)
    recuperados = recuperados[:k]

    if memoria is not None:
        print("\n[C] Memoria RBC: {} caso(s) armazenado(s); "
              "{} experiencia(s) semelhante(s) aplicada(s)."
              .format(len(memoria), experiencias_usadas))
        if experiencias_usadas:
            print("    Aprovacoes reforcam e rejeicoes penalizam o ranking atual.")

    print("\n    Distancias euclidianas encontradas:")
    for posicao, caso in enumerate(recuperados, start=1):
        memoria_txt = ""
        if caso.ajuste_memoria:
            memoria_txt = "  |  memoria {:+.2f} p.p.".format(
                caso.ajuste_memoria * 100
            )
        print("      {}o vizinho -> d = {:.4f}  |  similaridade = {:5.2f}%{}"
              "  |  ranking = {:5.2f}%"
              .format(posicao, caso.distancia, caso.similaridade * 100,
                      memoria_txt, caso.pontuacao_ranking * 100))

    return recuperados
