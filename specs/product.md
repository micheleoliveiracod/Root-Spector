# Produto: Root-Spector — Investigação de Causa Raiz de Não Conformidades

## Visão do Produto

Agente de IA (LangGraph) que conduz, em conjunto com um operador humano, a
investigação de causa raiz de uma não conformidade (NC) de processo
produtivo — mapeando o contexto do desvio com um diagrama de Ishikawa e
aprofundando na categoria mais provável com o método dos 5 Porquês —, e
produz um relatório estruturado da causa raiz identificada.

> ⚠️ O produto **não substitui o especialista de qualidade**. O agente
> facilita e acelera a coleta e a síntese de informação; a validação da
> causa raiz e a decisão sobre a ação corretiva são sempre do operador, que
> revisa o relatório já gerado (ou pede ajuste, reabrindo um novo ciclo).

---

## Problema

Tratar uma não conformidade de processo produtivo exige identificar a causa
raiz do desvio, e essa investigação costuma depender de um especialista que
cruza manualmente o evento com o histórico do processo:

- A investigação não segue um método estruturado de forma consistente —
  fica sujeita a quem conduz e a quanto tempo essa pessoa tem disponível.
- Cruzar o desvio com o histórico de sensores é manual e demorado.
- O registro da análise (perguntas feitas, respostas obtidas, raciocínio)
  raramente fica documentado de forma rastreável.
- Quando há mais de uma categoria possível de causa (método, máquina,
  material, mão de obra, meio ambiente, medição), não há um jeito
  sistemático de priorizar por onde começar antes de aprofundar.
- Um colaborador da qualidade investigando a NC de um processo operacional
  realizado por outro colaborador carrega um viés interpessoal difícil de
  eliminar — um agente de IA traz imparcialidade e impessoalidade a essa
  investigação, por não ser parte da equipe operacional.
- Quanto mais lenta a investigação e o tratamento da causa, maior o risco
  de o lote seguir avançando no processo produtivo e se transformar em
  produto antes do problema ser endereçado — aumentando o desperdício.
  Agilidade no processo de investigação reduz essa janela de risco.

---

## Solução

Uma plataforma web local que:

- Lista os lotes já classificados por risco (saída do BiotecPredict),
  destacando os elegíveis para investigação (risco médio/alto).
- Conduz uma conversa estruturada em duas fases com o operador: primeiro um
  mapeamento de contexto por categoria (Ishikawa/6M), depois um
  aprofundamento de 5 Porquês ancorado na categoria mais provável
  identificada.
- Consulta o histórico de leituras de biosensor do lote como evidência,
  quando a pergunta em curso se beneficia de dado bruto.
- Valida a resposta do operador em duas camadas — rejeita respostas vazias
  ou evasivas, e dá até 2 chances quando uma resposta não é informativa —
  para manter a qualidade da investigação sem travar o fluxo indefinidamente.
- Sintetiza a cadeia completa numa causa raiz estruturada, gera o relatório
  e apresenta ao operador pra revisão, que pode pedir ajuste (reabrindo um
  novo ciclo, com o anterior preservado para auditoria).
- Produz o relatório final em JSON (consumo por outros sistemas) e HTML
  (leitura humana).

---

## Público-Alvo

- Operadores de processo/qualidade de manufatura de bioprocessos.
- Analistas/engenheiros de qualidade responsáveis por investigação de NC.

---

## Objetivos

- Estruturar a investigação de causa raiz com um método de qualidade
  reconhecido (Ishikawa + 5 Porquês), não uma conversa livre.
- Reduzir o tempo de condução da investigação, sem eliminar o julgamento
  humano do operador.
- Deixar rastreável cada pergunta, resposta e evidência consultada.
- Adaptar-se a outros setores produtivos trocando apenas `config/` e
  `data/` — o motor do agente (`root_cause_agent/`) não muda.

---

## Escopo desta entrega

**Dentro do escopo:**
- Leitura de lotes reprovados/classificados a partir de
  `data/biotecpredict.db` (schema real do BiotecPredict, classificado pelo
  motor real do BiotecPredict — ver `specs/design.md` § Estratégia de
  dados para a proveniência).
- Mapeamento Ishikawa (6 categorias fixas) + 5 Porquês (ancorado na
  categoria mais provável), conduzidos via interface web com
  human-in-the-loop (`interrupt()`/checkpointer do LangGraph).
- Consulta de leituras de biosensor como ferramenta do agente, restrita ao
  lote sob investigação e a uma janela de datas validada.
