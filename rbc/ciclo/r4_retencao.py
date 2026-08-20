# -*- coding: utf-8 -*-
"""
================================================================================
 4o R - RETENCAO (Retain)
================================================================================

 Aqui acontece a APRENDIZAGEM INCREMENTAL do RBC: o par (problema, solucao
 validada) vira um NOVO CASO e entra na base de conhecimento. Da proxima vez que
 um problema parecido aparecer, o sistema ja tera essa experiencia disponivel.

 A DIFERENCA PARA O MACHINE LEARNING TRADICIONAL
 -----------------------------------------------
 Uma rede neural precisaria ser RE-TREINADA para incorporar um exemplo novo.
 O RBC nao: basta acrescentar o caso a base. O aprendizado e imediato,
 incremental e - o mais importante para um sistema de apoio a decisao -
 totalmente AUDITAVEL, porque cada caso guardado e legivel por um humano.

 APRENDER COM O ERRO
 -------------------
 Casos REJEITADOS tambem sao retidos, marcados como "caso_de_falha". Na teoria
 do RBC isso e conhecimento valioso: registra que aquele tipo de recomendacao
 nao funcionou, e por que.

 A memoria vive em dois lugares:
   * MemoriaDeCasos.casos           -> lista em memoria, durante a execucao
   * memoria/base_casos_aprendidos.json -> persistencia entre execucoes
================================================================================
"""

import json

from .. import config
from ..modelos import CasoAprendido
from ..interface import saida


class MemoriaDeCasos:
    """
    A base de conhecimento aprendida pelo sistema.

    Encapsular a lista numa classe deixa explicito que ela e um COMPONENTE do
    RBC (a memoria), e nao uma variavel global qualquer.
    """

    def __init__(self):
        self.casos = []   # <<< a base de casos aprendidos, em memoria

    def __len__(self):
        return len(self.casos)

    # ------------------------------------------------------------ carga ---
    def carregar(self):
        """Recarrega os casos aprendidos em execucoes anteriores."""
        if not config.ARQUIVO_MEMORIA.exists():
            return self

        try:
            with open(config.ARQUIVO_MEMORIA, encoding="utf-8") as arquivo:
                self.casos = json.load(arquivo)
            print("[Memoria] {} caso(s) recuperados de execucoes anteriores."
                  .format(len(self.casos)))
        except (OSError, json.JSONDecodeError) as erro:
            print("[Memoria] Nao foi possivel ler a memoria ({}). Comecando vazia."
                  .format(erro))
            self.casos = []
        return self

    # ------------------------------------------------------- persistencia ---
    def salvar(self):
        """Grava a base de casos em disco, em JSON legivel."""
        try:
            config.PASTA_MEMORIA.mkdir(parents=True, exist_ok=True)
            with open(config.ARQUIVO_MEMORIA, "w", encoding="utf-8") as arquivo:
                json.dump(self.casos, arquivo, ensure_ascii=False, indent=2)
            return True
        except OSError as erro:
            print("\n(Nao foi possivel gravar o arquivo: {})".format(erro))
            return False

    # ---------------------------------------------------------- retencao ---
    def reter(self, problema, recuperados, avaliacao):
        """Monta o novo caso, adiciona a memoria e persiste."""
        novo_caso = CasoAprendido(
            id=len(self.casos) + 1,
            problema=problema,
            solucao_sugerida=recuperados,
            avaliacao=avaliacao,
            tipo="caso_de_sucesso" if avaliacao.aprovado else "caso_de_falha",
        )
        self.casos.append(novo_caso.para_dict())
        self.salvar()
        return novo_caso

    # ---------------------------------------------------------- relatorio ---
    def resumo(self):
        """Contagem de sucessos e falhas na base de conhecimento."""
        sucessos = sum(1 for c in self.casos if c.get("tipo") == "caso_de_sucesso")
        falhas = sum(1 for c in self.casos if c.get("tipo") == "caso_de_falha")
        return sucessos, falhas


def reter(memoria, problema, recuperados, avaliacao):
    """
    Executa a etapa de Retencao e relata o que foi aprendido.
    """
    saida.cabecalho(">>> 4o R - RETENCAO (Retain)")

    novo_caso = memoria.reter(problema, recuperados, avaliacao)

    if avaliacao.aprovado:
        # Caso de SUCESSO: reforca o conhecimento do sistema.
        print("Caso APROVADO adicionado a base de casos (id {}).".format(novo_caso.id))
        print("   Problema : {}".format(problema.perfil_desejado))
        print("   Restricao: teto de " + saida.fmt_eur(problema.orcamento))
        print("   Solucao  : {}".format(avaliacao.escolhido))
        print("   Confianca: nota {}/10 do especialista".format(avaliacao.nota))
    else:
        # Caso de FALHA: no RBC, erros tambem sao conhecimento util -
        # evitam que o sistema repita a mesma recomendacao ruim.
        print("Caso de FALHA registrado (id {}).".format(novo_caso.id))
        print("   Aprender com o erro tambem e RBC.")
        print("   Motivo: {}".format(avaliacao.obs or "(nao informado)"))

    sucessos, falhas = memoria.resumo()
    print("\nBase de casos gravada em: {}"
          .format(config.ARQUIVO_MEMORIA.relative_to(config.RAIZ)))
    print("Conhecimento acumulado: {} caso(s) - {} sucesso(s), {} falha(s)."
          .format(len(memoria), sucessos, falhas))

    return novo_caso
