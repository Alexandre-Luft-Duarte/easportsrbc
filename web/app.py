# -*- coding: utf-8 -*-
"""
================================================================================
 OLHEIRO VIRTUAL - Interface WEB
================================================================================

 Esta e a MESMA aplicacao do main.py, com outra camada de apresentacao.

 O pacote rbc/ nao foi alterado em nenhuma linha para que esta interface
 existisse. Isso e a demonstracao pratica da separacao que o projeto propoe:

   * rbc/base_casos.py            -> REUTILIZADO tal como esta
   * rbc/similaridade.py          -> REUTILIZADO tal como esta
   * rbc/ciclo/r1_recuperacao.py  -> REUTILIZADO tal como esta
   * rbc/ciclo/r4_retencao.py     -> REUTILIZADO tal como esta

   * rbc/ciclo/r2_reutilizacao.py -> reescrito em HTML (era so apresentacao)
   * rbc/ciclo/r3_revisao.py      -> reescrito em HTML (era so input())
   * rbc/interface/               -> substituido por templates/

 O 2o e o 3o R nao sao "logica de raciocinio": o R2 apenas EXIBE a adaptacao e
 o R3 apenas COLETA o veredito humano. Trocar terminal por navegador troca
 exatamente esses dois, e mais nada. O raciocinio (R1 e R4) fica intacto.

 Execucao:  python web/app.py    ->  http://127.0.0.1:5000
================================================================================
"""

import contextlib
import io
import sys
import uuid
from pathlib import Path

# Permite rodar como "python web/app.py" a partir de qualquer pasta.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask, redirect, render_template, request, url_for

from rbc import config
from rbc.base_casos import BaseDeCasos, localizar_dataset
from rbc.ciclo import recuperar, reter, MemoriaDeCasos
from rbc.modelos import Avaliacao, Problema
from rbc.similaridade import EspacoDeSimilaridade

app = Flask(__name__)


def _silencioso(funcao, *args, **kwargs):
    """
    Executa uma etapa do ciclo capturando o que ela imprimiria no terminal.

    As funcoes do pacote rbc/ narram o proprio raciocinio via print(). Em vez
    de simplesmente descartar isso, capturamos o texto e exibimos na pagina
    como "trace do ciclo" - assim o passo a passo do RBC continua visivel, que
    e o objetivo didatico do projeto.
    """
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        resultado = funcao(*args, **kwargs)
    return resultado, buffer.getvalue()


# ==============================================================================
# PASSO 0 - PREPARACAO (uma unica vez, na subida do servidor)
# ------------------------------------------------------------------------------
# Mesma logica do preparar() do main.py: a base nao muda entre consultas, entao
# recarregar 17 mil jogadores e reajustar o MinMaxScaler a cada requisicao HTTP
# seria desperdicio puro.
# ==============================================================================

print("Carregando a base de casos...")
BASE = BaseDeCasos.carregar(localizar_dataset())
ESPACO = EspacoDeSimilaridade(BASE)
MEMORIA = MemoriaDeCasos().carregar()
print("Base pronta: {} casos validos.".format(len(BASE)))

# Guarda a consulta em andamento entre o 2o R (exibicao) e o 4o R (retencao).
# E o equivalente web da variavel local que o main.py mantinha na pilha.
CONSULTAS = {}


# ==============================================================================
# ROTA 1 - DESCRICAO DO PROBLEMA NOVO
# ==============================================================================

@app.route("/")
def index():
    return render_template(
        "index.html",
        atributos=BASE.nomes_atributos,
        perfil_padrao=config.PERFIL_PADRAO,
        orcamento_padrao=config.ORCAMENTO_PADRAO,
        base=BASE,
        memoria=MEMORIA,
    )


# ==============================================================================
# ROTA 2 - 1o R (RECUPERACAO) + 2o R (REUTILIZACAO) + formulario do 3o R
# ==============================================================================

