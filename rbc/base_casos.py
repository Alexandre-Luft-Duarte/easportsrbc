# -*- coding: utf-8 -*-
"""
BASE DE CASOS (Case Base) - o "coracao" do sistema RBC.

Diferente de um modelo de Machine Learning, que comprime o conhecimento em
pesos, o RBC mantem o conhecimento explicito: cada linha do CSV e um caso ja
resolvido pelo mundo real (um jogador que existe, com atributos tecnicos
conhecidos e um preco de mercado conhecido).

Este modulo cuida de: localizar o CSV, mapear as colunas, limpar os dados e
expor a base pronta para as etapas do ciclo.
"""

import numpy as np
import pandas as pd

from . import config


# ==============================================================================
# LOCALIZACAO DOS ARQUIVOS
# ==============================================================================

def listar_datasets():
    """
    Lista os CSVs disponiveis em data/.

    O dataset vem separado por temporada (players_15.csv ... players_22.csv).
    Cada arquivo e uma BASE DE CASOS diferente: os mesmos jogadores, mas com
    atributos e precos daquele ano - o que muda completamente o resultado da
    recuperacao.
    """
    if not config.PASTA_DADOS.exists():
        raise FileNotFoundError(
            "\n\n>>> A pasta de dados nao existe:\n    {}\n"
            ">>> Crie-a e coloque os CSVs do FIFA dentro.\n".format(config.PASTA_DADOS)
        )

    csvs = sorted(config.PASTA_DADOS.glob("*.csv"))
    if not csvs:
        raise FileNotFoundError(
            "\n\n>>> Nenhum arquivo .csv encontrado em:\n    {}\n"
            ">>> Coloque o CSV do FIFA nesta pasta e rode de novo.\n".format(config.PASTA_DADOS)
        )
    return csvs


# ==============================================================================
# MAPEAMENTO DE COLUNAS
# ==============================================================================

def _achar_coluna(df, candidatos):
    """Retorna o primeiro nome de coluna que existir no DataFrame, ou None."""
    for c in candidatos:
        if c in df.columns:
            return c
    return None


def _mapear_colunas(df):
    """
    Descobre quais colunas do CSV correspondem a cada papel semantico.

    Devolve (mapa_descritivo, mapa_atributos), ambos no formato
    {papel_semantico: nome_real_da_coluna}.
    """
    mapa = {}
    for papel, candidatos in config.COLUNAS_DESCRITIVAS.items():
        col = _achar_coluna(df, candidatos)
        if col is not None:
            mapa[papel] = col

    if "valor" not in mapa:
        raise KeyError(
            "Nao encontrei a coluna de VALOR DE MERCADO no CSV.\n"
            "Sem ela nao ha como aplicar o filtro de orcamento.\n"
            "Colunas disponiveis: {}".format(list(df.columns)[:40])
        )

    atributos = {}
    for papel, candidatos in config.ATRIBUTOS_SIMILARIDADE.items():
        col = _achar_coluna(df, candidatos)
        if col is not None and pd.api.types.is_numeric_dtype(df[col]):
            atributos[papel] = col

    if len(atributos) < 3:
        raise KeyError(
            "Nao encontrei atributos tecnicos numericos suficientes no CSV.\n"
            "Colunas disponiveis: {}".format(list(df.columns)[:40])
        )

    return mapa, atributos


# ==============================================================================
# LIMPEZA
# ==============================================================================

def _limpar_valor_monetario(serie):
    """
    Converte a coluna de preco para float.

    Alguns datasets trazem numero puro (110500000.0), outros trazem texto
    formatado (ex.: "110.5M", "77K", com simbolo de moeda). Tratamos os dois.
    """
    if pd.api.types.is_numeric_dtype(serie):
        return serie.astype(float)

    def converte(v):
        if pd.isna(v):
            return np.nan
        texto = str(v).strip()
        for simbolo in ("€", "£", "$", ","):
            texto = texto.replace(simbolo, "")
        multiplicador = 1.0
        if texto.upper().endswith("M"):
            multiplicador, texto = 1_000_000.0, texto[:-1]
        elif texto.upper().endswith("K"):
            multiplicador, texto = 1_000.0, texto[:-1]
        try:
            return float(texto) * multiplicador
        except ValueError:
            return np.nan

    return serie.map(converte)


