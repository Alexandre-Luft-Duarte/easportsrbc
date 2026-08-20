# -*- coding: utf-8 -*-
"""
================================================================================
 OLHEIRO VIRTUAL - Sistema de Recomendacao de Contratacoes
 Raciocinio Baseado em Casos (RBC) aplicado ao dataset do FIFA
================================================================================

 O QUE E RACIOCINIO BASEADO EM CASOS?
 ------------------------------------
 O RBC (Case-Based Reasoning) e um paradigma da IA Classica que resolve um
 problema NOVO recuperando problemas ANTIGOS parecidos e adaptando as solucoes
 que ja funcionaram. Nao existe "treinamento" de um modelo estatistico: o
 conhecimento fica armazenado na propria BASE DE CASOS.

 A analogia deste trabalho:
   * CASO          -> um jogador do dataset (atributos + preco)
   * PROBLEMA NOVO -> o perfil tecnico do jogador ideal (caro demais)
   * RESTRICAO     -> o orcamento maximo do clube
   * SOLUCAO       -> os jogadores similares e acessiveis encontrados

 O CICLO DOS 4 Rs (Aamodt & Plaza, 1994):
   1. RECUPERACAO  (Retrieve) -> achar os casos mais parecidos     [ETAPA 1]
   2. REUTILIZACAO (Reuse)    -> propor a solucao encontrada       [ETAPA 2]
   3. REVISAO      (Revise)   -> especialista humano valida        [ETAPA 3]
   4. RETENCAO     (Retain)   -> aprender: guardar o caso resolvido[ETAPA 4]

 Execucao:  python olheiro_virtual.py
 Requisitos: pandas, numpy, scikit-learn
================================================================================
"""

import os
import sys
import glob
import json
from datetime import datetime

# O dataset do FIFA e UTF-8 e tem muitos nomes acentuados (Suarez, Balde,
# Mbappe...). O console do Windows costuma usar cp1252 e quebraria esses
# caracteres na hora de imprimir, entao forcamos a saida para UTF-8.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors   # algoritmo KNN (vizinhos mais proximos)
from sklearn.preprocessing import MinMaxScaler   # normalizacao das features


# ==============================================================================
# CONFIGURACOES GERAIS
# ==============================================================================

K_VIZINHOS      = 5                              # quantos casos similares recuperar
ARQUIVO_MEMORIA = "base_casos_aprendidos.json"   # onde a RETENCAO persiste


def cabecalho(titulo, simbolo="="):
    """Imprime um cabecalho de secao para deixar o fluxo do RBC visivel."""
    print("\n" + simbolo * 78)
    print(" " + titulo)
    print(simbolo * 78)


# ==============================================================================
# PASSO 0 - PREPARACAO DA BASE DE CASOS
# ------------------------------------------------------------------------------
# No RBC, a "Case Base" e o coracao do sistema. Aqui ela e o CSV do FIFA:
# cada linha e um caso ja resolvido pelo mundo real (um jogador que existe,
# com atributos tecnicos conhecidos e um valor de mercado conhecido).
# ==============================================================================

# --- Dicionario de sinonimos --------------------------------------------------
# Cada versao do dataset do FIFA nomeia as colunas de um jeito ligeiramente
# diferente (ex.: "value_eur" vs "Value", "short_name" vs "Name"). Em vez de
# fixar um nome unico, procuramos por candidatos. Isso torna o script portavel
# entre players_15.csv ... players_22.csv, FIFA23, versoes do Kaggle etc.
CANDIDATOS = {
    "nome":      ["short_name", "long_name", "Name", "name", "player_name", "Player"],
    "idade":     ["age", "Age"],
    "clube":     ["club_name", "Club", "club", "team"],
    "posicao":   ["player_positions", "Position", "positions", "club_position", "BP"],
    "overall":   ["overall", "Overall", "OVA", "rating"],
    "potencial": ["potential", "Potential", "POT"],
    "valor":     ["value_eur", "Value", "value", "market_value"],
}

