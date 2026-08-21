# -*- coding: utf-8 -*-
"""
Configuracoes centrais do sistema.

Manter constantes e mapeamentos aqui (em vez de espalhados pelo codigo) e o que
permite trocar o dataset, o numero de vizinhos ou os atributos de similaridade
sem precisar mexer na logica do ciclo RBC.
"""

from pathlib import Path

# ==============================================================================
# CAMINHOS DO PROJETO
# ==============================================================================
# RAIZ = a pasta trab_rbc/ (dois niveis acima deste arquivo: rbc/config.py)
RAIZ = Path(__file__).resolve().parent.parent

PASTA_DADOS = RAIZ / "data"       # onde fica o CSV do FIFA (base de casos)
PASTA_MEMORIA = RAIZ / "memoria"  # onde a RETENCAO grava os casos aprendidos

# A BASE DE CASOS e a temporada 2022 do FIFA - a mais recente do dataset e a
# unica usada pelo sistema. Fixar o arquivo aqui mantem a execucao direta: o
# usuario descreve o problema e o ciclo roda, sem escolher temporada antes.
ARQUIVO_DADOS = PASTA_DADOS / "players_22.csv"

ARQUIVO_MEMORIA = PASTA_MEMORIA / "base_casos_aprendidos.json"


# ==============================================================================
# PARAMETROS DO RACIOCINIO
# ==============================================================================

K_VIZINHOS = 5          # quantos casos similares a RECUPERACAO deve trazer
METRICA = "euclidean"   # metrica de distancia usada pelo KNN
ORCAMENTO_PADRAO = 15_000_000.0

# A recuperacao consulta mais candidatos antes de aplicar o aprendizado da
# memoria. Assim, uma recomendacao aprovada pode subir no ranking e uma
# recomendacao rejeitada pode dar lugar a uma alternativa.
FATOR_POOL_MEMORIA = 5
LIMIAR_EXPERIENCIA_SEMELHANTE = 0.80
PESO_SUCESSO_MEMORIA = 0.15
PESO_FALHA_MEMORIA = 0.15


# ==============================================================================
# MAPEAMENTO DE COLUNAS (portabilidade entre versoes do dataset)
# ------------------------------------------------------------------------------
# Cada versao do dataset do FIFA nomeia as colunas de um jeito ligeiramente
# diferente (ex.: "value_eur" vs "Value", "short_name" vs "Name"). Em vez de
# fixar um nome unico, listamos candidatos e procuramos o primeiro que existir.
# Mesmo usando apenas players_22.csv, isso mantem o projeto portavel: trocar o
# CSV por outra versao publicada no Kaggle nao exige mexer na logica.
# ==============================================================================

COLUNAS_DESCRITIVAS = {
    "nome":      ["short_name", "long_name", "Name", "name", "player_name", "Player"],
    "idade":     ["age", "Age"],
    "clube":     ["club_name", "Club", "club", "team"],
    "posicao":   ["player_positions", "Position", "positions", "club_position", "BP"],
    "overall":   ["overall", "Overall", "OVA", "rating"],
    "potencial": ["potential", "Potential", "POT"],
    "valor":     ["value_eur", "Value", "value", "market_value"],
}

# ------------------------------------------------------------------------------
# ATRIBUTOS DE SIMILARIDADE
# Sao os 6 "macro-atributos" do FIFA. Foram escolhidos porque:
#   1. sao numericos e ja vivem na mesma escala (0-100);
#   2. descrevem o ESTILO de jogo, que e exatamente o que queremos clonar;
#   3. resumem bem as ~40 sub-habilidades do dataset sem redundancia.
# ------------------------------------------------------------------------------
ATRIBUTOS_SIMILARIDADE = {
    "velocidade": ["pace", "Pace", "PAC", "movement_sprint_speed"],
    "chute":      ["shooting", "Shooting", "SHO", "attacking_finishing"],
    "passe":      ["passing", "Passing", "PAS", "attacking_short_passing"],
    "drible":     ["dribbling", "Dribbling", "DRI", "skill_dribbling"],
    "defesa":     ["defending", "Defending", "DEF", "defending_marking"],
    "fisico":     ["physic", "Physicality", "PHY", "power_strength"],
}

# Perfil sugerido quando o usuario aperta Enter: um ponta veloz e habilidoso
# (estilo Mbappe / Vinicius Jr) - tipicamente caro demais, que e a premissa
# do problema que o sistema resolve.
PERFIL_PADRAO = {
    "velocidade": 95,
    "chute": 88,
    "passe": 80,
    "drible": 92,
    "defesa": 36,
    "fisico": 78,
}