- Validação em duas camadas da resposta do operador (rejeição
  determinística de vazio/evasiva + julgamento de informatividade pelo LLM,
  até 2 tentativas por pergunta).
- Revisão do operador com o relatório já gerado, e opção de pedido de
  ajuste (novo ciclo, histórico preservado).
- Relatório final em JSON + HTML.
- Fallback de LLM em cadeia (Gemini → Groq → Anthropic → OpenAI) para
  resiliência a falhas de rede/rate limit/chave.

**Fora do escopo (nesta entrega — ver `specs/requirements.md` para a lista
completa):**
- Detecção automática da NC (já chega classificada como entrada).
- Segundo agente (RAG) para recomendação de plano PDCA e fluxo de Garantia
  da Qualidade — roadmap, ver `specs/design.md` § Roadmap.
- Múltiplos parâmetros fora da faixa simultaneamente tratados como NCs
  separadas.
- Adaptação simultânea a mais de um setor produtivo nesta entrega.

---

## Categorias do Ishikawa (6M)

| Categoria | Exemplo de pergunta de contexto |
|---|---|
| **Método** | Houve mudança de procedimento ou receita neste lote? |
| **Máquina** | Algum equipamento recebeu manutenção corretiva recente ou está com a preventiva atrasada? |
| **Material** | Os insumos usados são do fornecedor/lote habituais? |
| **Mão de obra** | Houve troca de equipe, treinamento pendente ou execução fora do padrão? |
| **Meio ambiente** | Houve condição ambiental atípica durante o lote? |
| **Medição** | Os sensores estão com calibração em dia? |

As perguntas-modelo ficam em `config/regras_bioprocesso.yaml` e são
adaptadas pelo agente ao contexto específico da NC, não repetidas
literalmente.

---

## Entrada (herdada do BiotecPredict)

O BiotecPredict avalia lotes de bioprocesso por dois sinais independentes,
ambos confirmados no código-fonte real:

| Sinal | Faixa | Classificação |
|---|---|---|
| `compliance_score` | 80–100 | ACCEPTABLE |
| `compliance_score` | 45–79 | WARNING |
| `compliance_score` | 0–44 | CRITICAL |
| `risk_prediction` | — | LOW_RISK / MEDIUM_RISK / HIGH_RISK (saída de ML, sinal independente) |

Lotes `WARNING`/`CRITICAL` são os elegíveis para investigação — é dessa
lista, já classificada, que o operador escolhe o lote.

---

## Saída Esperada por Investigação

Para cada investigação concluída, o sistema produz um `Diagnostico`
(`reports/{batch_id}_{timestamp}.json` + `.html`) contendo:

- A NC original (eco, para rastreabilidade).
- As 6 respostas do mapeamento Ishikawa, com a categoria principal
  identificada (e justificativa) e as categorias descartadas (com motivo).
- A cadeia completa dos 5 Porquês (pergunta, resposta, tentativas,
  informatividade, evidência quando consultada).
- A causa raiz sintetizada e uma narrativa curta do raciocínio.
- Os ciclos anteriores, se o operador tiver pedido ajuste alguma vez.

---

## Fonte de Dados

**Demonstração:** `data/biotecpredict.db` — nunca versionado, colocado
manualmente em `data/`, montado a partir do dataset curado e versionado
`data/simulacao_causa_raiz/` (15 lotes: 5 ideais + 10 com um desvio de
causa física única cada), classificado pelo motor real (não reimplementado)
do BiotecPredict — ver `specs/design.md` § Estratégia de dados para a
proveniência completa. `docs/demo/gabarito-testes.md` tem o roteiro de
respostas esperadas pros dois lotes elegíveis do dataset atual.

**Teste:** `tests/fixtures/biotecpredict_teste.db` — fixture sintética e
determinística, arquivo estático e versionado, usada exclusivamente pelos
testes automatizados — nunca pela aplicação em execução.

---

## Roadmap (fora desta entrega)

Ver `specs/design.md` § Roadmap para o desenho completo: um segundo agente
(RAG) consultando documentação da empresa/legislação/ANVISA/bibliografia
para recomendar um plano PDCA (ação corretiva + Kaizen), avaliado pela
Garantia da Qualidade em conjunto com a Coordenação da Produção, executado
e verificado quanto à eficácia por reincidência — fechando um ciclo PDCA
completo. Exige infraestrutura (ingestão de documentos, embeddings, vector
store) fora do escopo desta entrega.
