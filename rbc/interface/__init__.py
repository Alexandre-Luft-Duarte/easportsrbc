# -*- coding: utf-8 -*-
"""
Camada de interface com o usuario (terminal).

Manter entrada e saida isoladas do ciclo RBC permitiria trocar o terminal por
uma interface grafica ou web sem alterar a logica do raciocinio.
"""

from . import entrada, saida

__all__ = ["entrada", "saida"]
