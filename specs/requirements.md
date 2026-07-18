# Requisitos — Agente de Investigação de Causa Raiz de NC

## Objetivo

Automatizar a **facilitação de duas ferramentas clássicas de qualidade em
sequência** — diagrama de Ishikawa (6M) e método dos 5 Porquês — dentro do
tratamento de uma Não-Conformidade (NC) de processo produtivo, através de
uma pequena plataforma web: o operador abre a aplicação, vê a lista de
lotes já classificados por risco, escolhe um lote elegível e conduz a
investigação em conjunto com o agente pelo navegador.

Dado um lote já reprovado, com o(s) parâmetro(s) de processo que motivaram
a reprovação já identificados a partir dos dados, o agente primeiro conduz
uma conversa estruturada de 6 perguntas de contexto (uma por categoria do
Ishikawa — Método, Máquina, Material, Mão de obra, Meio ambiente, Medição)
com o operador, identifica a categoria mais provável, e só então aprofunda
com 5 perguntas "por quê" ancoradas nessa categoria — cada pergunta
partindo da resposta anterior — até chegar a uma causa raiz sistêmica. Ao
final, o operador revisa a cadeia completa e **aprova** (gera o relatório)
ou **pede ajuste** (reabre um novo ciclo completo, preservando o anterior
para auditoria). O relatório aprovado é produzido em **JSON** (para
consumo por outros sistemas) **e HTML** (para leitura humana).

**Por que Ishikawa antes de 5 Porquês:** 5 Porquês não tem mecanismo
próprio de priorização quando a causa pode estar em categorias muito
diferentes (método, máquina, material, mão de obra, meio ambiente,
medição) — pular direto pra "por que o pH está alto" arrisca ancorar a
investigação numa categoria errada. Mapear o contexto primeiro (Ishikawa) e
só depois aprofundar (5 Porquês) é a combinação recomendada pela literatura
de qualidade (ASQ, KaiNexus) pra esse cenário — ver `specs/design.md`.