@app.route("/buscar", methods=["POST"])
def buscar():
    perfil = {a: int(request.form.get(a, 70)) for a in BASE.nomes_atributos}
    orcamento = float(request.form.get("orcamento", config.ORCAMENTO_PADRAO))
    problema = Problema(perfil_desejado=perfil, orcamento=orcamento)

    # ---- 1o R: RECUPERACAO -------------------------------------------------
    # Funcao importada de rbc/ciclo/r1_recuperacao.py, sem nenhuma adaptacao.
    recuperados, trace = _silencioso(
        recuperar, BASE, ESPACO, problema, k=config.K_VIZINHOS, memoria=MEMORIA
    )

    viaveis = int(BASE.mascara_orcamento(orcamento).sum())

    # Nenhum jogador cabe no orcamento: a volta termina aqui, igual ao main.py.
    if not recuperados:
        return render_template(
            "resultado.html",
            problema=problema, recuperados=None, viaveis=0,
            base=BASE, memoria=MEMORIA, trace=trace,
        )

    token = uuid.uuid4().hex
    CONSULTAS[token] = (problema, recuperados)

    return render_template(
        "resultado.html",
        problema=problema,
        recuperados=recuperados,
        viaveis=viaveis,
        token=token,
        base=BASE,
        memoria=MEMORIA,
        trace=trace,
    )


# ==============================================================================
# ROTA 3 - 3o R (REVISAO) + 4o R (RETENCAO)
# ==============================================================================

@app.route("/avaliar", methods=["POST"])
def avaliar():
    token = request.form.get("token", "")
    if token not in CONSULTAS:
        # Recarregou a pagina ou reiniciou o servidor: recomeca o ciclo.
        return redirect(url_for("index"))

    problema, recuperados = CONSULTAS.pop(token)
    escolha = int(request.form.get("escolha", 0))

    # ---- 3o R: REVISAO -----------------------------------------------------
    # Mesma decisao do r3_revisao.py, so que vinda de um <form> em vez de input()
    if escolha == 0:
        avaliacao = Avaliacao(
            aprovado=False, obs=request.form.get("motivo", "").strip()
        )
    else:
        escolhido = recuperados[escolha - 1]
        avaliacao = Avaliacao(
            aprovado=True,
            escolhido=escolhido.nome,
            indice=escolha - 1,
            nota=int(request.form.get("nota", 8)),
            obs=request.form.get("obs", "").strip(),
        )

    # ---- 4o R: RETENCAO ----------------------------------------------------
    # Funcao importada de rbc/ciclo/r4_retencao.py, sem nenhuma adaptacao.
    novo_caso, trace = _silencioso(reter, MEMORIA, problema, recuperados, avaliacao)

    sucessos, falhas = MEMORIA.resumo()
    return render_template(
        "retido.html",
        caso=novo_caso, avaliacao=avaliacao, problema=problema,
        sucessos=sucessos, falhas=falhas,
        base=BASE, memoria=MEMORIA, trace=trace,
    )


# ==============================================================================
# ROTA 4 - A BASE DE CASOS APRENDIDOS (o que torna o RBC auditavel)
# ==============================================================================

@app.route("/memoria")
def ver_memoria():
    sucessos, falhas = MEMORIA.resumo()
    return render_template(
        "memoria.html",
        casos=list(reversed(MEMORIA.casos)),
        sucessos=sucessos, falhas=falhas,
        arquivo=config.ARQUIVO_MEMORIA,
        base=BASE, memoria=MEMORIA,
    )


@app.route("/memoria/limpar", methods=["POST"])
def limpar_memoria():
    """Zera a base de casos aprendidos - util para demonstrar o ciclo do zero."""
    MEMORIA.casos = []
    MEMORIA.salvar()
    return redirect(url_for("ver_memoria"))


# ==============================================================================
# FILTROS DE FORMATACAO (equivalentes aos de rbc/interface/saida.py)
# ==============================================================================

@app.template_filter("eur")
def _fmt_eur(valor):
    return "€ " + "{:,}".format(int(round(valor))).replace(",", ".")


@app.template_filter("num")
def _fmt_num(valor):
    return "{:,}".format(int(valor)).replace(",", ".")


if __name__ == "__main__":
    # use_reloader=False: sem isso o Flask reinicia o processo e recarrega os
    # 17 mil jogadores duas vezes a cada alteracao de arquivo.
    app.run(debug=True, use_reloader=False, port=5000)