# Atributos tecnicos usados no calculo de similaridade.
# Sao os 6 "macro-atributos" do FIFA - cobrem velocidade, chute, passe,
# drible, defesa e fisico. Sao numericos, estao na mesma escala (0-100) e
# descrevem o ESTILO do jogador, que e exatamente o que queremos clonar.
CANDIDATOS_FEATURES = {
    "velocidade": ["pace", "Pace", "PAC", "movement_sprint_speed"],
    "chute":      ["shooting", "Shooting", "SHO", "attacking_finishing"],
    "passe":      ["passing", "Passing", "PAS", "attacking_short_passing"],
    "drible":     ["dribbling", "Dribbling", "DRI", "skill_dribbling"],
    "defesa":     ["defending", "Defending", "DEF", "defending_marking"],
    "fisico":     ["physic", "Physicality", "PHY", "power_strength"],
}


def achar_coluna(df, candidatos):
    """Retorna o primeiro nome de coluna que existir no DataFrame, ou None."""
    for c in candidatos:
        if c in df.columns:
            return c
    return None


def localizar_csv():
    """
    Encontra o CSV do FIFA na pasta do script.

    O dataset vem separado por temporada (players_15.csv ... players_22.csv).
    Cada arquivo e uma BASE DE CASOS diferente: os mesmos jogadores, mas com
    atributos e precos daquele ano. Como isso muda completamente o resultado
    da recuperacao, deixamos o usuario escolher qual temporada usar.
    """
    pasta = os.path.dirname(os.path.abspath(__file__))
    csvs = sorted(glob.glob(os.path.join(pasta, "*.csv")))

    if not csvs:
        raise FileNotFoundError(
            "\n\n>>> Nenhum arquivo .csv encontrado em:\n    " + pasta +
            "\n>>> Coloque o CSV do FIFA nesta pasta e rode de novo.\n"
        )

    if len(csvs) == 1:
        return csvs[0]

    # Varias temporadas disponiveis -> menu de selecao (padrao: a mais recente)
    print("\nBases de casos disponiveis (uma por temporada do FIFA):")
    for i, c in enumerate(csvs, start=1):
        print("   {}) {}".format(i, os.path.basename(c)))

    padrao = len(csvs)   # a ultima em ordem alfabetica = temporada mais recente
    while True:
        txt = input("\nEscolha a temporada [1-{}] (Enter = {}): "
                    .format(len(csvs), os.path.basename(csvs[padrao - 1]))).strip()
        if txt == "":
            return csvs[padrao - 1]
        if txt.isdigit() and 1 <= int(txt) <= len(csvs):
            return csvs[int(txt) - 1]
        print("   ! Opcao invalida.")


def limpar_valor_monetario(serie):
    """
    Converte a coluna de preco para float.
    Alguns datasets trazem numero puro (110500000.0), outros trazem texto
    formatado (ex.: 110.5M, 77K, com simbolo de moeda). Tratamos os dois casos.
    """
    if pd.api.types.is_numeric_dtype(serie):
        return serie.astype(float)

    def converte(v):
        if pd.isna(v):
            return np.nan
        t = str(v).strip()
        for simbolo in ("€", "£", "$", ","):
            t = t.replace(simbolo, "")
        mult = 1.0
        if t.upper().endswith("M"):
            mult, t = 1_000_000.0, t[:-1]
        elif t.upper().endswith("K"):
            mult, t = 1_000.0, t[:-1]
        try:
            return float(t) * mult
        except ValueError:
            return np.nan

    return serie.map(converte)


def fmt_eur(v):
    """Formata um valor em euros com ponto como separador de milhar."""
    return "EUR " + ("{:,.0f}".format(v)).replace(",", ".")


