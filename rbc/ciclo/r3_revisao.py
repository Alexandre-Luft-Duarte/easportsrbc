# -*- coding: utf-8 -*-
"""
================================================================================
 3o R - REVISAO (Revise)
================================================================================

 O RBC NAO confia cegamente na solucao recuperada. A etapa de Revisao coloca o
 especialista humano - aqui, o diretor de futebol / olheiro do clube - dentro do
 circuito para avaliar, corrigir ou rejeitar a sugestao.

 POR QUE ISSO IMPORTA?
 ---------------------
 E o que caracteriza o RBC como SISTEMA DE APOIO A DECISAO, e nao como uma
 caixa-preta. A maquina calcula similaridade tecnica; o humano traz o que os
 numeros nao capturam: idade, contrato, adaptacao cultural, indisciplina,
 esquema tatico do clube. A avaliacao produzida aqui e o que da CONFIANCA ao
 caso que sera guardado na etapa seguinte.

 Em sistemas reais, esta etapa muitas vezes e automatizada por simulacao. Neste
 trabalho ela e simulada por input() no terminal.
================================================================================
"""

from ..modelos import Avaliacao
from ..interface import saida, entrada


def revisar(recuperados):
    """
    Coleta o veredito do especialista humano sobre a solucao sugerida.

    Devolve um objeto Avaliacao.
    """
    saida.cabecalho(">>> 3o R - REVISAO (Revise)")
    print("Avaliacao do ESPECIALISTA HUMANO (voce, o olheiro do clube).\n")

    for posicao, caso in enumerate(recuperados, start=1):
        print("   {}) {:<28} {:>18}  ({:.2f}% similar)"
              .format(posicao, caso.nome, saida.fmt_eur(caso.valor),
                      caso.similaridade * 100))

    print("\n   0) Nenhum serve - rejeitar a sugestao")

    escolha = entrada.ler_opcao(
        "\n   A sugestao faz sentido? Escolha o jogador aprovado",
        minimo=0,
        maximo=len(recuperados),
    )

    # ------------------------------------------------------------------
    # CAMINHO 1: o especialista REJEITOU a sugestao
    # ------------------------------------------------------------------
    if escolha == 0:
        motivo = input("   Por que a sugestao falhou? ").strip()
        print("\n   >> Sugestao REJEITADA pelo especialista.")
        return Avaliacao(aprovado=False, obs=motivo)

    # ------------------------------------------------------------------
    # CAMINHO 2: o especialista APROVOU um dos candidatos
    # ------------------------------------------------------------------
    escolhido = recuperados[escolha - 1]
    nota = entrada.ler_inteiro("   Nota para a recomendacao", 0, 10, padrao=8)
    obs = input("   Observacoes do olheiro (opcional): ").strip()

    print("\n   >> Sugestao APROVADA: {} (nota {}/10)".format(escolhido.nome, nota))

    return Avaliacao(
        aprovado=True,
        escolhido=escolhido.nome,
        indice=escolha - 1,
        nota=nota,
        obs=obs,
    )
