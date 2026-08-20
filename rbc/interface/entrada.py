# -*- coding: utf-8 -*-
"""
Camada de ENTRADA - coleta e valida tudo que o usuario digita.

Toda leitura de terminal fica concentrada aqui. Isso mantem o ciclo RBC livre de
chamadas a input(), e centraliza a validacao num lugar so.
"""

from .. import config
from ..modelos import Problema
from . import saida


# ==============================================================================
# LEITORES BASICOS (com validacao e valor padrao)
# ==============================================================================

def ler_inteiro(mensagem, minimo, maximo, padrao):
    """Le um inteiro dentro de uma faixa. Enter aceita o valor padrao."""
    while True:
        texto = input("{} [{}-{}] (Enter = {}): "
                      .format(mensagem, minimo, maximo, padrao)).strip()
        if texto == "":
            return padrao
        try:
            valor = int(float(texto.replace(",", ".")))
        except ValueError:
            print("   ! Digite um numero.")
            continue
        if minimo <= valor <= maximo:
            return valor
        print("   ! Valor fora da faixa {}-{}.".format(minimo, maximo))


def ler_opcao(mensagem, minimo, maximo):
    """Le uma escolha de menu (sem valor padrao - a escolha e obrigatoria)."""
    while True:
        texto = input("{}: ".format(mensagem)).strip()
        if texto.isdigit() and minimo <= int(texto) <= maximo:
            return int(texto)
        print("   ! Opcao invalida.")


def ler_monetario(mensagem, padrao):
    """Le um valor em euros. Aceita '15000000', '15.000.000' ou Enter."""
    while True:
        texto = input("{} (Enter = {}): "
                      .format(mensagem, saida.fmt_num(padrao))).strip()
        if texto == "":
            return padrao
        try:
            return float(texto.replace(".", "").replace(",", "."))
        except ValueError:
            print("   ! Digite um numero.")


def confirmar(mensagem):
    """Pergunta sim/nao. Qualquer coisa que nao comece com 's' e nao."""
    return input("{} (s/n): ".format(mensagem)).strip().lower().startswith("s")


# ==============================================================================
# SELECAO DA BASE DE CASOS
# ==============================================================================

def escolher_dataset(csvs):
    """
    Menu de escolha da temporada.

    Cada CSV e uma base de casos diferente: os mesmos jogadores, mas com
    atributos e precos daquele ano.
    """
    if len(csvs) == 1:
        return csvs[0]

    print("\nBases de casos disponiveis (uma por temporada do FIFA):")
    for i, caminho in enumerate(csvs, start=1):
        print("   {}) {}".format(i, caminho.name))

    padrao = len(csvs)   # a ultima em ordem alfabetica = temporada mais recente
    while True:
        texto = input("\nEscolha a temporada [1-{}] (Enter = {}): "
                      .format(len(csvs), csvs[padrao - 1].name)).strip()
        if texto == "":
            return csvs[padrao - 1]
        if texto.isdigit() and 1 <= int(texto) <= len(csvs):
            return csvs[int(texto) - 1]
        print("   ! Opcao invalida.")


# ==============================================================================
# DESCRICAO DO PROBLEMA NOVO
# ------------------------------------------------------------------------------
# O usuario descreve o jogador dos sonhos - aquele que o clube nao pode pagar -
# e informa quanto dinheiro tem em caixa. Esse par (perfil, orcamento) e o
# PROBLEMA que o ciclo RBC vai resolver.
# ==============================================================================

def montar_problema(base):
    """Coleta o perfil-alvo + a restricao de orcamento e devolve um Problema."""
    saida.cabecalho("NOVO PROBLEMA - PERFIL DO JOGADOR IDEAL")
    print("Descreva o jogador que voce QUERIA contratar (atributos de 0 a 100).")
    print("Pressione Enter para aceitar o valor sugerido.\n")

    perfil = {}
    for papel in base.nomes_atributos:      # so pergunta o que existe no CSV
        perfil[papel] = ler_inteiro(
            "  {:<12}".format(papel.capitalize()),
            minimo=0,
            maximo=100,
            padrao=config.PERFIL_PADRAO.get(papel, 70),
        )

    print()
    print("  Agora a restricao: quanto o clube pode gastar?")
    orcamento = ler_monetario("  Orcamento MAXIMO (EUR)", config.ORCAMENTO_PADRAO)

    return Problema(perfil_desejado=perfil, orcamento=orcamento)
