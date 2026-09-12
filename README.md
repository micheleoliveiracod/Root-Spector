<div align="center">

<img src="docs/brand/logo-lockup.png" alt="Root-Spector" width="720" />

![Python](https://img.shields.io/badge/Python-3.12-9184D9?style=flat-square&labelColor=0B0A10)
![LangGraph](https://img.shields.io/badge/LangGraph-agente-9184D9?style=flat-square&labelColor=0B0A10)
![FastAPI](https://img.shields.io/badge/FastAPI-backend-9184D9?style=flat-square&labelColor=0B0A10)
![React](https://img.shields.io/badge/React-frontend-9184D9?style=flat-square&labelColor=0B0A10)
[![CI](https://github.com/micheleoliveiracod/Root-Spector/actions/workflows/ci.yml/badge.svg)](https://github.com/micheleoliveiracod/Root-Spector/actions/workflows/ci.yml)
![License](https://img.shields.io/badge/licenca-todos%20os%20direitos%20reservados-9184D9?style=flat-square&labelColor=0B0A10)

</div>

---

# Root-Spector, Agente de Investigação de Causa Raiz de NC

**Desenvolvido por:** [Michele Oliveira](https://github.com/micheleoliveiracod)

**Organização:** Programa SCTEC e SENAI (https://github.com/IA-para-DEVs-SCTEC-T2)

**Curso:** IA para DEVs

**Objetivo:** Desenvolvimento de um mini projeto E2E com IA em todas as etapas, entregue em 2 fases do módulo 2.

## Fases de entrega

Este projeto foi entregue em duas fases do Módulo 2 do curso IA para DEVs:

- **Fase 1, entrega parcial**, submetida em 19/07/2026 (tag `v1.0-entrega`
  em `main`). Mini projeto E2E completo: agente LangGraph conduzindo uma
  investigação de causa raiz de não conformidade com Ishikawa e 5
  Porquês, backend FastAPI, frontend React, testes automatizados
  (pytest, Vitest e Playwright) e CI. Descrita na seção "Fase 1" logo
  abaixo.
- **Fase 2, entrega final**, desenvolvida de 22/08/2026 a 31/08/2026,
  sobre a mesma base da Fase 1, sem reescrever a arquitetura original.
  Adiciona os requisitos avançados do PDF do módulo: RAG, paralelização
  real no grafo, uma tool nova de recorrência, governança e guardrails de
  segurança, observabilidade, e documentação de QA e DevOps sobre
  trabalho real do próprio projeto. Descrita na seção "Fase 2" logo na
  sequência.

> **Status:** as duas fases estão implementadas e verificadas localmente
> (pytest, Vitest e Playwright), com CI verde. Detalhamento técnico da
> Fase 1 em `specs/requirements.md` e `specs/design.md`; da Fase 2 em
> `specs/fase02/requirements.md` e `specs/fase02/design.md`.

---

## Vídeo de demonstração

[Root-Spector em funcionamento](https://youtu.be/PQP-jA8mIXI)

---

## Fase 1, Entrega Parcial do Módulo 2

### Descrição do problema

Quando um processo produtivo gera uma Não Conformidade (NC), um lote fora
da especificação, o passo mais custoso do tratamento costuma ser
descobrir **por que** aconteceu, não só constatar que aconteceu. Essa
investigação normalmente depende de um especialista cruzando manualmente
o evento de NC com dados históricos de processo, um trabalho lento que
atrasa a correção enquanto o lote continua avançando no processo
produtivo.

O maior valor de um agente de IA nessa investigação é a agilidade. Com
dados de biosensor coletados em tempo real, a não conformidade é
identificada assim que ocorre, e a investigação de causa raiz pode
acontecer imediatamente, antes que o lote avance e se transforme em
produto final. Isso possibilita a correção enquanto o processo ainda está
em andamento, evitando desperdício de material e tempo, e reduzindo a
chance de o mesmo problema se repetir nos lotes seguintes. Um agente de
IA também traz imparcialidade e impessoalidade a essa investigação, por
não ser parte da equipe operacional, o que ajuda a evitar o viés
interpessoal de um colaborador da qualidade investigando um processo
conduzido por outro colaborador. No entanto, esse ganho é secundário diante do
ganho de agilidade, redução de desperdícios e a garantia da qualidade do produto.

### Objetivo do agente

Este agente é o **complemento de causa raiz** do
[BiotecPredict](https://github.com/micheleoliveiracod/Projeto-avaliativo-M1-2-BiotecPredict)
(projeto da mesma autora), uma plataforma que avalia lotes de bioprocesso
a partir de dados de biosensores por dois sinais independentes: um
`compliance_score` (0 a 100, classificável em ACCEPTABLE, WARNING ou
CRITICAL) e um `risk_prediction` de ML (LOW_RISK, MEDIUM_RISK ou
HIGH_RISK). O resultado é persistido num **banco SQLite** (`batches` e
`sensor_readings`, schema verificado diretamente no código-fonte do
BiotecPredict).

Ao abrir a aplicação, o operador vê a lista de lotes já classificada por
risco e escolhe um lote elegível para investigar. O agente identifica
deterministicamente qual ou quais parâmetros de biosensor estão fora da
faixa (comparando a média das leituras do lote contra
`config/regras_bioprocesso.yaml`) e então **facilita duas ferramentas de
qualidade em sequência com o operador**: primeiro um **diagrama de
Ishikawa** (6 perguntas de contexto, Método, Máquina, Material, Mão de
obra, Meio ambiente e Medição, não perguntas diretas sobre o parâmetro
fora da faixa), que identifica a categoria mais provável, e só então
aprofunda com o **método dos 5 Porquês** ancorado nessa categoria,
sempre 6 mais 5 rodadas, até sintetizar uma causa raiz sistêmica, gerando
o relatório. Ao final, o operador revisa a cadeia completa e pode **pedir
ajuste** (reabre um novo ciclo, preservando o anterior). Não é um agente
que investiga sozinho; é um agente que conduz a investigação em conjunto
com quem opera o processo.

**Case de referência:** biotecnologia, produção de
bioinsumos e bioprocessos. A solução é desenhada para ser adaptável a
outros setores produtivos trocando apenas os arquivos de
configuração/dados, ver "Adaptação a outro setor" em `specs/design.md`.
Este projeto começou desenhado para agronegócio e grãos e foi
reconfigurado para bioprocessos trocando só esses arquivos, na prática
validando esse requisito.

### Classificação da solução

Esta solução é classificada como um **agente**, não um workflow
determinístico nem um sistema híbrido. A diferença central está em quem
decide o próximo passo da investigação: os nós determinísticos do grafo
(leitura de biosensor, roteamento condicional) cuidam só da mecânica de
estado, mas o conteúdo da investigação (qual pergunta de Ishikawa
formular a seguir, qual categoria priorizar, quando invocar a ferramenta
`consultar_recorrencia`, como sintetizar a causa raiz e a recomendação de
tratativa) é decidido pelo LLM em tempo de execução, a partir do que o
operador responde, não por um roteiro fixo escrito antecipadamente. O LLM
também decide autonomamente, chamada a chamada, se e quando usar cada
ferramenta disponível (`consultar_leituras_biosensor` e
`consultar_recorrencia`), o que caracteriza um agente e não um workflow
de passos fixos. O LangGraph funciona aqui como motor de orquestração de
estado do agente, não como um mecanismo de regras que dispensaria o LLM.

### Arquitetura

- **Backend:** Python, LangGraph (motor do agente) e FastAPI (API).
- **Frontend:** React e TypeScript (Vite), uma única tela.
- **Dados de entrada:** `data/biotecpredict.db`, um arquivo SQLite (não
  versionado, ver "Como executar").

### Fluxo com LangGraph

```
Lote escolhido pelo operador na lista da interface web
   ↓
preparar_contexto        [determinístico: consulta batches (COMPLETED, com score), calcula sensor_metrics,
                           identifica parametros_fora_da_faixa, monta a NC]
   ↓
┌── FASE 1: ISHIKAWA (6 categorias, sempre nesta ordem) ───────────────┐
│ formular_pergunta_ishikawa ⇄ usar_ferramenta                         │
│    ↓                                                                  │
│ perguntar_operador  ← PONTO HUMAN-IN-THE-LOOP (via interface web)     │
│    ↓ (repete até as 6 categorias serem respondidas)                   │
└────────────────────────────────────────────────────────────────────┘
   ↓
orquestrar_analise   [nó LLM: identifica categoria_principal + categorias_descartadas]
   ↓
┌── FASE 2: 5 PORQUÊS (ancorado na categoria_principal) ───────────────┐
│ formular_porque ⇄ usar_ferramenta                                    │
│    ↓                                                                  │
│ perguntar_operador  ← PONTO HUMAN-IN-THE-LOOP                        │
│    ↓ (repete 5x)                                                       │
└────────────────────────────────────────────────────────────────────┘
   ↓
gerar_causa_raiz   [Diagnostico: Ishikawa + cadeia de 5 porquês + causa raiz]
   ↓
reports.py          [gera relatório JSON]
   ↓
Revisão pelo operador → link do relatório já disponível | pedir ajuste (reabre ciclo)
```

Este é o fluxo tal como entregue na Fase 1. A Fase 2 acrescenta um
fan-out real depois de `orquestrar_analise` e um nó novo de
recomendação, ver o diagrama atualizado na seção "Fase 2" abaixo.
Detalhamento completo (estado, mecanismo de interrupção e retomada do
LangGraph, por que é um agente e não só um workflow, estratégia de dados)
em `specs/design.md`.

### Ferramenta utilizada pelo agente

`consultar_leituras_biosensor(batch_id, data_inicio, data_fim)` executa
um `SELECT` somente leitura na tabela `sensor_readings` de
`data/biotecpredict.db`, restrito a um `batch_id` e a uma janela de
datas. Está disponível tanto em `formular_pergunta_ishikawa` quanto em
`formular_porque` (no máximo uma vez por pergunta), tipicamente mais
usada nas perguntas técnicas (Máquina e Medição, 5 Porquês) do que nas de
processo e pessoas (Método e Mão de obra). A Fase 2 adiciona uma segunda
tool, `consultar_recorrencia`, ver a seção "Fase 2".

### Como executar

```bash
# 1. Backend
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -e ".[dev]"
cp .env.example .env         # preencher a chave de API do provedor de LLM escolhido

# 2. Dados: colocar um arquivo biotecpredict.db (exportado do BiotecPredict,
#    schema em specs/design.md) em data/biotecpredict.db.
#    Os testes automatizados usam tests/fixtures/biotecpredict_teste.db
#    (fixture estática já incluída no repositório), nunca este arquivo real.

# 3. Subir a API
uvicorn backend.main:app --reload

# 4. Frontend (em outro terminal)
cd frontend
npm install
npm run dev
```

Abrir a URL indicada pelo Vite (padrão `http://localhost:5173`). A tela
inicial já lista os lotes de `data/biotecpredict.db` com sua
classificação. `LANGSMITH_TRACING` é opcional (Fase 2, observabilidade),
ver `docs/OBSERVABILIDADE.md`.

### Exemplo de entrada (formato)

Linha da tabela `batches` que dispara a investigação (schema real do
BiotecPredict; lote 11 do dataset de demonstração atual, ver "Estratégia
de dados" em `specs/design.md`):

```json
{
  "id": 11,
  "upload_date": "2026-07-05T08:00:00",
  "status": "COMPLETED",
  "compliance_score": 71.32,
  "risk_prediction": "MEDIUM_RISK"
}
```

`compliance_score=71.32` é classificado `WARNING` (entre 45 e 80, regra
real do BiotecPredict replicada em `config/regras_bioprocesso.yaml`).
`classification` não é uma coluna do banco, o agente calcula na hora. O
`risk_prediction` do modelo de ML concorda (`MEDIUM_RISK`).
`preparar_contexto` calcula `sensor_metrics` a partir de
`sensor_readings` e identifica `parametros_fora_da_faixa:
["dissolved_oxygen", "agitator_speed"]` (par correlacionado, menos
agitação resulta em menos transferência de oxigênio). Isso já vem pronto
quando o agente entra em ação; ele não descobre qual parâmetro é, ele
investiga por que esses parâmetros ficaram fora da faixa, primeiro
mapeando o contexto (Ishikawa), depois aprofundando (5 Porquês).

### Exemplo de interação (Ishikawa e 5 Porquês)

```
[Agente] (Máquina) O agitador deste lote operou dentro da velocidade
         (RPM) padrão do processo?
[Operador] Não, o setpoint do inversor de frequência estava abaixo do
           valor padrão.
[Agente] (Método) Houve alguma mudança de procedimento neste lote?
[Operador] Não, seguimos o procedimento padrão.
... (Material, Mão de obra, Meio ambiente, Medição)
```
(6 perguntas de contexto, depois a orquestração identifica `categoria_principal: "Máquina"`)

```
[Agente] Por que o agitador operou com velocidade abaixo do padrão?
[Operador] Porque o setpoint configurado no inversor de frequência estava
           abaixo do valor padrão do processo.
[Agente] Por que o setpoint estava abaixo do padrão?
[Operador] Porque foi alterado durante o ajuste do lote anterior e não foi
           restaurado.
[Agente] Por que não foi restaurado antes de iniciar este lote?
[Operador] ...
```
(continua até a 5ª pergunta, quando o relatório já é gerado; o operador
revisa e pode pedir ajuste, roteiro completo em
`docs/demo/gabarito-testes.md`)

### Cenário de risco: falha de todos os provedores de LLM

Nem sempre a chamada ao LLM tem sucesso. A cadeia de fallback configurada
em `config.py` tenta, em ordem, Groq, Gemini, Anthropic e OpenAI; se um
provedor falhar (limite de cota, erro de rede, chave inválida), o próximo
da lista assume automaticamente a mesma chamada, sem intervenção do
operador. O cenário de risco documentado é o caso em que todos os
provedores configurados falham na mesma chamada: a API responde HTTP 503
em vez de travar ou devolver um erro genérico, e o estado da investigação
em andamento não é perdido, porque o checkpointer do LangGraph já havia
persistido o passo anterior antes da chamada falhar. O operador pode
tentar novamente mais tarde, retomando exatamente do ponto em que a
cadeia de fallback foi esgotada, sem repetir perguntas já respondidas.
Esse comportamento está descrito em detalhe em `specs/design.md` e é o
motivo pelo qual o checkpointer é obrigatório mesmo numa arquitetura de
agente único, não multiagente.

### Exemplo de saída (formato)

Salvo em `reports/11_20260719T000000.json`:

```json
{
  "batch_id": 11,
  "categoria_principal": {
    "categoria": "Máquina",
    "justificativa": "Setpoint do inversor de frequência do agitador abaixo do padrão, coincide com a queda de agitator_speed e dissolved_oxygen"
  },
  "categorias_descartadas": [
    {"categoria": "Método", "motivo": "operador confirma procedimento padrão seguido"}
  ],
  "cadeia_de_porques": [
    {
      "numero": 1,
      "pergunta": "Por que o agitador operou com velocidade abaixo do padrão?",
      "resposta": "Porque o setpoint configurado no inversor de frequência estava abaixo do valor padrão do processo.",
      "evidencia": "agitator_speed e dissolved_oxygen fora da faixa aceitável (par correlacionado)"
    },
    {
      "numero": 2,
      "pergunta": "Por que o setpoint estava abaixo do padrão?",
      "resposta": "Porque foi alterado durante o ajuste do lote anterior e não foi restaurado ao valor padrão.",
      "evidencia": null
    }
  ],
  "causa_raiz": "Ausência de atualização do checklist de início de lote após a instalação de um novo inversor de frequência no agitador, permitindo que um setpoint de velocidade incorreto não fosse detectado antes do início do processo.",
  "narrativa": "...",
  "ciclos_anteriores": [],
  "gerado_em": "2026-07-19T00:00:00"
}
```

O PDF correspondente, com o mesmo conteúdo formatado para leitura, é
gerado sob demanda ao clicar em "Gerar relatório" na tela de revisão,
nunca salvo em disco. Essa é uma mudança da Fase 2, descrita na seção
abaixo (na Fase 1 esse relatório era um HTML estático, salvo junto do
JSON).

### Principais decisões (Fase 1)

- **LangGraph** com estado (`AgentState`), nós determinísticos e 4 nós
  agênticos (`formular_pergunta_ishikawa`, `orquestrar_analise`,
  `formular_porque`, `gerar_causa_raiz`), um `ToolNode`, e um ponto
  human-in-the-loop (`perguntar_operador`, reutilizado nas duas fases).
- **Interface web (FastAPI e React), não CLI.** O operador interage pelo
  navegador; o mecanismo de pausa e retomada usa `interrupt()` e um
  checkpointer do LangGraph, não `input()` bloqueante, que não funciona
  atrás de uma API, ver `specs/design.md`.
- **Ishikawa (6 categorias) antes de 5 Porquês.** O método dos 5 Porquês
  sozinho não prioriza entre causas de categorias diferentes (método,
  máquina, material, mão de obra, meio ambiente, medição); mapear o
  contexto primeiro evita ancorar a investigação numa categoria errada.
  Decisão informada por literatura de qualidade (ASQ, KaiNexus) e por um
  artigo acadêmico sobre RCA multiagente, ver `specs/design.md`.
- **"Orquestrador" e "relatório" são nós do mesmo grafo, não agentes
  separados.** Decisão deliberada de simplicidade; a literatura de
  referência usa arquitetura multiagente de verdade, mas replicar isso
  aqui adicionaria complexidade de coordenação sem necessidade.
- **Sempre exatamente 6 perguntas de Ishikawa e 5 Porquês, no máximo uma
  consulta à ferramenta por pergunta.** Decisão deliberada por
  previsibilidade, mesmo sabendo que a prática real do método às vezes
  para antes (ver `specs/design.md`).
- **Relatório gerado ao final de cada ciclo, revisão sempre disponível.**
  O relatório já é salvo assim que a cadeia é concluída (5º porquê
  respondido) e seu link aparece na tela de revisão; o operador pode
  pedir ajuste a qualquer momento, o que preserva o ciclo anterior (já
  reportado) em `ciclos_anteriores` (auditoria) e reabre um novo ciclo.
- **LLM plugável:** provedor e modelo escolhidos via variável de ambiente
  (`LLM_PROVIDER`/`LLM_MODEL`) usando `init_chat_model` do LangChain,
  com Google Gemini (gratuito) como padrão nesta entrega.
- **Entrada via SQLite, schema real do BiotecPredict.**
  `data/biotecpredict.db` (nunca versionado) é montado a partir de um
  dataset curado de demonstração, versionado em
  `data/simulacao_causa_raiz/` (15 lotes: 5 ideais mais 10 com um desvio
  de causa física única cada). Os valores de sensor são desenhados
  propositalmente, mas `compliance_score`, `classification` e
  `risk_prediction` não são inventados: vêm de rodar o
  `ComplianceService`/`MLModel` reais e inalterados do BiotecPredict
  sobre esses dados, ver "Estratégia de dados" em `specs/design.md`. Os
  limiares de classificação (80 ou mais ACCEPTABLE, 45 ou mais WARNING,
  abaixo disso CRITICAL) foram conferidos linha a linha em
  `ComplianceService._classify_score()` do BiotecPredict, não apenas no
  README dele. Uma fixture sintética estática
  (`tests/fixtures/biotecpredict_teste.db`) existe só para os testes
  automatizados.

### Limitações (Fase 1)

- A classificação e a detecção da NC não são feitas por este agente,
  vêm do BiotecPredict. O agente lê um arquivo de banco local (exportado
  manualmente), não uma conexão ao vivo com uma instância em execução.
- Cobre um parâmetro fora da faixa por lote; múltiplos parâmetros fora da
  faixa simultaneamente exigiriam ciclos e NCs separadas.
- Os loops sempre completam todas as perguntas (6 Ishikawa e 5 Porquês),
  mesmo que a categoria ou a causa fique óbvia antes; não implementa
  parada antecipada.
- Lotes com `compliance_score` nulo (processados mas sem score
  atribuído) são excluídos da lista de elegíveis. A Fase 2 corrigiu um
  problema relacionado, ver "Correção de elegibilidade" abaixo.

### Adaptação a outro setor produtivo

Ver seção correspondente em `specs/design.md`.

---

## Fase 2, Entrega Final do Módulo 2

A Fase 2 desenvolve, sobre a mesma arquitetura da Fase 1, os requisitos
avançados do PDF do módulo: RAG, paralelização, tool nova, governança,
observabilidade, QA e DevOps inteligentes. Mapeamento completo contra o
PDF em `specs/fase02/requirements.md`; desenho técnico em
`specs/fase02/design.md`.

### RAG (memória e recomendação de tratativa)

O novo nó `pre_busca_rag` consulta uma base de conhecimento curada
(`data/base_conhecimento/`) por similaridade semântica (chunking real,
embedding e vector store, não busca por palavra-chave). O novo nó
`recomendar_tratativa` sintetiza uma recomendação de ação corretiva e
preventiva a partir da causa raiz e dos trechos recuperados. Detalhado em
`docs/RAG.md`.

### Refinamento documentado: falha silenciosa no `pre_busca_rag`

Durante a construção da análise de observabilidade desta fase (ver
"DevOps inteligente" abaixo), os dados reais de `eventos_log` mostraram
uma anomalia concreta: o nó `pre_busca_rag` executou 10 vezes numa única
investigação do lote 606, quando o esperado é uma única execução por
chamada do grafo. A causa raiz foi rastreada até `rag.py`: a função de
embeddings do Gemini falhava sem tratamento de exceção, e o retry
automático de nó do LangGraph reexecutava o nó inteiro repetidamente, sem
nunca degradar de forma previsível. A mudança feita foi envolver a busca
em `pre_busca_rag` num bloco try/except, registrar a falha via log
estruturado e devolver uma lista vazia de candidatos em vez de deixar a
exceção subir, com um teste de regressão dedicado
(`tests/test_pre_busca_rag_falha_embeddings.py`) provando o comportamento
antes e depois da correção. O resultado, medido no antes e depois do
deploy dessa correção (16:47 UTC), está documentado com números reais em
`docs/fase02/devops/analise-desempenho-agente.ipynb`: a duração média por
evento caiu de 2,77 para 0,98 segundos, e as execuções indevidas de
`pre_busca_rag` caíram de 7 em 85 eventos para 3 em 193 eventos.

### Paralelização real no grafo

Depois de `orquestrar_analise`, o grafo faz um fan-out genuíno: o loop
dos 5 Porquês e `pre_busca_rag` rodam na mesma superstep do LangGraph, não
em sequência disfarçada. Um teste dedicado (`tests/test_paralelizacao.py`)
prova isso com uma barreira de sincronização: se a execução fosse
sequencial, o teste travaria por timeout.

```
orquestrar_analise
   ├──> formular_porque (loop 5 Porquês, com o operador)
   └──> pre_busca_rag (busca na base de conhecimento, roda em paralelo)
   ambos convergem em ──> recomendar_tratativa
```

### Tool nova: `consultar_recorrencia`

Segunda ferramenta do agente, decidida pelo LLM (não uma automação por
agenda): verifica se a não conformidade atual já ocorreu antes,
comparando categoria principal e parâmetros fora da faixa contra
investigações anteriores (`reports/*.json`). O resultado entra no
relatório de forma estruturada (`Diagnostico.casos_semelhantes`), não só
em texto solto.

### Governança e guardrails de segurança

Teste de cenário adversarial de prompt injection
(`tests/test_seguranca_prompt_injection.py`), mais quatro guardrails
novos: limite de tentativas de resposta rejeitada por pergunta, limite de
tamanho da resposta do operador, CORS restrito com limite de taxa por IP
na API, e uma chave de API interna exigida nas rotas de lotes,
investigações e resumo diário. Análise completa, incluindo os guardrails
estruturais que já existiam desde a Fase 1, em `docs/GOVERNANCA.md`.

### Observabilidade

Dois sinais correlacionados: logging estruturado (JSON) por nó do grafo
executado (`config.py`/`graph.py`), persistido também numa tabela
`eventos_log` (SQLite local, `data/observabilidade.db`, por padrão;
Postgres, a mesma instância do checkpointer, quando `DATABASE_URL`
estiver definida, consultável direto por uma ferramenta de BI), e trace
opcional do LangSmith (`LANGSMITH_TRACING`). Um callback dedicado
registra cada tentativa de chamada de LLM dentro da cadeia de fallback,
incluindo as que falham antes do próximo provedor assumir, com provedor,
modelo, duração e sucesso ou erro, permitindo comparar desempenho e
confiabilidade entre provedores. A consulta SQL da tool de biosensor tem
timeout e retry explícitos. Detalhado em `docs/OBSERVABILIDADE.md`.

### QA inteligente

Code review de IA sobre um PR de código real do próprio projeto (os
guardrails de governança), com achados concretos, mais o teste de prompt
injection registrado como o teste priorizado por risco desta fase, com a
justificativa da prioridade. Em `docs/fase02/qa/code-review-ia.md`.

### DevOps inteligente

Análise de um incidente real de CI deste repositório: explicação de log
de duas etapas do pipeline (lint e E2E), detecção e explicação de uma
anomalia real (uma mensagem de erro genérica mascarando a causa raiz
verdadeira), e uma estimativa de tendência de taxa de falha, tudo com
dados reais coletados via `gh api`. Em
`docs/fase02/devops/analise-incidente-ci.md`.

### Relatório em PDF, gerado sob demanda

O JSON é salvo automaticamente ao fim de cada investigação
(`reports/*.json`, usado inclusive por `consultar_recorrencia`). O
relatório para leitura humana é um PDF gerado na hora, ao clicar em
"Gerar relatório" na tela de revisão, nunca persistido em disco.

### Low-code: resumo diário por e-mail (n8n)

Endpoint `GET /api/relatorios/resumo-diario` varre `reports/*.json` do dia
pedido (padrão: o dia anterior) e devolve, por investigação, classificação,
risco, categoria principal, causa raiz, recorrência e recomendação de
tratativa, mais o link do relatório em PDF sob demanda. Agrega também a
eficiência operacional do dia a partir do log estruturado: tempo médio por
investigação, tempo médio por nó, respostas com 2 tentativas, e o
desempenho de cada provedor de LLM na cadeia de fallback (quantas chamadas,
quantas falharam, duração média), útil para investigar problemas reais de
fallback, não só contar quantas vezes ele foi acionado. Quem quiser ir
além desse resumo pode conectar uma ferramenta de BI direto em
`data/observabilidade.db` (a mesma tabela `eventos_log` usada aqui) e
consultar a sequência exata de eventos com SQL, sem depender de nenhum
resumo pronto. O workflow no n8n (Cron Trigger, HTTP Request, IF, Set,
Send Email) foi construído manualmente na interface do n8n, consumindo o
endpoint acima. Instruções de construção, passo a passo, em
`docs/fase02/low-code/construcao-workflow-n8n.md`.

### Planejado, ainda não implementado

- **Nenhum item de escopo do PDF ficou pendente.** O deploy em produção
  (Render, Vercel e Azure), fora do escopo avaliado do PDF mas executado
  como exercício de aprendizado, está no ar: o checkpointer do grafo e a
  tabela `eventos_log` já usam o Postgres do Azure quando `DATABASE_URL`
  está definida, e o relatório de cada investigação é persistido na
  tabela `relatorios` desse mesmo banco, verificado com investigações
  reais rodando em produção. Plano completo em
  `specs/deploy-producao/plano.md`.

---

## Documentação relacionada

**Fase 1:**
- `docs/PRD.md`, documento de requisitos de produto (problema, público, escopo, critérios de sucesso)
- `docs/cenarios-de-uso.md`, cenários de uso passo a passo (fluxo principal, validação, erro e ajuste)
- `docs/diagrama-fluxo.md`, diagramas Mermaid do grafo LangGraph e da sequência de chamadas HTTP
- `docs/openapi.yaml`, contrato completo da API (gerado a partir do schema real do FastAPI)
- `specs/requirements.md`, requisitos funcionais e não funcionais
- `specs/design.md`, arquitetura, fluxo do grafo, estratégia de dados
- `docs/prompts.md`, prompts usados para planejar e implementar o agente
- `docs/gitflow.md`, modelo de branches, CI/CD, convenções de commit e PR
- `docs/apresentacao.md`, conteúdo da apresentação de 2 slides
- [BiotecPredict](https://github.com/micheleoliveiracod/Projeto-avaliativo-M1-2-BiotecPredict), projeto complementar (classificação de risco do lote)

**Fase 2:**
- `specs/fase02/requirements.md`, mapeamento de cada critério do PDF do módulo
- `specs/fase02/design.md`, desenho técnico de cada requisito novo
- `specs/fase02/gitflow.md`, branches e issues específicas da Fase 2
- `docs/RAG.md`, retrieval-augmented generation e recomendação de tratativa
- `docs/GOVERNANCA.md`, guardrails de segurança, estruturais e novos
- `docs/OBSERVABILIDADE.md`, logging estruturado e trace do LangSmith
- `docs/fase02/qa/code-review-ia.md`, code review de IA e teste priorizado por risco
- `docs/fase02/devops/analise-incidente-ci.md`, análise de incidente real de CI
- `docs/fase02/low-code/construcao-workflow-n8n.md`, passo a passo de construção do workflow no n8n
- `docs/demo/gabarito-testes.md`, roteiro de teste com os lotes elegíveis do dataset atual
- `specs/deploy-producao/plano.md`, plano de deploy (Render, Vercel e Azure), fora do escopo avaliado

---

## ⭐ Agradecimentos

- **SCTEC e SENAI:** Programa de IA para DEVs
- **Comunidade Open Source:** ferramentas e bibliotecas utilizadas

---

## 👩🏻‍💻 Desenvolvedora

**Desenvolvido com 💜 por Michele Oliveira**
- GitHub: [@micheleoliveiracod](https://github.com/micheleoliveiracod)
- Email: [data.analystmlso@gmail.com](mailto:data.analystmlso@gmail.com)

**Última atualização:** 29 de agosto de 2026

---

## 📄 Licença do Projeto

Copyright (c) 2026 Michele Oliveira. Todos os direitos reservados.

A Fase 1 (mini-projeto avaliativo, entregue em 19/07/2026) foi
licenciada sob a Apache License 2.0. A partir do início da construção
da Fase 2, o projeto passou a ser proprietário.

Este código é disponibilizado publicamente apenas para fins de consulta,
avaliação acadêmica e portfólio. É permitido baixar e executar o projeto
localmente, para estudo pessoal. Não é permitido copiar, modificar,
redistribuir ou usar este código para fins comerciais sem autorização
prévia e por escrito da autora. Ver [LICENSE](LICENSE) para o texto
completo.
