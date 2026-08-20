# -*- coding: utf-8 -*-
"""
================================================================================
 2o R - REUTILIZACAO (Reuse)
================================================================================

 Reutilizar = pegar a solucao dos casos recuperados e propo-la como solucao do
 problema novo. Aqui a "solucao" e a lista de jogadores substitutos.

 ADAPTACAO
 ---------
 O RBC raramente reaproveita uma solucao antiga sem ajuste. A sub-etapa de
 adaptacao (adaptation) transforma a solucao recuperada para caber no contexto
 do problema novo. Como nao podemos "editar" um jogador real, nossa adaptacao e
 INFORMACIONAL: calculamos e exibimos, para cada candidato,

   * o DELTA de cada atributo em relacao ao ideal  -> o que se ganha e se perde
   * a ECONOMIA gerada em relacao ao orcamento     -> o que sobra em caixa

 Isso transforma uma lista crua de nomes numa recomendacao que o especialista
 humano consegue de fato julgar na proxima etapa.
================================================================================
"""

from ..interface import saida


def reutilizar(recuperados, problema):
    """
    Exibe os casos recuperados como a solucao sugerida, ja adaptada.

    Devolve a mesma lista, para encadear com a etapa de Revisao.
    """
    saida.cabecalho(">>> 2o R - REUTILIZACAO (Reuse)")
    print("Solucao sugerida: jogadores similares ao ideal e dentro do orcamento.\n")

    for posicao, caso in enumerate(recuperados, start=1):
        saida.linha()
        print("  #{}  {}   |   SIMILARIDADE: {:.2f}%"
              .format(posicao, caso.nome, caso.similaridade * 100))

        # ---- ficha descritiva -------------------------------------------
        rotulos = {
            "idade": "Idade",
            "clube": "Clube",
            "posicao": "Posicao",
            "overall": "Overall",
            "potencial": "Potencial",
        }
        campos = [
            "{}: {}".format(rotulos[papel], valor)
            for papel, valor in caso.ficha.items()
            if papel in rotulos
        ]
        if campos:
            print("      " + "  |  ".join(campos))

        # ---- adaptacao 1: impacto financeiro ----------------------------
        print("      Valor de mercado: " + saida.fmt_eur(caso.valor)
              + "   (sobra no caixa: "
              + saida.fmt_eur(caso.economia(problema.orcamento)) + ")")

        # ---- adaptacao 2: o que se ganha e o que se perde ---------------
        print("      Atributos (alvo -> encontrado):")
        comparacoes = []
        for papel, encontrado in caso.atributos.items():
            desejado = problema.perfil_desejado[papel]
            delta = encontrado - desejado
            sinal = "+" if delta > 0 else ""
            comparacoes.append("{}: {}->{} ({}{})"
                               .format(papel[:4], desejado, encontrado, sinal, delta))
        print("        " + " | ".join(comparacoes))

    saida.linha()
    return recuperados