# ==============================================================================
# A CLASSE QUE REPRESENTA A BASE DE CASOS
# ==============================================================================

class BaseDeCasos:
    """
    Encapsula o DataFrame limpo + o mapeamento de colunas.

    Agrupar isso numa classe evita ter que passar (df, mapa, atributos) como
    tres parametros soltos por todo o codigo, e da um lugar natural para as
    operacoes sobre a base (filtrar por orcamento, ler a ficha de um jogador).
    """

    COL_VALOR = "_valor"   # coluna interna, normalizada, com o preco em EUR

    def __init__(self, df, mapa, atributos, origem):
        self.df = df
        self.mapa = mapa                    # {papel: coluna} descritivo
        self.atributos = atributos          # {papel: coluna} de similaridade
        self.origem = origem                # Path do CSV carregado
        self.removidos = 0

    # -------------------------------------------------------------- carga ---
    @classmethod
    def carregar(cls, caminho_csv):
        """Le o CSV, mapeia as colunas e devolve a base ja limpa."""
        df = pd.read_csv(caminho_csv, low_memory=False, encoding="utf-8")
        brutos = len(df)

        mapa, atributos = _mapear_colunas(df)

        # 1) preco numerico numa coluna interna de nome estavel
        df[cls.COL_VALOR] = _limpar_valor_monetario(df[mapa["valor"]])

        # 2) descarta casos incompletos ou sem preco.
        #    OBS IMPORTANTE: goleiros tem pace/shooting/etc. nulos nesses
        #    datasets, entao saem naturalmente da base. Isso e uma DECISAO DE
        #    MODELAGEM correta, nao um bug: comparar goleiro com atacante
        #    usando estes 6 atributos nao produziria similaridade util.
        colunas_obrigatorias = list(atributos.values()) + [cls.COL_VALOR]
        df = df.dropna(subset=colunas_obrigatorias)
        df = df[df[cls.COL_VALOR] > 0].reset_index(drop=True)

        base = cls(df, mapa, atributos, caminho_csv)
        base.brutos = brutos
        base.removidos = brutos - len(df)
        return base

    # ------------------------------------------------------------ consulta ---
    def __len__(self):
        return len(self.df)

    @property
    def nomes_atributos(self):
        """Papeis semanticos dos atributos, na ordem usada nos vetores."""
        return list(self.atributos.keys())

    @property
    def colunas_atributos(self):
        """Nomes reais das colunas de atributos, na mesma ordem."""
        return list(self.atributos.values())

    def matriz_atributos(self):
        """Matriz (n_casos x n_atributos) com os valores brutos."""
        return self.df[self.colunas_atributos].to_numpy(dtype=float)

    def precos(self):
        """Vetor com o preco de cada caso, em EUR."""
        return self.df[self.COL_VALOR].to_numpy()

    def mascara_orcamento(self, orcamento):
        """Vetor booleano: True para os casos que cabem no orcamento."""
        return self.precos() <= orcamento

    def ficha(self, linha):
        """Extrai os dados descritivos de um jogador para exibicao."""
        dados = {}
        for papel in ("idade", "clube", "posicao", "overall", "potencial"):
            col = self.mapa.get(papel)
            if col is not None and pd.notna(linha[col]):
                valor = linha[col]
                if papel in ("idade", "overall", "potencial"):
                    valor = int(valor)
                dados[papel] = valor
        return dados

    def nome_de(self, linha):
        """Nome do jogador, com fallback caso a coluna nao exista."""
        col = self.mapa.get("nome")
        return str(linha[col]) if col is not None else "Jogador sem nome"