def carregar_base_de_casos():
    """Le o CSV, mapeia as colunas e devolve a base de casos limpa."""
    caminho = localizar_csv()
    cabecalho("PASSO 0 - CARREGANDO A BASE DE CASOS")
    print("Arquivo: " + os.path.basename(caminho))

    df = pd.read_csv(caminho, low_memory=False)
    print("Registros brutos: {:,}".format(len(df)).replace(",", "."))

    # ---- mapeia colunas descritivas -----------------------------------------
    mapa = {}
    for papel, cands in CANDIDATOS.items():
        col = achar_coluna(df, cands)
        if col:
            mapa[papel] = col

    if "valor" not in mapa:
        raise KeyError(
            "Nao encontrei a coluna de VALOR DE MERCADO no CSV.\n"
            "Colunas disponiveis: " + str(list(df.columns)[:40])
        )

    # ---- mapeia as features tecnicas (as que entram no KNN) ------------------
    features = {}
    for papel, cands in CANDIDATOS_FEATURES.items():
        col = achar_coluna(df, cands)
        if col is not None and pd.api.types.is_numeric_dtype(df[col]):
            features[papel] = col

    if len(features) < 3:
        raise KeyError(
            "Nao encontrei atributos tecnicos numericos suficientes no CSV.\n"
            "Colunas disponiveis: " + str(list(df.columns)[:40])
        )

    print("\nFeatures escolhidas para o calculo de SIMILARIDADE:")
    for papel, col in features.items():
        print("   - {:<12} -> coluna '{}'".format(papel, col))
    print("\nColuna de orcamento (preco) -> '{}'".format(mapa["valor"]))

    # ---- limpeza -------------------------------------------------------------
    # 1) preco numerico
    df["_valor"] = limpar_valor_monetario(df[mapa["valor"]])

    # 2) descarta jogadores sem preco, sem atributos ou de graca.
    #    OBS: goleiros costumam ter pace/shooting nulos nesses datasets, entao
    #    eles saem naturalmente da base - o que faz sentido, porque comparar
    #    goleiro com atacante usando esses 6 atributos nao teria valor algum.
    cols_feat = list(features.values())
    antes = len(df)
    df = df.dropna(subset=cols_feat + ["_valor"])
    df = df[df["_valor"] > 0].reset_index(drop=True)
    print("\nCasos validos apos limpeza: {:,}".format(len(df)).replace(",", ".")
          + "  (removidos {:,})".format(antes - len(df)).replace(",", "."))

    return df, mapa, features


# ==============================================================================
# PASSO 0.1 - REPRESENTACAO E NORMALIZACAO DOS CASOS
# ------------------------------------------------------------------------------
# A Distancia Euclidiana soma diferencas ao quadrado em cada eixo. Se um
# atributo variasse de 0 a 100 e outro de 0 a 5, o primeiro dominaria a conta.
# Por isso normalizamos TUDO para o intervalo [0, 1] com o MinMaxScaler.
# Como todos os 6 atributos do FIFA ja vao de 0 a 100, isso tambem garante que
# cada um pese exatamente o mesmo na nocao de "parecido".
# ==============================================================================

def vetorizar_casos(df, features):
    """Transforma cada caso num vetor numerico normalizado (o 'DNA' do jogador)."""
    X = df[list(features.values())].to_numpy(dtype=float)
    scaler = MinMaxScaler()
    X_norm = scaler.fit_transform(X)
    return X_norm, scaler


# ==============================================================================
# PASSO 0.2 - DESCRICAO DO PROBLEMA NOVO (a "consulta")
# ------------------------------------------------------------------------------
# O usuario descreve o jogador dos sonhos - aquele que o clube nao pode pagar -
# e informa quanto dinheiro tem em caixa.
# ==============================================================================

def ler_int(msg, minimo, maximo, padrao):
    """Le um inteiro do terminal com validacao e valor padrao."""
    while True:
        txt = input("{} [{}-{}] (Enter = {}): ".format(msg, minimo, maximo, padrao)).strip()
        if txt == "":
            return padrao
        try:
            v = int(float(txt.replace(",", ".")))
            if minimo <= v <= maximo:
                return v
            print("   ! Valor fora da faixa {}-{}.".format(minimo, maximo))
        except ValueError:
            print("   ! Digite um numero.")


