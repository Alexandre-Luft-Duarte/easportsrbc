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
import math

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

    # ---------------------------------------------------- uso na recuperacao ---
    @staticmethod
    def _similaridade_problemas(perfil_atual, perfil_passado):
        """Compara dois perfis tecnicos na escala normalizada de 0 a 1."""
        atributos = sorted(set(perfil_atual) & set(perfil_passado))
        if not atributos:
            return 0.0
        distancia = math.sqrt(sum(
            ((float(perfil_atual[a]) - float(perfil_passado[a])) / 100.0) ** 2
            for a in atributos
        ))
        return 1.0 / (1.0 + distancia)

    def influencias(self, problema):
        """
        Calcula o reforco ou a penalizacao aprendida para cada jogador.

        Casos aprovados reforcam apenas a solucao escolhida pelo especialista.
        Casos rejeitados penalizam a lista que falhou, evitando repeti-la em
        problemas suficientemente semelhantes. Experiencias distantes nao
        interferem na consulta atual.
        """
        ajustes = {}
        experiencias_usadas = 0

        for caso in self.casos:
            perfil_passado = caso.get("problema", {}).get("perfil_desejado", {})
            relevancia = self._similaridade_problemas(
                problema.perfil_desejado, perfil_passado
            )
            if relevancia < config.LIMIAR_EXPERIENCIA_SEMELHANTE:
                continue

            avaliacao = caso.get("avaliacao_especialista", {})
            if caso.get("tipo") == "caso_de_sucesso":
                escolhido = avaliacao.get("escolhido")
                if not escolhido:
                    continue
                nota = avaliacao.get("nota")
                confianca = float(nota) / 10.0 if nota is not None else 0.5
                ajustes[escolhido] = ajustes.get(escolhido, 0.0) + (
                    config.PESO_SUCESSO_MEMORIA * relevancia * confianca
                )
                experiencias_usadas += 1
            elif caso.get("tipo") == "caso_de_falha":
                nomes = {
                    solucao.get("nome")
                    for solucao in caso.get("solucao_sugerida", [])
                    if solucao.get("nome")
                }
                for nome in nomes:
                    ajustes[nome] = ajustes.get(nome, 0.0) - (
                        config.PESO_FALHA_MEMORIA * relevancia
                    )
                if nomes:
                    experiencias_usadas += 1

        return ajustes, experiencias_usadas


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
