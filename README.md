# Olheiro Virtual — Raciocínio Baseado em Casos (RBC)

Sistema de Recomendação de Contratações que, dado o perfil técnico de um jogador
ideal (caro demais) e um orçamento máximo, recupera na base do FIFA os jogadores
mais **similares** que **cabem no bolso** do clube.

Implementa o **Ciclo dos 4 Rs** do RBC (Aamodt & Plaza, 1994) usando
`scikit-learn` (KNN com Distância Euclidiana).

---

## Como rodar

```bash
pip install -r requirements.txt
python main.py
```

O programa pergunta qual temporada usar (`players_15` … `players_22`), coleta o
perfil desejado e o orçamento, e executa o ciclo completo.

---

## Estrutura do projeto

```
trab_rbc/
├── main.py                      # orquestração do ciclo (ler daqui primeiro)
├── requirements.txt
│
├── data/                        # BASE DE CASOS: um CSV por temporada
│   └── players_15.csv … players_22.csv
│
├── memoria/                     # o que a Retenção aprendeu, entre execuções
│   └── base_casos_aprendidos.json
│
├── rbc/                         # o pacote com toda a lógica
│   ├── config.py                # parâmetros, caminhos, mapeamento de colunas
│   ├── modelos.py               # Problema, CasoRecuperado, Avaliação, CasoAprendido
│   ├── base_casos.py            # carga, limpeza e consulta da Case Base
│   ├── similaridade.py          # normalização + distância euclidiana + KNN
│   │
│   ├── ciclo/                   # >>> UM ARQUIVO PARA CADA R <<<
│   │   ├── r1_recuperacao.py    # Retrieve
│   │   ├── r2_reutilizacao.py   # Reuse
│   │   ├── r3_revisao.py        # Revise
│   │   └── r4_retencao.py       # Retain
│   │
│   └── interface/               # terminal (entrada e saída)
│       ├── entrada.py
│       └── saida.py
│
└── legado/
    └── olheiro_virtual_v1.py    # versão monolítica, para comparação
```

A ideia da organização: **o ciclo do RBC é visível na própria árvore de pastas**,
não apenas nos comentários. Cada R é um módulo independente com uma única função
pública.

---

## O ciclo dos 4 Rs neste projeto

| Etapa | Arquivo | O que faz |
|---|---|---|
| **1. Recuperação** | `rbc/ciclo/r1_recuperacao.py` | (A) filtra a base pelo orçamento; (B) `NearestNeighbors(metric='euclidean')` sobre atributos normalizados |
| **2. Reutilização** | `rbc/ciclo/r2_reutilizacao.py` | exibe os candidatos com *delta* por atributo e economia gerada (adaptação) |
| **3. Revisão** | `rbc/ciclo/r3_revisao.py` | `input()` no terminal: o especialista aprova, rejeita, dá nota e justifica |
| **4. Retenção** | `rbc/ciclo/r4_retencao.py` | grava o par (problema, solução) em memória e em JSON — aprendizagem incremental |

---

## Decisões de projeto (para defender na apresentação)

**Por que filtrar o orçamento ANTES do KNN, e não depois?**
Se filtrássemos depois, os K vizinhos seriam gastos com craques impagáveis
(Mbappé, Haaland) e sobrariam poucos — ou nenhum — candidatos viáveis.
Filtrando antes, garantimos K sugestões que o clube realmente pode contratar.

**Por que normalizar com `MinMaxScaler`?**
A Distância Euclidiana soma diferenças ao quadrado em cada eixo. Sem
normalização, um atributo de escala maior dominaria a conta. Levando tudo a
`[0, 1]`, cada um dos 6 atributos pesa exatamente o mesmo.

**Por que `similaridade = 1 / (1 + d)`?**
Distância 0 (caso idêntico) vira 100%; a similaridade cai suavemente conforme a
distância cresce; nunca divide por zero; o resultado fica sempre em `(0, 1]`.

**Por que os goleiros somem da base?**
Eles não possuem `pace`, `shooting`, etc. no dataset — 2.198 dos 19.239
registros de `players_22` são removidos na limpeza. É uma **decisão de
modelagem**, não um bug: comparar goleiro com atacante nesses 6 eixos não
produziria similaridade útil.

**Por que guardar também os casos rejeitados?**
Na teoria do RBC, falha é conhecimento. Casos rejeitados entram como
`caso_de_falha` com a justificativa do especialista, registrando que aquele tipo
de recomendação não funcionou e por quê.

**Qual a diferença para Machine Learning tradicional?**
Uma rede neural precisaria ser re-treinada para incorporar um exemplo novo. O
RBC não: basta acrescentar o caso à base. O aprendizado é imediato, incremental
e — o mais importante num sistema de apoio à decisão — **auditável**, porque
cada caso guardado é legível por um humano.

---

## Dica de demonstração

Com orçamento de €15M, ~16.400 dos 17.041 jogadores passam no filtro — ou seja,
o filtro quase não filtra, porque a maioria dos jogadores do FIFA é barata.

Para a etapa de **Recuperação** mostrar o filtro fazendo diferença de verdade,
use um perfil de craque com orçamento apertado:

```
velocidade 95 | chute 90 | passe 85 | drible 93 | defesa 35 | físico 75
orçamento: 2000000
```

Aí fica visível o contraste entre "quem eu queria" e "quem eu consigo pagar" —
que é justamente a graça do sistema.