def ler_float(msg, padrao):
    """Le um valor monetario do terminal."""
    while True:
        txt = input("{} (Enter = {:,.0f}): ".format(msg, padrao).replace(",", ".")).strip()
        if txt == "":
            return padrao
        try:
            return float(txt.replace(".", "").replace(",", "."))
        except ValueError:
            print("   ! Digite um numero.")


def montar_problema(features):
    """Coleta do usuario o perfil-alvo + a restricao de orcamento."""
    cabecalho("NOVO PROBLEMA - PERFIL DO JOGADOR IDEAL")
    print("Informe os atributos do jogador que voce QUERIA contratar (0 a 100).")
    print("Pressione Enter para aceitar o valor sugerido.\n")

    # Perfil padrao: um ponta veloz e habilidoso (estilo Mbappe / Vinicius Jr).
    padroes = {"velocidade": 95, "chute": 88, "passe": 80,
               "drible": 92, "defesa": 36, "fisico": 78}

    alvo = {}
    for papel in features:                      # so pergunta o que existe no CSV
        alvo[papel] = ler_int("  {:<12}".format(papel.capitalize()),
                              0, 100, padroes.get(papel, 70))

    print()
    orcamento = ler_float("  Orcamento MAXIMO (EUR)", 15_000_000.0)

    return alvo, orcamento


# ==============================================================================
#                        >>> ETAPA 1 - RECUPERACAO <<<
# ------------------------------------------------------------------------------
# Esta e a etapa mais importante do RBC. Ela tem duas partes:
#
#  (A) FILTRAGEM POR RESTRICAO
#      Antes de medir similaridade, eliminamos da base todos os casos que
#      violam a restricao dura do problema: o orcamento. Isso e o que a
#      literatura chama de "filtro" ou "pre-selecao". Fazemos ANTES do KNN
#      porque, se filtrassemos depois, o KNN gastaria os K vizinhos com
#      craques impagaveis e sobrariam poucos (ou nenhum) candidatos viaveis.
#
#  (B) CALCULO DE SIMILARIDADE (DISTANCIA EUCLIDIANA)
#      Cada jogador e um ponto num espaco de N dimensoes (N = nro de atributos).
#      A distancia entre o jogador ideal (q) e um candidato (c) e:
#
#            d(q, c) = raiz( (q1-c1)^2 + (q2-c2)^2 + ... + (qN-cN)^2 )
#
#      Quanto MENOR a distancia, MAIOR a similaridade. Convertemos uma na
#      outra com:   similaridade = 1 / (1 + d)     -> resultado entre 0 e 1.
#
#      Usamos o NearestNeighbors do scikit-learn (algoritmo KNN) com
#      metric='euclidean' para achar os K pontos mais proximos de forma
#      eficiente, atraves de estruturas de indexacao (kd_tree / ball_tree).
# ==============================================================================