Case de referência: **biotecnologia — bioprocessos / produção de
bioinsumos**, como **agente complementar ao
[BiotecPredict](https://github.com/micheleoliveiracod/Projeto-avaliativo-M1-2-BiotecPredict)**,
plataforma da mesma autora que avalia lotes de bioprocesso a partir de
dados de biosensores por dois caminhos independentes, ambos persistidos ou
derivados do mesmo banco SQLite (schema real, verificado no código-fonte —
tabelas `batches` e `sensor_readings`, ver `specs/design.md`): um
`compliance_score` (0–100, persistido) classificável em
ACCEPTABLE/WARNING/CRITICAL, e um `risk_prediction` de ML
(LOW_RISK/MEDIUM_RISK/HIGH_RISK, persistido). Lotes com `status='COMPLETED'`
e `compliance_score` classificado abaixo de ACCEPTABLE (risco médio ou
alto) são os **elegíveis** para investigação — a lista exibida ao operador
já vem classificada, e é dela que ele escolhe qual lote investigar. A
engine é desenhada para que outro setor produtivo adapte a solução trocando
`config/regras_*.yaml` e os arquivos em `data/`, sem alterar o código do
agente — este projeto, aliás, começou desenhado para agronegócio/grãos e
foi re-configurado para bioprocessos trocando só esses dois pontos,
validando esse requisito na prática.

## Contexto de avaliação

Este projeto é entregue como Mini-Projeto Avaliativo do Módulo 2 (IA para
DEVs), prazo 20/07/2026. Os requisitos abaixo incorporam os itens
obrigatórios do rubric da disciplina — ver `MEMORY.md` do projeto para o
texto completo do enunciado.

## Entrada

A base de entrada deste agente é um arquivo `data/biotecpredict.db` —
**uma exportação real do banco do BiotecPredict** (schema idêntico,
gerado por uma instância real daquela aplicação), colocado manualmente na
pasta `data/` e nunca versionado (ver `specs/design.md` § Estratégia de
dados para a justificativa). O agente lê a tabela `batches` e seleciona
linhas com `status='COMPLETED'` e `compliance_score` não nulo, classificado
como `WARNING` ou `CRITICAL` — usando a lógica real de
`ComplianceService._classify_score()` do BiotecPredict (`score>=80`
ACCEPTABLE, `score>=45` WARNING, `else` CRITICAL; replicada em
`config/regras_bioprocesso.yaml`, já que `classification` não é uma coluna
persistida, é computada pela API do BiotecPredict). Lotes com
`compliance_score` nulo (status `COMPLETED` mas ainda sem score, um estado
real observado na exportação disponível) são excluídos da lista de
elegíveis, não tratados como erro.

Um objeto `NaoConformidade` é construído a partir de uma dessas linhas,
contendo pelo menos:
- `batch_id` (inteiro, chave primária em `batches`)
- `compliance_score` (0–100, persistido) e a `classification` derivada (WARNING/CRITICAL)
- `risk_prediction` (`LOW_RISK`/`MEDIUM_RISK`/`HIGH_RISK`, persistido, sinal independente do modelo de ML — pode concordar ou não com a `classification`, o que já é um dado interessante pro agente considerar)
- `sensor_metrics` (média/min/max por parâmetro de biosensor, calculado a partir de `sensor_readings`, replicando `get_sensor_metrics()` do BiotecPredict)
- `parametros_fora_da_faixa` (lista dos parâmetros cuja métrica está fora da faixa aceitável de `config/regras_bioprocesso.yaml` — **identificado deterministicamente**, não pelo LLM)
- `upload_date` (quando o lote foi processado pelo BiotecPredict)

O agente **não** descobre qual parâmetro está fora da faixa — isso já vem
pronto em `parametros_fora_da_faixa`. O que o agente investiga, junto com o
operador, é **por que** aquele parâmetro saiu da faixa — primeiro mapeando
o contexto (Ishikawa), depois aprofundando (5 Porquês) — ver
`specs/design.md`.

## Saída

Um objeto `Diagnostico`, persistido em **dois formatos** — `reports/{batch_id}_{timestamp}.json`
(consumo por máquina/outros sistemas) e `reports/{batch_id}_{timestamp}.html`
(leitura humana, é o link exibido ao operador após a aprovação) — contendo:
- a NC original (eco, para rastreabilidade)
- `respostas_ishikawa`: as 6 perguntas/respostas de contexto, uma por categoria
- `categoria_principal`: a categoria identificada como mais provável, com justificativa
- `categorias_descartadas`: as demais categorias, cada uma com o motivo de descarte
- `cadeia_de_porques`: lista de exatamente 5 `PorQue` (número, pergunta formulada pelo agente, resposta do operador, tentativas dadas e se a resposta final foi considerada informativa, evidência da ferramenta quando consultada), na ordem em que aconteceram — ancorada em `categoria_principal`
- `causa_raiz`: a síntese da causa raiz sistêmica, feita pelo agente a partir da cadeia completa
- uma narrativa curta explicando o raciocínio
- `ciclos_anteriores`: ciclos de investigação anteriores para o mesmo lote, caso o operador tenha pedido ajuste — preservados para auditoria, nunca sobrescritos
- timestamp de geração

## Requisitos funcionais (RF)

- **RF1** — O sistema deve validar a `NaoConformidade` de entrada antes de iniciar a investigação (schema Pydantic), rejeitando entradas malformadas com erro claro.
- **RF2** — O sistema deve carregar as regras/limiares do setor produtivo (ex: `config/regras_bioprocesso.yaml`), incluindo as 6 categorias do Ishikawa, e disponibilizá-las como contexto para a investigação.
- **RF3** — O sistema deve identificar deterministicamente, em `preparar_contexto`, quais parâmetros de biosensor do lote estão fora da faixa aceitável, antes de qualquer envolvimento do LLM.
- **RF4** — O agente deve conduzir exatamente 6 iterações de mapeamento Ishikawa (uma por categoria, sempre na mesma ordem), formulando uma pergunta de contexto por categoria (não sobre o parâmetro fora da faixa diretamente), podendo consultar a ferramenta de biosensor (no máximo 1 vez por categoria) quando precisar de mais contexto.
- **RF5** — Após as 6 respostas do Ishikawa, o sistema deve identificar deterministicamente-com-apoio-de-LLM a `categoria_principal` (a mais provável) e registrar as `categorias_descartadas` com o motivo, verificando inconsistências entre as respostas.
- **RF6** — O agente deve conduzir exatamente 5 iterações do método dos 5 Porquês, ancoradas na `categoria_principal`: a cada iteração, formular uma pergunta "por quê" (a 1ª a partir da categoria identificada, as demais a partir da resposta do operador na iteração anterior), podendo consultar a ferramenta de biosensor (no máximo 1 vez por iteração) quando precisar de mais evidência.
- **RF7** — O sistema deve pausar a execução em cada uma das 11 iterações (6 Ishikawa + 5 porquês) para capturar a resposta do operador (human-in-the-loop) via interface web, antes de seguir para a próxima pergunta.
- **RF8** — O sistema deve manter a cadeia completa de perguntas e respostas (Ishikawa e 5 Porquês) como memória/contexto durante toda a execução (estado do grafo).
- **RF9** — Ao final das 11 iterações, o sistema deve apresentar ao operador a cadeia completa para revisão, com duas ações possíveis: **aprovar** (gera o `Diagnostico` final e os relatórios JSON/HTML) ou **pedir ajuste** (arquiva o ciclo atual em `ciclos_anteriores` e reinicia um novo ciclo completo para o mesmo lote).
- **RF10** — O sistema deve produzir, na aprovação, uma saída estruturada (`Diagnostico`) em JSON e em HTML, validada contra um schema antes de ser salva.
- **RF11** — O sistema deve permitir trocar o provedor/modelo de LLM usado por configuração (variável de ambiente), sem alterar código.
- **RF12** — O sistema deve expor uma interface web local (backend FastAPI + frontend React/TypeScript) que, ao ser iniciada, lista os lotes de `data/biotecpredict.db` com sua classificação, destacando os elegíveis (risco médio/alto), e permite ao operador escolher um lote e conduzir a investigação inteiramente pelo navegador.
- **RF13** — O sistema deve validar a resposta do operador em duas camadas antes de aceitá-la: (a) rejeitar deterministicamente respostas vazias/só espaço ou uma lista fixa de frases evasivas conhecidas ("não sei" etc.), sinalizando "Este tipo de resposta não é aceito" na tela, sem avançar a investigação e sem contar como tentativa; (b) julgar via LLM se uma resposta que passou pela camada anterior é informativa para a pergunta feita, dando ao operador no máximo 2 tentativas por pergunta — se a 2ª também não for informativa, a investigação segue para a próxima pergunta, registrando as duas tentativas e sinalizando a não-informatividade.

## Requisitos não-funcionais (RNF)

- **RNF1 (Segurança)** — Nenhuma chave de API deve ser hardcoded ou versionada; leitura exclusiva via variável de ambiente/`.env` (gitignored).
- **RNF2 (Segurança)** — A ferramenta de consulta a dados deve ser somente-leitura (consulta SQL `SELECT`, nunca `INSERT`/`UPDATE`/`DELETE`) e restrita ao banco SQLite local, ao `batch_id` do lote sob investigação (injetado a partir do estado via `InjectedState`, não escolhido pelo LLM a cada chamada) e a uma janela de datas validada (formato ISO parseável, `data_inicio <= data_fim`; formato inválido devolve uma mensagem de erro clara para o LLM, não um resultado vazio silencioso) — sem acesso arbitrário a arquivos ou rede.
- **RNF3 (Adaptabilidade)** — Nenhum limiar, nome de setor, ou parâmetro específico de produto deve estar hardcoded na lógica do grafo/nós — deve vir de `config/`.
- **RNF4 (Rastreabilidade)** — `data/biotecpredict.db` é uma exportação real de uma instância do BiotecPredict (não um dataset sintético) e não é versionada — o repositório documenta como obtê-la (ver `specs/design.md`); uma fixture sintética equivalente (`tests/fixtures/biotecpredict_teste.db`), estática e versionada, existe apenas para os testes automatizados, claramente rotulada como tal, e nunca é usada pela aplicação em execução.
- **RNF5 (Simplicidade)** — A implementação deve ser a mais simples que ainda satisfaça RF1–RF12 — sem camadas de abstração além do necessário para separar: schemas, estado, configuração, ferramentas, nós, grafo, geração de relatórios e API. Em particular: "orquestração" e "geração de relatório" são nós do mesmo `StateGraph`, não agentes/grafos separados — ver `specs/design.md` § Decisão de simplicidade. O frontend React não usa router nem biblioteca de gerência de estado — uma única tela com estado local basta.
- **RNF6 (Resiliência)** — O LLM deve ter fallback em cadeia — Gemini (oficial, gratuito, usado em testes/prototipagem) → Anthropic → OpenAI, cada camada ativada apenas se a respectiva chave de API estiver configurada — antes de qualquer chamada ser considerada uma falha. Só quando todos os provedores configurados falharem (rede, rate limit, chave inválida/ausente) é que o nó agêntico captura a falha e relança `FalhaLLMError`; a API traduz isso numa resposta HTTP 503 com a mensagem "Serviço de IA indisponível, recarregue a página." (sem retry automático em loop); o checkpoint da investigação (`thread_id`) permanece pausado no último ponto bem-sucedido, permitindo repetir a ação mais tarde sem perder progresso nem repetir perguntas já respondidas.

## Fora de escopo (nesta entrega)

- Detecção automática da NC (a NC já chega detectada/classificada como entrada).
- Persistência da *saída* em banco de dados — o `Diagnostico` é salvo como arquivos (JSON+HTML) em `reports/`; só a *entrada* (lotes/leituras do BiotecPredict) vem de SQLite.
- Múltiplos parâmetros fora da faixa simultaneamente no mesmo lote — o mapeamento Ishikawa endereça a *causa* poder estar em categorias diferentes, não *múltiplos parâmetros fora da faixa ao mesmo tempo* (esse caso mais amplo fica para um próximo ciclo/NC separada).
- Parada antecipada do mapeamento Ishikawa ou do loop de 5 Porquês — sempre as 6 + 5 perguntas são feitas, mesmo que a resposta pareça óbvia antes (decisão de previsibilidade).
- Arquitetura multiagente de verdade (grafos/agentes separados coordenando entre si) — "orquestrador" e "relatório" são nós do mesmo grafo nesta entrega, ver `specs/design.md` § Decisão de simplicidade.
- Integração ao vivo (API) com uma instância do BiotecPredict em execução — o agente lê um arquivo `.db` local, que é uma cópia/exportação, não uma conexão de rede.
- Uso da tabela `predictions` do BiotecPredict (presente no schema, mas vazia na exportação disponível) — não consultada por este agente.
- **Segundo agente (RAG)** para o setor da Qualidade — consulta documentação da empresa, legislação aplicável, normas ANVISA e referências bibliográficas para recomendar o tratamento da NC como um plano PDCA (ação corretiva + Kaizen), com o relatório final indo para a Garantia da Qualidade (não para o operador). Fase 2 do roadmap, exige infraestrutura própria (ingestão de documentos, embeddings, vector store) fora do escopo desta entrega.
- **Execução e verificação de eficácia do plano PDCA** pela Garantia da Qualidade (Do + Check, incluindo o acompanhamento de reincidência do problema ao longo do tempo) — depende do item anterior, mesmo status de roadmap.
- Um segundo perfil de setor além de bioprocessos (fica documentado como próximo passo, não implementado).

## Critérios de aceitação

- [ ] `pytest` passa com os testes de `tests/` (usando a fixture sintética, sem depender de `data/biotecpredict.db`).
- [ ] `npm run test` (Vitest) passa nos componentes de `frontend/`, e `npx playwright test` (`e2e/`) passa o fluxo completo (incluindo o caso de "pedir ajuste") local e no GitHub Actions — ambos sem depender de um provedor de LLM real (`LLM_PROVIDER=fake`) nem de `data/biotecpredict.db`.
- [ ] A cadeia de fallback de LLM (RNF6) tem cobertura automatizada (`tests/test_config.py`) simulando cada provedor falhando, sem chamada real.
- [ ] Com `data/biotecpredict.db` presente, a interface web lista os lotes elegíveis corretamente e conduz uma investigação completa (11 perguntas + revisão + aprovação) produzindo `Diagnostico` válido em JSON e HTML.
- [ ] O fluxo de "pedir ajuste" reabre um novo ciclo e preserva o ciclo anterior em `ciclos_anteriores`.
- [ ] Nenhuma chave de API, nem `data/biotecpredict.db`, aparece no histórico de commits.
- [ ] README.md contém todas as seções exigidas pelo rubric (ver `specs/design.md`).
- [ ] `docs/prompts.md` registra os prompts principais usados no desenvolvimento.
- [ ] `slides/apresentacao.md` cobre os 6 pontos exigidos pelo rubric.
