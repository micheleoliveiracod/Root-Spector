# Apresentação — Root-Spector (2 slides)

## Slide 1 — O problema e o agente

**Problema**
O tratamento de uma não conformidade de processo produtivo exige
identificar a causa raiz do desvio. Essa investigação costuma depender de um especialista, que cruza
manualmente o evento com o histórico do processo, com registro da análise. Isso aumenta o tempo de conclusão da investigação, da ação corretiva e dos planos de melhoria. O uso do agente serve para conduzir as perguntas e gerar os relatórios, garantindo a imparcialidade e agilidade na investigação.

**Processo automatizado**
A etapa de investigação de causa raiz de um desvio, realizada após a classificação de
risco de um lote. Dado um lote reprovado, com o parâmetro de processo já
identificado, o agente aplica duas ferramentas de qualidade em sequência:
um diagrama de Ishikawa, para mapear o contexto do desvio por categoria, e
o método dos 5 Porquês, para aprofundar a investigação na categoria
identificada. Cada etapa é conduzida em conjunto com o operador.

**Proposta do agente**
Agente construído com LangGraph, complementar ao
[BiotecPredict](https://github.com/micheleoliveiracod/Projeto-avaliativo-M1-2-BiotecPredict),
plataforma que classifica lotes de bioprocesso a partir de dados de
biosensores. O operador seleciona, em uma lista já classificada por risco,
o lote a ser investigado, e conduz a investigação com o agente por meio de
uma interface web. Ao final, o relatório já é gerado e o operador revisa as
respostas registradas, podendo solicitar ajuste, reabrindo um novo ciclo de
investigação. Mas o histórico do primeiro ciclo fica salvo, para rastreabilidade e auditoria de todos os dados.

**Case de referência**
Biotecnologia — bioprocessos/produção de bioinsumos. Os dados de
demonstração vêm de um dataset curado e versionado
(`data/simulacao_causa_raiz/`), classificado pelo motor real do
BiotecPredict (não inventado). O motor do agente foi desenhado para ser
adaptável a outros setores produtivos, mediante alteração dos arquivos de
configuração e de dados, sem alteração do código — o projeto, aliás,
começou desenhado para agronegócio/grãos e foi re-configurado para
bioprocessos trocando só esses arquivos, validando esse requisito na
prática.

---

## Slide 2 — Entrada, saída e fluxo

**Entrada esperada** (linha de `batches`, schema real do BiotecPredict, lida
de `data/biotecpredict.db`; lote 11 do dataset de demonstração atual)
```json
{
  "id": 11,
  "status": "COMPLETED",
  "compliance_score": 71.32,
  "risk_prediction": "MEDIUM_RISK"
}
```
`preparar_contexto` calcula `sensor_metrics` e identifica
`parametros_fora_da_faixa: ["dissolved_oxygen", "agitator_speed"]` antes do
agente entrar em ação.

**Saída esperada**
`Diagnostico` estruturado — mapeamento Ishikawa (categoria principal +
categorias descartadas) + cadeia completa dos 5 Porquês (pergunta +
resposta do operador + evidência, quando consultada) + causa raiz
sintetizada + narrativa — salvo como relatório em **JSON** (consumo por
outros sistemas) e **HTML** (leitura humana, link exibido ao operador assim
que o ciclo é concluído).

**Visão geral do fluxo**
```
Lote escolhido pelo operador → preparar_contexto
   ↓
Ishikawa (6 perguntas) → orquestrar_analise (categoria_principal)
   ↓
5 Porquês (ancorado na categoria) → gerar_causa_raiz → relatório (JSON+HTML)
   ↓
Revisão do operador → link do relatório já disponível | pedir ajuste (novo ciclo)
```

- `preparar_contexto`: identifica o(s) parâmetro(s) fora da faixa (determinístico).
- `formular_pergunta_ishikawa`: nó LLM — pergunta de contexto por categoria (6x).
- `orquestrar_analise`: nó LLM — identifica a categoria mais provável.
- `formular_porque`: nó LLM — pergunta "por quê" ancorada na categoria (5x).
- `usar_ferramenta`: consulta o histórico de biosensor do lote via tool, se precisar de mais evidência.
- `perguntar_operador`: interface web, human-in-the-loop, reusado nas duas fases.
- `gerar_causa_raiz`: sintetiza tudo na causa raiz final e gera o relatório; operador revisa e pode pedir ajuste.