def recuperacao(df, X_norm, scaler, features, alvo, orcamento, k=K_VIZINHOS):
    cabecalho(">>> ETAPA 1 - RECUPERACAO (Retrieve)")

    # ---------- (A) FILTRO DE RESTRICAO: o orcamento --------------------------
    mascara = df["_valor"].to_numpy() <= orcamento
    n_viaveis = int(mascara.sum())

    print("[A] Filtro de orcamento: ate " + fmt_eur(orcamento))
    print("    Base completa .............. {:,} casos".format(len(df)).replace(",", "."))
    print("    Casos dentro do orcamento .. {:,} casos".format(n_viaveis).replace(",", "."))

    if n_viaveis == 0:
        print("\n    ! Nenhum jogador cabe nesse orcamento. Aumente o valor.")
        return None

    # Sub-base contendo apenas os casos viaveis
    X_viavel = X_norm[mascara]
    df_viavel = df[mascara].reset_index(drop=True)

    # ---------- (B) SIMILARIDADE VIA KNN -------------------------------------
    # O vetor-problema precisa passar pela MESMA normalizacao da base,
    # senao estariamos comparando escalas diferentes.
    q = np.array([[alvo[p] for p in features]], dtype=float)
    q_norm = scaler.transform(q)

    k_efetivo = min(k, n_viaveis)

    modelo_knn = NearestNeighbors(
        n_neighbors=k_efetivo,
        metric="euclidean",   # <<< Distancia Euclidiana: o coracao da similaridade
        algorithm="auto",
    )
    modelo_knn.fit(X_viavel)                       # indexa a base de casos viaveis
    distancias, indices = modelo_knn.kneighbors(q_norm)

    distancias = distancias[0]
    indices = indices[0]

    print("\n[B] KNN (metric='euclidean') buscando os {} vizinhos mais proximos...".format(k_efetivo))
    print("    Espaco de similaridade: {} dimensoes {}".format(len(features), list(features.keys())))

    # Converte distancia -> similaridade (0 a 1)
    similaridades = 1.0 / (1.0 + distancias)

    # Monta o resultado da recuperacao
    recuperados = df_viavel.iloc[indices].copy()
    recuperados["_distancia"] = distancias
    recuperados["_similaridade"] = similaridades

    print("\n    Distancias euclidianas encontradas:")
    for pos, (d, s) in enumerate(zip(distancias, similaridades), start=1):
        print("      {}o vizinho -> d = {:.4f}  |  similaridade = {:5.2f}%".format(pos, d, s * 100))

    return recuperados


# ==============================================================================
#                       >>> ETAPA 2 - REUTILIZACAO <<<
# ------------------------------------------------------------------------------
# Reutilizar = pegar a solucao dos casos recuperados e propo-la como solucao do
# problema novo. Aqui a "solucao" e a lista de jogadores substitutos.
# Tambem fazemos uma pequena ADAPTACAO (adaptation), tipica do RBC: mostramos
# o delta de cada atributo em relacao ao ideal e a economia gerada, para o
# especialista entender o que ele ganha e o que ele perde em cada opcao.
# ==============================================================================

def reutilizacao(recuperados, mapa, features, alvo, orcamento):
    cabecalho(">>> ETAPA 2 - REUTILIZACAO (Reuse)")
    print("Solucao sugerida: jogadores similares ao ideal e dentro do orcamento.\n")

    col_nome = mapa.get("nome")

    for pos, (idx, jog) in enumerate(recuperados.iterrows(), start=1):
        nome = jog[col_nome] if col_nome else "Jogador #{}".format(idx)
        print("-" * 78)
        print("  #{}  {}   |   SIMILARIDADE: {:.2f}%".format(pos, nome, jog["_similaridade"] * 100))

        # ficha descritiva
        linha = []
        if "idade" in mapa:
            linha.append("Idade: {}".format(int(jog[mapa["idade"]])))
        if "clube" in mapa and pd.notna(jog[mapa["clube"]]):
            linha.append("Clube: {}".format(jog[mapa["clube"]]))
        if "posicao" in mapa:
            linha.append("Posicao: {}".format(jog[mapa["posicao"]]))
        if "overall" in mapa:
            linha.append("Overall: {}".format(int(jog[mapa["overall"]])))
        if "potencial" in mapa:
            linha.append("Potencial: {}".format(int(jog[mapa["potencial"]])))
        if linha:
            print("      " + "  |  ".join(linha))

        # preco e folga no caixa
        preco = jog["_valor"]
        folga = orcamento - preco
        print("      Valor de mercado: " + fmt_eur(preco)
              + "   (sobra no caixa: " + fmt_eur(folga) + ")")

        # ADAPTACAO: comparacao atributo a atributo com o alvo
        print("      Atributos (alvo -> encontrado):")
        comp = []
        for papel, col in features.items():
            vi = alvo[papel]
            vr = int(jog[col])
            dif = vr - vi
            sinal = "+" if dif > 0 else ""
            comp.append("{}: {}->{} ({}{})".format(papel[:4], vi, vr, sinal, dif))
        print("        " + " | ".join(comp))

    print("-" * 78)
    return recuperados


