# -*- coding: utf-8 -*-
"""
Camada de SAIDA - tudo que o sistema imprime no terminal.

Separar apresentacao da logica e o que permite, no futuro, trocar o terminal por
uma interface web ou por uma API sem tocar em uma linha do ciclo RBC.
"""

import sys

LARGURA = 78


def configurar_console():
    """
    Forca a saida para UTF-8.

    O dataset do FIFA e UTF-8 e tem muitos nomes acentuados (Suarez, Mbappe,
    Balde...). O console do Windows costuma usar cp1252 e quebraria esses
    caracteres na impressao.
    """
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass


# ==============================================================================
# FORMATACAO
# ==============================================================================

def fmt_num(valor):
    """Formata inteiro com ponto como separador de milhar (padrao pt-BR)."""
    return "{:,}".format(int(valor)).replace(",", ".")


def fmt_eur(valor):
    """Formata um valor monetario em euros no padrao pt-BR."""
    return "EUR " + fmt_num(round(valor))


# ==============================================================================
# BLOCOS VISUAIS
# ==============================================================================

def linha(simbolo="-"):
    """Divisoria simples."""
    print(simbolo * LARGURA)


def cabecalho(titulo, simbolo="="):
    """Cabecalho de secao - deixa cada etapa do ciclo RBC visivel na execucao."""
    print("\n" + simbolo * LARGURA)
    print(" " + titulo)
    print(simbolo * LARGURA)


def banner():
    """Abertura do programa."""
    print("\n" + "#" * LARGURA)
    print("#" + " OLHEIRO VIRTUAL ".center(LARGURA - 2) + "#")
    print("#" + " Sistema de Recomendacao de Contratacoes ".center(LARGURA - 2) + "#")
    print("#" + " Raciocinio Baseado em Casos (RBC) ".center(LARGURA - 2) + "#")
    print("#" + "-" * (LARGURA - 2) + "#")
    print("#" + " Ciclo dos 4 Rs: Recuperacao > Reutilizacao > Revisao > Retencao "
          .center(LARGURA - 2) + "#")
    print("#" * LARGURA)


def resumo_base(base):
    """Relata o que foi carregado da base de casos."""
    cabecalho("PASSO 0 - CARREGANDO A BASE DE CASOS")
    print("Arquivo: " + base.origem.name)
    print("Registros brutos: " + fmt_num(base.brutos))

    print("\nAtributos usados no calculo de SIMILARIDADE:")
    for papel, coluna in base.atributos.items():
        print("   - {:<12} -> coluna '{}'".format(papel, coluna))

    print("\nColuna de orcamento (preco) -> '{}'".format(base.mapa["valor"]))

    print("\nCasos validos apos limpeza: " + fmt_num(len(base))
          + "  (removidos " + fmt_num(base.removidos) + ")")
    print("   Os removidos sao, em sua maioria, goleiros: eles nao possuem")
    print("   estes 6 atributos no dataset, e compara-los com jogadores de")
    print("   linha nao produziria similaridade util.")


def encerramento(memoria):
    """Fecha o programa com o balanco do conhecimento acumulado."""
    sucessos, falhas = memoria.resumo()
    cabecalho("FIM DO CICLO RBC", "#")
    print("Casos na base de conhecimento: {} ({} sucesso(s), {} falha(s))"
          .format(len(memoria), sucessos, falhas))
    print("Obrigado por usar o Olheiro Virtual.\n")
