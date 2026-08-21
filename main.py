# -*- coding: utf-8 -*-
"""
================================================================================
 OLHEIRO VIRTUAL - Sistema de Recomendacao de Contratacoes
 Raciocinio Baseado em Casos (RBC) aplicado ao dataset do FIFA
================================================================================

 O PROBLEMA
 ----------
 O clube quer um jogador com um perfil tecnico especifico, mas esse jogador e
 caro demais. O sistema busca, na base de jogadores, quem mais se PARECE com
 esse ideal e ao mesmo tempo CABE no orcamento disponivel.

 O QUE E RACIOCINIO BASEADO EM CASOS?
 ------------------------------------
 O RBC (Case-Based Reasoning) e um paradigma da IA Classica que resolve um
 problema NOVO recuperando problemas ANTIGOS parecidos e adaptando as solucoes
 que ja funcionaram. Nao ha "treinamento" de um modelo estatistico: o
 conhecimento fica armazenado, explicito e auditavel, na BASE DE CASOS.

 A analogia deste trabalho:
   * CASO          -> um jogador do dataset (atributos + preco)
   * PROBLEMA NOVO -> o perfil tecnico do jogador ideal (caro demais)
   * RESTRICAO     -> o orcamento maximo do clube
   * SOLUCAO       -> os jogadores similares e acessiveis encontrados

 ESTE ARQUIVO
 ------------
 Aqui esta apenas a ORQUESTRACAO do ciclo. A logica de cada etapa vive em
 rbc/ciclo/, um arquivo por R. Ler este main de cima a baixo deve bastar para
 entender o fluxo completo do RBC.

 Execucao:  python main.py
================================================================================
"""

from rbc import config
from rbc.base_casos import BaseDeCasos, localizar_dataset
from rbc.similaridade import EspacoDeSimilaridade
from rbc.interface import entrada, saida

# Os 4 Rs do ciclo, importados na ordem em que sao executados
from rbc.ciclo import recuperar, reutilizar, revisar, reter, MemoriaDeCasos


def preparar():
    """
    PASSO 0 - Preparacao.

    Carrega a base de casos (players_22.csv) e constroi o espaco de
    similaridade. Isso e feito UMA vez: a base nao muda entre consultas, entao
    nao ha por que reprocessar 17 mil jogadores a cada pergunta.
    """
    base = BaseDeCasos.carregar(localizar_dataset())
    saida.resumo_base(base)

    espaco = EspacoDeSimilaridade(base)
    return base, espaco


def executar_ciclo(base, espaco, memoria):
    """
    Roda UMA volta completa do ciclo dos 4 Rs.

    Quem pergunta se o usuario quer continuar e o main(), uma unica vez. Se
    nenhum caso cabe no orcamento a volta termina mais cedo: nao ha o que
    reutilizar, revisar nem reter.
    """
    # ---- descricao do problema novo -------------------------------------
    problema = entrada.montar_problema(base)

    # ================= 1o R - RECUPERACAO =================================
    recuperados = recuperar(
        base, espaco, problema, memoria=memoria, k=config.K_VIZINHOS
    )
    if recuperados is None:
        # Sem candidatos nao ha ciclo a completar: encerra a volta aqui.
        return

    # ================= 2o R - REUTILIZACAO ================================
    reutilizar(recuperados, problema)

    # ================= 3o R - REVISAO =====================================
    avaliacao = revisar(recuperados)

    # ================= 4o R - RETENCAO ====================================
    reter(memoria, problema, recuperados, avaliacao)


def main():
    saida.configurar_console()
    saida.banner()

    # A memoria e carregada ANTES de tudo: o sistema comeca ja sabendo o que
    # aprendeu nas execucoes anteriores. Essa e a aprendizagem incremental.
    memoria = MemoriaDeCasos().carregar()

    base, espaco = preparar()

    # O ciclo do RBC e continuo: cada consulta resolvida enriquece a base de
    # conhecimento, que fica disponivel para a proxima.
    while True:
        executar_ciclo(base, espaco, memoria)
        if not entrada.confirmar("\nFazer nova busca?"):
            break

    saida.encerramento(memoria)


if __name__ == "__main__":
    main()