# ==============================================================================
#                         >>> ETAPA 3 - REVISAO <<<
# ------------------------------------------------------------------------------
# O RBC NAO confia cegamente na solucao recuperada. A etapa de Revisao coloca
# o especialista humano (aqui, o diretor de futebol) no circuito para avaliar,
# corrigir ou rejeitar a sugestao. E o que caracteriza o RBC como um sistema
# de apoio a decisao, e nao uma caixa-preta.
# ==============================================================================

def revisao(recuperados, mapa):
    cabecalho(">>> ETAPA 3 - REVISAO (Revise)")
    print("Avaliacao do ESPECIALISTA HUMANO (voce, o olheiro do clube).\n")

    col_nome = mapa.get("nome")
    nomes = [str(recuperados.iloc[i][col_nome]) if col_nome else "#{}".format(i + 1)
             for i in range(len(recuperados))]

    for i, n in enumerate(nomes, start=1):
        print("   {}) {}".format(i, n))

    print("\n   0) Nenhum serve - rejeitar a sugestao")

    while True:
        esc = input("\n   A sugestao faz sentido? Escolha o jogador aprovado: ").strip()
        if esc.isdigit():
            e = int(esc)
            if e == 0:
                motivo = input("   Por que a sugestao falhou? ").strip()
                print("\n   >> Sugestao REJEITADA pelo especialista.")
                return {"aprovado": False, "escolhido": None, "nota": None, "obs": motivo}
            if 1 <= e <= len(nomes):
                nota = ler_int("   Nota para a recomendacao", 0, 10, 8)
                obs = input("   Observacoes do olheiro (opcional): ").strip()
                print("\n   >> Sugestao APROVADA: {} (nota {}/10)".format(nomes[e - 1], nota))
                return {
                    "aprovado": True,
                    "escolhido": nomes[e - 1],
                    "indice": e - 1,
                    "nota": nota,
                    "obs": obs,
                }
        print("   ! Opcao invalida.")


# ==============================================================================
#                        >>> ETAPA 4 - RETENCAO <<<
# ------------------------------------------------------------------------------
# Aqui acontece a APRENDIZAGEM INCREMENTAL do RBC: o par (problema, solucao
# validada) vira um NOVO CASO e entra na base de casos. Da proxima vez que um
# problema parecido aparecer, o sistema ja tera essa experiencia disponivel -
# sem precisar re-treinar nada, diferente de um modelo de ML tradicional.
#
# Guardamos em dois lugares:
#   * MEMORIA_CASOS               -> lista em memoria (viva durante a execucao)
#   * base_casos_aprendidos.json  -> persistencia entre execucoes
# ==============================================================================

MEMORIA_CASOS = []   # <<< a base de casos aprendidos, em memoria


