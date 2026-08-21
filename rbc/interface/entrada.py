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


def _texto_para_float(texto):
    """
    Converte o que o usuario digitou num numero, no padrao pt-BR.

    O ponto e AMBIGUO em portugues: em "2.500.000" e separador de milhar, mas
    em "2500000.75" e separador decimal. Trocar cego todo ponto por nada (ou
    por virgula) faz "2500000.75" virar 250000075 - cem vezes maior, e sem
    aviso nenhum. Como o valor lido aqui e o ORCAMENTO, ou seja, a restricao
    dura do problema, o erro se propagaria por todo o ciclo. Por isso o caso
    e desambiguado explicitamente:

        "2.500.000"     dois ou mais pontos      -> milhar    -> 2500000.0
        "1.234.567,89"  tem ponto E virgula      -> pt-BR     -> 1234567.89
        "2500000,75"    so virgula               -> decimal   -> 2500000.75
        "2.500"         um ponto, 3 casas depois -> milhar    -> 2500.0
        "2500000.75"    um ponto, ate 2 casas    -> decimal   -> 2500000.75
    """
    texto = texto.strip().replace(" ", "")
    for simbolo in ("EUR", "eur", "R$", "€", "$"):
        texto = texto.replace(simbolo, "")

    tem_virgula = "," in texto
    pontos = texto.count(".")

    if tem_virgula and pontos:
        texto = texto.replace(".", "").replace(",", ".")
    elif tem_virgula:
        texto = texto.replace(",", ".")
    elif pontos > 1:
        texto = texto.replace(".", "")
    elif pontos == 1 and len(texto.split(".")[1]) == 3:
        # "2.500": 3 digitos depois do ponto e agrupamento de milhar em pt-BR.
        texto = texto.replace(".", "")

    return float(texto)


def ler_monetario(mensagem, padrao):
    """Le um valor em euros. Aceita '15000000', '15.000.000', '15000000,50'."""
    while True:
        texto = input("{} (Enter = {}): "
                      .format(mensagem, saida.fmt_num(padrao))).strip()
        if texto == "":
            return padrao
        try:
            valor = _texto_para_float(texto)
        except ValueError:
            print("   ! Digite um numero.")
            continue
        if valor <= 0:
            print("   ! O orcamento precisa ser maior que zero.")
            continue
        return valor


def confirmar(mensagem):
    """Pergunta sim/nao. Qualquer coisa que nao comece com 's' e nao."""
    return input("{} (s/n): ".format(mensagem)).strip().lower().startswith("s")


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
