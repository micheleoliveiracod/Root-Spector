# PRD — Root-Spector

Documento de requisitos de produto, para leitura rápida do problema, do
público, do escopo e dos critérios de sucesso. Não substitui os documentos
técnicos canônicos — cada seção aponta para onde o detalhe completo vive
(`specs/product.md`, `specs/requirements.md`, `specs/design.md`). Em caso
de divergência, os arquivos em `specs/` são a fonte da verdade.

## 1. Resumo executivo

Root-Spector é um agente de IA (LangGraph) que conduz, em conjunto com um
operador humano, a investigação de causa raiz de uma Não-Conformidade (NC)
de processo produtivo — mapeando o contexto do desvio com um diagrama de
Ishikawa e aprofundando na categoria mais provável com o método dos 5
Porquês — e produz um relatório estruturado (JSON + HTML) da causa raiz
identificada. É o complemento de causa raiz do
[BiotecPredict](https://github.com/micheleoliveiracod/Projeto-avaliativo-M1-2-BiotecPredict)
(projeto da mesma autora), que classifica lotes de bioprocesso por risco a
partir de dados de biosensores.

## 2. Problema

Tratar uma NC de processo produtivo exige identificar a causa raiz do
desvio — um passo tipicamente manual, sujeito a três limitações:

- **Inconsistência de método**: a investigação não segue um método
  estruturado de forma consistente; fica sujeita a quem conduz e a quanto
  tempo essa pessoa tem disponível.
- **Falta de rastreabilidade**: o registro da análise (perguntas feitas,
  respostas obtidas, raciocínio) raramente fica documentado de forma
  auditável.
- **Viés interpessoal**: um colaborador da qualidade investigando a NC de
  um processo operacional realizado por outro colaborador carrega um viés
  difícil de eliminar.

Quanto mais lenta a investigação, maior o risco de o lote avançar no
processo produtivo e se transformar em produto antes do problema ser
endereçado — agilidade reduz essa janela de risco. Detalhamento completo
em `specs/product.md` § Problema.

## 3. Objetivos

- Estruturar a investigação de causa raiz com um método de qualidade
  reconhecido (Ishikawa + 5 Porquês), não uma conversa livre.
- Reduzir o tempo de condução da investigação, sem eliminar o julgamento
  humano do operador — o agente facilita e acelera a coleta/síntese de
  informação; a validação da causa raiz continua sendo do operador.
- Deixar rastreável cada pergunta, resposta e evidência consultada.
- Validar, na prática (não só em teoria), que o motor do agente se adapta
  a outro setor produtivo trocando somente `config/` e `data/` — este
  projeto começou desenhado para agronegócio/grãos e foi re-configurado
  para bioprocessos sem tocar em `root_cause_agent/` (ver
  `docs/prompts.md`).

## 4. Público-alvo

- **Operadores de processo/qualidade** de manufatura de bioprocessos — o
  usuário direto, que conduz a investigação pelo navegador.
- **Analistas/engenheiros de qualidade** responsáveis por investigação de
  NC — consomem o relatório final (JSON/HTML) como evidência estruturada.

## 5. Proposta de solução

Uma plataforma web local (FastAPI + React, uma única tela) que:

1. Lista os lotes já classificados por risco pelo BiotecPredict, destacando
   os elegíveis para investigação (`WARNING`/`CRITICAL`) e os parâmetros de
   biosensor fora da faixa aceitável.
2. Conduz uma conversa estruturada em duas fases com o operador: 6
   perguntas de contexto (Ishikawa/6M), depois 5 perguntas "por quê"
   ancoradas na categoria mais provável identificada.
3. Consulta o histórico de leituras de biosensor do lote como evidência,
   via ferramenta, quando a pergunta em curso se beneficia de dado bruto.
4. Valida a resposta do operador em duas camadas (determinística +
   julgamento do LLM) para manter a qualidade da investigação sem travar o
   fluxo indefinidamente.
5. Sintetiza a cadeia completa numa causa raiz estruturada, gera o
   relatório (JSON + HTML) e apresenta ao operador para revisão — que pode
   pedir ajuste, reabrindo um novo ciclo com o anterior preservado para
   auditoria.

Ver `docs/diagrama-fluxo.md` para o fluxo completo (grafo LangGraph +
sequência de chamadas HTTP) e `docs/openapi.yaml` para o contrato da API.

## 6. Escopo

**Dentro do escopo desta entrega** (lista completa em `specs/product.md` §
Escopo desta entrega e `specs/requirements.md`):
- Leitura de lotes já classificados a partir de `data/biotecpredict.db`.
- Mapeamento Ishikawa (6 categorias fixas) + 5 Porquês, via interface web
  com human-in-the-loop.
- Ferramenta de consulta a biosensor, restrita ao lote e a uma janela de
  datas validada.
- Validação em duas camadas da resposta do operador.
- Revisão do operador com opção de pedido de ajuste (novo ciclo).
- Relatório final em JSON + HTML.
- Fallback de LLM em cadeia (Gemini → Groq → Anthropic → OpenAI).

**Fora do escopo nesta entrega:**
- Detecção automática da NC (já chega classificada como entrada).
- Segundo agente (RAG) para recomendação de plano PDCA e fluxo de Garantia
  da Qualidade — roadmap, ver § 12 abaixo.
- Múltiplos parâmetros fora da faixa tratados como NCs separadas.
- Adaptação simultânea a mais de um setor produtivo.
- Parada antecipada dos loops (sempre 6 + 5 perguntas, mesmo se a causa
  parecer óbvia antes).

## 7. Requisitos funcionais (resumo)

Lista completa e numerada (RF1–RF13) em `specs/requirements.md`. Os pontos
centrais:

| # | Requisito |
|---|---|
| RF1–RF3 | Validar a NC de entrada; carregar regras do setor; identificar deterministicamente os parâmetros fora da faixa antes de qualquer envolvimento do LLM |
| RF4–RF6 | Conduzir exatamente 6 perguntas Ishikawa, identificar a categoria principal, conduzir exatamente 5 Porquês ancorados nela |
| RF7–RF8 | Pausar em cada uma das 11 iterações (human-in-the-loop); manter a cadeia completa como memória do grafo |
| RF9–RF10 | Gerar o diagnóstico e os relatórios JSON/HTML ao final; permitir pedido de ajuste |
| RF11 | Permitir trocar o provedor/modelo de LLM por configuração |
| RF12 | Expor uma interface web que lista lotes e conduz a investigação inteiramente pelo navegador, com o histórico de parâmetros sempre visível |
| RF13 | Validar a resposta do operador em duas camadas (determinística + LLM, até 2 tentativas) |

## 8. Requisitos não-funcionais (resumo)

Lista completa (RNF1–RNF6) em `specs/requirements.md`. Resumo: segurança
(chaves nunca versionadas; ferramenta somente-leitura, restrita ao lote e
a uma janela de datas validada), adaptabilidade (nenhum limiar hardcoded
fora de `config/`), rastreabilidade (proveniência dos dados documentada),
simplicidade (sem camadas de abstração além do necessário) e resiliência
(fallback de LLM em cadeia, sem retry automático em loop).

## 9. Fluxo do usuário (alto nível)

```
Operador abre a aplicação
   → vê a lista de lotes já classificada por risco
   → escolhe um lote elegível (WARNING/CRITICAL)
   → responde 6 perguntas de contexto (Ishikawa)
   → responde 5 perguntas "por quê" (ancoradas na categoria identificada)
   → revisa a cadeia completa + causa raiz + link do relatório
   → aprova (fim) OU pede ajuste (reabre um novo ciclo)
```

Detalhamento nó a nó em `docs/diagrama-fluxo.md`; cenários passo a passo
(incluindo casos de erro/validação) em `docs/cenarios-de-uso.md`.

## 10. Critérios de sucesso / aceitação

Este projeto é entregue como Mini-Projeto Avaliativo do Módulo 2 (IA para
DEVs) — os critérios de sucesso são os de aceitação técnica, listados por
completo em `specs/requirements.md` § Critérios de aceitação. Resumo:

- Suíte de testes (pytest + Vitest + Playwright) verde, sem depender de um
  provedor de LLM real nem de `data/biotecpredict.db`.
- Com `data/biotecpredict.db` presente, a interface conduz uma
  investigação completa (11 perguntas + revisão) produzindo um
  `Diagnostico` válido em JSON e HTML.
- O fluxo de "pedir ajuste" reabre um novo ciclo e preserva o anterior.
- Nenhuma chave de API nem `data/biotecpredict.db` no histórico de commits.
- README, `docs/prompts.md` e `docs/apresentacao.md` cobrindo os pontos
  exigidos pelo rubric da disciplina.

Não há metas quantitativas de negócio (ex.: "reduzir tempo de investigação
em X%") nesta entrega — é um projeto acadêmico sem base de uso real para
medir contra; o roadmap (§ 12) é onde esse tipo de métrica passaria a
fazer sentido, com uso em produção.

## 11. Riscos e limitações conhecidas

- A classificação/detecção da NC não é feita por este agente — vem do
  BiotecPredict; o agente lê um arquivo de banco local (exportado/montado
  manualmente), não uma conexão ao vivo.
- Cobre um parâmetro (ou par correlacionado) fora da faixa por lote —
  múltiplos parâmetros de causas independentes exigiriam ciclos separados.
- Os loops sempre completam todas as perguntas, mesmo que a causa fique
  óbvia antes — decisão deliberada de previsibilidade, não uma limitação
  técnica.
- Depende de pelo menos um provedor de LLM configurado e acessível — sem
  nenhum configurado ou todos falhando, a investigação fica bloqueada
  (com o progresso preservado no checkpoint, não perdido).
- `data/biotecpredict.db` de demonstração é um dataset curado (ver
  `specs/design.md` § Estratégia de dados) — validado contra o motor real
  de classificação do BiotecPredict, mas não uma captura de uma instância
  de produção real.

## 12. Roadmap (fora desta entrega)

Ver `specs/design.md` § Roadmap para o desenho completo: um segundo agente
(RAG) consultando documentação da empresa/legislação/ANVISA/bibliografia
para recomendar um plano PDCA (ação corretiva + Kaizen), avaliado pela
Garantia da Qualidade em conjunto com a Coordenação da Produção, executado
e verificado quanto à eficácia por reincidência — fechando um ciclo PDCA
completo. É nesse estágio que métricas de negócio (tempo médio de
investigação, taxa de reincidência) passariam a ser aplicáveis.

## 13. Referências

- `specs/product.md` — visão de produto completa
- `specs/requirements.md` — RF/RNF completos, entrada/saída, critérios de aceitação
- `specs/design.md` — arquitetura, fluxo do grafo, estratégia de dados, roadmap
- `docs/diagrama-fluxo.md` — diagramas Mermaid (grafo + sequência HTTP)
- `docs/cenarios-de-uso.md` — cenários de uso passo a passo
- `docs/openapi.yaml` — contrato da API
- `docs/prompts.md` — histórico de decisões que moldaram este PRD