def retencao(alvo, orcamento, recuperados, veredito, mapa, features):
    cabecalho(">>> ETAPA 4 - RETENCAO (Retain)")

    novo_caso = {
        "id": len(MEMORIA_CASOS) + 1,
        "data_hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        # --- descricao do problema ---
        "problema": {
            "perfil_desejado": alvo,
            "orcamento_eur": orcamento,
        },
        # --- solucao proposta pelo sistema ---
        "solucao_sugerida": [
            {
                "nome": str(r[mapa["nome"]]) if "nome" in mapa else "?",
                "valor_eur": float(r["_valor"]),
                "similaridade": round(float(r["_similaridade"]), 4),
                "distancia": round(float(r["_distancia"]), 4),
            }
            for _, r in recuperados.iterrows()
        ],
        # --- resultado da revisao humana ---
        "avaliacao_especialista": veredito,
    }

    if veredito["aprovado"]:
        # Caso de SUCESSO: reforca o conhecimento do sistema.
        novo_caso["tipo"] = "caso_de_sucesso"
        MEMORIA_CASOS.append(novo_caso)
        print("Caso APROVADO adicionado a base de casos.")
        print("   Problema : perfil {} com teto de {}".format(alvo, fmt_eur(orcamento)))
        print("   Solucao  : {}".format(veredito["escolhido"]))
        print("   Confianca: nota {}/10 do especialista".format(veredito["nota"]))
    else:
        # Caso de FALHA: no RBC, falhas tambem sao conhecimento util -
        # evitam que o sistema repita a mesma recomendacao ruim.
        novo_caso["tipo"] = "caso_de_falha"
        MEMORIA_CASOS.append(novo_caso)
        print("Caso de FALHA registrado (aprender com o erro tambem e RBC).")
        print("   Motivo: {}".format(veredito["obs"] or "(nao informado)"))

    # --- persistencia em disco ---
    try:
        with open(ARQUIVO_MEMORIA, "w", encoding="utf-8") as f:
            json.dump(MEMORIA_CASOS, f, ensure_ascii=False, indent=2)
        print("\nBase de casos gravada em '{}'.".format(ARQUIVO_MEMORIA))
    except OSError as e:
        print("\n(Nao foi possivel gravar o arquivo: {})".format(e))

    print("Total de casos na base de conhecimento: {}".format(len(MEMORIA_CASOS)))
    return novo_caso


def carregar_memoria():
    """Recarrega os casos aprendidos em execucoes anteriores."""
    global MEMORIA_CASOS
    if os.path.exists(ARQUIVO_MEMORIA):
        try:
            with open(ARQUIVO_MEMORIA, encoding="utf-8") as f:
                MEMORIA_CASOS = json.load(f)
            print("[Memoria] {} caso(s) aprendidos recuperados de execucoes anteriores."
                  .format(len(MEMORIA_CASOS)))
        except (OSError, json.JSONDecodeError):
            MEMORIA_CASOS = []


# ==============================================================================
# ORQUESTRADOR - roda o ciclo completo dos 4 Rs
# ==============================================================================

def main():
    print("\n" + "#" * 78)
    print("#" + " OLHEIRO VIRTUAL - RBC (Raciocinio Baseado em Casos) ".center(76) + "#")
    print("#" + " Ciclo dos 4 Rs: Recuperacao > Reutilizacao > Revisao > Retencao ".center(76) + "#")
    print("#" * 78)

    carregar_memoria()

    # PASSO 0 - base de casos
    df, mapa, features = carregar_base_de_casos()
    X_norm, scaler = vetorizar_casos(df, features)

    while True:
        # PASSO 0.2 - problema novo
        alvo, orcamento = montar_problema(features)

        # ETAPA 1 - RECUPERACAO
        recuperados = recuperacao(df, X_norm, scaler, features, alvo, orcamento)
        if recuperados is None:
            if input("\nTentar outro orcamento? (s/n): ").strip().lower().startswith("s"):
                continue
            break

        # ETAPA 2 - REUTILIZACAO
        reutilizacao(recuperados, mapa, features, alvo, orcamento)

        # ETAPA 3 - REVISAO
        veredito = revisao(recuperados, mapa)

        # ETAPA 4 - RETENCAO
        retencao(alvo, orcamento, recuperados, veredito, mapa, features)

        # O ciclo do RBC e continuo: cada consulta enriquece a base de casos.
        if not input("\nFazer nova busca? (s/n): ").strip().lower().startswith("s"):
            break

    cabecalho("FIM DO CICLO RBC", "#")
    print("Casos na base de conhecimento: {}".format(len(MEMORIA_CASOS)))
    print("Obrigado por usar o Olheiro Virtual.\n")


if __name__ == "__main__":
    main()
