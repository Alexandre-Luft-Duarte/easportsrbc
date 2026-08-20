# -*- coding: utf-8 -*-
"""
O CICLO DOS 4 Rs (Aamodt & Plaza, 1994).

Cada etapa vive em seu proprio modulo, na ordem em que e executada:

    r1_recuperacao.py   Retrieve  -> achar os casos mais parecidos
    r2_reutilizacao.py  Reuse     -> propor e adaptar a solucao encontrada
    r3_revisao.py       Revise    -> o especialista humano valida
    r4_retencao.py      Retain    -> guardar o caso resolvido (aprender)

O ciclo e continuo: o que a Retencao guarda alimenta a Recuperacao seguinte.
"""

from .r1_recuperacao import recuperar
from .r2_reutilizacao import reutilizar
from .r3_revisao import revisar
from .r4_retencao import reter, MemoriaDeCasos

__all__ = ["recuperar", "reutilizar", "revisar", "reter", "MemoriaDeCasos"]
