# -*- coding: utf-8 -*-
"""
Modelos de dados do RBC.

No RBC, tudo gira em torno da nocao de CASO. Um caso e sempre um par:

        CASO = (descricao do PROBLEMA, descricao da SOLUCAO)

Modelar isso com dataclasses (em vez de dicionarios soltos) deixa o vocabulario
do dominio explicito no codigo e evita erros de digitacao em chaves.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


# ==============================================================================
# DESCRICAO DO PROBLEMA
# ==============================================================================

@dataclass
class Problema:
    """
    O problema novo que chega ao sistema.

    perfil_desejado : atributos tecnicos do jogador ideal, ex.:
                      {"velocidade": 95, "chute": 88, ...}
    orcamento       : restricao dura - o teto que o clube pode pagar (EUR).
    """
    perfil_desejado: dict
    orcamento: float

    def como_vetor(self, atributos):
        """Devolve os valores na MESMA ordem dos atributos da base de casos."""
        return [self.perfil_desejado[a] for a in atributos]


# ==============================================================================
# DESCRICAO DA SOLUCAO
# ==============================================================================

@dataclass
class CasoRecuperado:
    """
    Um jogador trazido pela etapa de RECUPERACAO.

    distancia    : distancia euclidiana ate o perfil desejado (menor = melhor)
    similaridade : 1 / (1 + distancia), normalizada entre 0 e 1
    atributos    : valores tecnicos do jogador encontrado
    ficha        : dados descritivos (idade, clube, posicao, overall...)
    """
    nome: str
    valor: float
    distancia: float
    similaridade: float
    atributos: dict
    ficha: dict = field(default_factory=dict)
    ajuste_memoria: float = 0.0

    @property
    def pontuacao_ranking(self) -> float:
        """Similaridade tecnica ajustada pelo aprendizado acumulado."""
        return max(0.0, min(1.0, self.similaridade + self.ajuste_memoria))

    def economia(self, orcamento: float) -> float:
        """Quanto sobra no caixa se o clube contratar este jogador."""
        return orcamento - self.valor


@dataclass
class Avaliacao:
    """
    O veredito do especialista humano, produzido na etapa de REVISAO.

    aprovado  : a sugestao do sistema faz sentido?
    escolhido : nome do jogador aprovado (None se rejeitada)
    nota      : confianca do especialista, de 0 a 10
    obs       : justificativa livre - vira conhecimento na base
    """
    aprovado: bool
    escolhido: Optional[str] = None
    indice: Optional[int] = None
    nota: Optional[int] = None
    obs: str = ""


# ==============================================================================
# O CASO COMPLETO (o que a RETENCAO guarda)
# ==============================================================================

@dataclass
class CasoAprendido:
    """
    Par (problema, solucao validada) que entra na base de conhecimento.

    E este objeto que faz a APRENDIZAGEM INCREMENTAL do RBC acontecer: ele e
    serializado em JSON e recarregado na proxima execucao, sem re-treinar nada.
    """
    id: int
    problema: Problema
    solucao_sugerida: list          # lista de CasoRecuperado
    avaliacao: Avaliacao
    tipo: str = "caso_de_sucesso"   # ou "caso_de_falha"
    data_hora: str = field(
        default_factory=lambda: datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    )

    def para_dict(self) -> dict:
        """Converte para dicionario serializavel em JSON."""
        return {
            "id": self.id,
            "data_hora": self.data_hora,
            "tipo": self.tipo,
            "problema": asdict(self.problema),
            "solucao_sugerida": [
                {
                    "nome": c.nome,
                    "valor_eur": c.valor,
                    "similaridade": round(c.similaridade, 4),
                    "distancia": round(c.distancia, 4),
                }
                for c in self.solucao_sugerida
            ],
            "avaliacao_especialista": asdict(self.avaliacao),
        }
