# Design — Agente de Investigação de Causa Raiz de NC

Ver `specs/requirements.md` para o que está sendo construído e por quê. Este
documento descreve **como**.

## Método: Ishikawa primeiro, depois 5 Porquês, com o operador (human-in-the-loop)

**Correção metodológica importante (2026-07-15):** a primeira versão deste
design pulava direto de "qual parâmetro está fora da faixa" pra "por que
esse parâmetro está fora da faixa". Isso contraria a prática estabelecida
de qualidade: 5 Porquês funciona bem pra um problema já bem delimitado, mas
**não tem mecanismo próprio de priorização/contextualização quando a causa
pode estar em categorias muito diferentes** (método, máquina, material, mão
de obra, meio ambiente, medição). A literatura (ASQ, KaiNexus, ITONICS) e
práticas recentes de agentes de IA pra RCA (ver referência acadêmica
abaixo) recomendam **mapear o cenário com um diagrama de Ishikawa (6M)
antes** de aprofundar com 5 Porquês numa categoria específica.

O núcleo do agente agora tem duas fases, ambas em conversa com o operador:

**Fase 1 — Mapeamento Ishikawa.** O agente pergunta, uma categoria de cada
vez (sempre as 6, nesta ordem: Método, Máquina, Material, Mão de obra, Meio
ambiente, Medição), sobre o contexto daquele cultivo específico — não sobre
o parâmetro fora da faixa diretamente. Ex: "Houve alguma mudança de
procedimento neste lote?" (Método), "O agitador recebeu manutenção
preventiva no prazo?" (Máquina). Cada resposta do operador vai pra
`respostas_ishikawa`.

**Orquestração.** Com as 6 respostas em mãos, um nó analisa o conjunto:
identifica a categoria mais provável (`categoria_principal`) — a que
melhor explica o parâmetro fora da faixa — e registra as demais como
`categorias_descartadas` (com o motivo), verificando inconsistências entre
respostas. Isso corresponde ao papel de "Agente Orquestrador" descrito na
literatura de RCA multiagente, aqui implementado como mais um nó do mesmo
grafo (ver decisão de simplicidade abaixo).

**Fase 2 — 5 Porquês, ancorado na categoria identificada.** Só agora o
agente aprofunda: a 1ª pergunta "por quê" parte da `categoria_principal`
(ex: se Máquina foi identificada por falta de manutenção, a pergunta é
"por que o agitador não recebeu manutenção preventiva?", não "por que o pH
está alto?"). Daqui em diante o mecanismo é o mesmo já desenhado
anteriormente: sempre exatamente 5 iterações, no máximo 1 consulta à
ferramenta por iteração, resposta do operador molda a próxima pergunta.

**Relatório final**, gerado pelo mesmo nó final, mas agora estruturado
pelas categorias do Ishikawa (categoria principal + cadeia de 5 porquês +
categorias descartadas com motivo) — corresponde ao papel de "Agente de
Relatório" da literatura, também implementado como nó, não um agente à
parte.

**Referência:** esse desenho foi informado por uma revisão de literatura de
qualidade (ASQ, KaiNexus, ITONICS — 5 Porquês não prioriza entre causas
múltiplas, recomenda-se Ishikawa/Fishbone primeiro) e por um artigo
acadêmico com arquitetura próxima (framework multiagente para RCA
colaborativo assistido por IA em garantia de qualidade, com um agente
orquestrador + agente de relatório usando categorias de Ishikawa,
demonstrado num estudo de caso de ruptura de mangueira hidráulica). Aqui
adaptamos a *metodologia* (Ishikawa → 5 Porquês → relatório por categoria)
sem adotar a arquitetura *multiagente* do artigo — decisão explícita de
simplicidade, ver abaixo.

**Referência bibliográfica completa:**
Bocanet, V.I., Muntean, M.H., Fleseriu, C. (2026). *Multi-agent Framework
for AI-Supported Collaborative Root Cause Analysis in Quality Assurance*.
In: Advances in Production Management Systems. Cyber-Physical-Human
Production Systems: Human-AI Collaboration and Beyond (APMS 2025). IFIP
Advances in Information and Communication Technology, vol. 766. Springer,
Cham. [https://doi.org/10.1007/978-3-032-03538-7_15](https://link.springer.com/chapter/10.1007/978-3-032-03538-7_15)

## Por que isso é um agente (e não só um workflow)

A maior parte do processo é determinística: identificar o(s) parâmetro(s)
fora da faixa, controlar a contagem dos dois loops (6 categorias fixas,
depois 5 porquês fixos), rotear pra ferramenta ou pro operador, gravar cada
resposta, formatar e salvar o relatório final — isso é **workflow**, código
fixo, sem ambiguidade quanto a *como* essas coisas acontecem. Mas o
*conteúdo* de cada pergunta (tanto as 6 do Ishikawa quanto as 5 do
"por quê"), a análise que identifica a categoria mais provável, e a síntese
final — tudo isso depende inteiramente do que a NC revela e do que o
operador acabou de responder; não dá pra pré-programar. Essa formulação e
essa análise são delegadas a um LLM que decide autonomamente o conteúdo a
cada volta. É esse núcleo de decisão sobre conteúdo (não o sistema inteiro,
nem a mecânica dos loops) que torna a solução um agente, no sentido usado
pela disciplina.

## Decisão de simplicidade: nós no mesmo grafo, não agentes separados

A literatura de referência usa uma arquitetura multiagente de verdade
(Orquestrador + agentes especializados + Agente de Relatório, coordenando
via mensagens entre grafos independentes). Dado o prazo desta entrega,
decidimos deliberadamente **não** replicar isso: "orquestrar" e "gerar
relatório por categoria" viram nós dentro do **mesmo** `StateGraph` que já
temos, não grafos/agentes separados precisando de coordenação própria. O
valor metodológico (Ishikawa → priorização → 5 Porquês → relatório
rastreável por categoria) é preservado; a complexidade de coordenação
entre agentes autônomos, não. Se o tempo permitir mais adiante, migrar
esses nós para agentes de verdade é um refactor localizado, não uma
reescrita.

## Interface: plataforma web (FastAPI + React), não CLI

O operador interage com o agente por uma pequena aplicação web local, no
mesmo padrão de stack do BiotecPredict (FastAPI no backend, React +
TypeScript no frontend). Ao iniciar, a aplicação já lista os lotes de
`data/biotecpredict.db` com sua classificação, destacando os elegíveis
(risco médio/alto) — é dessa lista que o operador escolhe qual lote
investigar.

**Por que não dá pra usar `input()` bloqueante:** um processo de servidor
web não pode travar esperando o navegador — precisa continuar disponível
para outras requisições enquanto aguarda a resposta do operador. A solução
é o mecanismo de **interrupção/retomada nativo do LangGraph**:

- `perguntar_operador` chama `interrupt({"pergunta": ..., "nc": ..., "fase": ...,
  "indice": ..., "total": ..., "categoria": ...})` em vez de `input()`, pausando
  a execução do grafo e devolvendo o controle pra API -- `indice`/`total`
  situam o operador na cadeia (ex.: "3 de 6"), `categoria` só é enviada na
  fase Ishikawa (Método, Máquina, Material, Mão de obra, Meio ambiente,
  Medição), e `nc` (a `NaoConformidade` inteira, com `sensor_metrics` por
  parâmetro) é reenviada em toda pergunta pra o operador não precisar
  memorizar qual parâmetro está fora da faixa nem voltar pra lista de lotes
  pra conferir os dados.
- O grafo é compilado com um **checkpointer** (`SqliteSaver`, gravando em
  `data/checkpoints.db`), que persiste o estado da investigação por
  `thread_id` (um id de sessão associado ao lote escolhido).
- A API retoma a execução com
  `graph.invoke(Command(resume=resposta_operador), config={"configurable": {"thread_id": ...}})`.

Isso troca "uma execução síncrona de ponta a ponta" por uma série de
invocações curtas do grafo, uma por resposta — exatamente o padrão que uma
API request/response precisa.

O frontend é deliberadamente minimalista: uma única tela (sem router, sem
biblioteca de gerência de estado), com uma máquina de estados simples —
lista de lotes → pergunta atual → revisão (já com o link do relatório).

**A API vive num pacote próprio, `backend/`, separado de `root_cause_agent/`**
(não dentro dele) — mesma separação backend/frontend do BiotecPredict.
`root_cause_agent/` é o motor do agente, sem nenhuma dependência de FastAPI,
importável e executável sozinho (via `main.py`, o harness de teste);
`backend/` importa `root_cause_agent` como biblioteca e expõe o grafo por
HTTP. Essa fronteira é o que sustenta a adaptabilidade a outros setores (ver
`specs/product.md`): quem quiser reusar só o motor do agente não precisa
arrastar FastAPI junto.

**Contrato da API (`backend/main.py`):**

| Rota | Efeito |
|---|---|
| `GET /api/lotes` | Lista os lotes de `data/biotecpredict.db` com classificação calculada, destaque dos elegíveis e, para estes, os parâmetros de biosensor fora da faixa aceitável |
| `POST /api/investigacoes/{batch_id}/iniciar` | Cria/retoma um `thread_id`, roda o grafo até o 1º `interrupt`, devolve a 1ª pergunta |
| `POST /api/investigacoes/{thread_id}/responder` | `Command(resume=resposta)`, devolve a próxima pergunta ou sinaliza "pronto pra revisão"; ao concluir o ciclo (resposta ao 5º porquê), já gera `reports/{batch_id}_{ts}.json` + `.html` (via `root_cause_agent.reports`) |
| `GET /api/investigacoes/{thread_id}/revisao` | Devolve toda a cadeia (Ishikawa + 5 Porquês) + rascunho de `causa_raiz` + os links do relatório já gerado |
| `POST /api/investigacoes/{thread_id}/ajustar` | Arquiva o ciclo atual em `ciclos_anteriores`, reinicia um novo ciclo completo pro mesmo `batch_id` |
| `GET /reports/{arquivo}` | Serve os relatórios estáticos (JSON e HTML) |

Só as duas rotas que efetivamente executam nós do grafo (`iniciar` e
`responder`) podem levantar `FalhaLLMError` — ver seção abaixo.

## Validação da resposta do operador (duas camadas)

**Decisão (2026-07-15):** `perguntar_operador` não grava a resposta do
operador diretamente — ela passa por duas camadas separadas antes de virar
um `RespostaIshikawa`/`PorQue` definitivo, seguindo a mesma separação
workflow/agente do resto do desenho (ver "Por que isso é um agente" acima).

**Camada 1 — rejeição determinística (dentro de `perguntar_operador`,
tentativas ilimitadas).** Antes de qualquer coisa, `tools.py::validar_resposta_operador`
(uma função Python simples, **não** uma `@tool` vinculada ao LLM — checar
vazio/espaço ou uma lista fixa de frases evasivas conhecidas não exige
julgamento de modelo, então não há razão para pagar uma chamada de LLM por
isso) rejeita: resposta vazia/só espaço, ou uma correspondência exata
(normalizada) com frases evasivas conhecidas ("não sei", "sei lá", "não
lembro", "n/a", etc. — não inclui "sim"/"não" isolados, que podem ser
respostas curtas mas legítimas a uma pergunta binária). Se rejeitada,
`perguntar_operador` chama `interrupt(...)` de novo com o sinal "Este tipo
de resposta não é aceito", sem avançar o grafo e **sem contar como uma das
2 chances** — não é uma resposta real, é a mesma validação de "campo
obrigatório" de qualquer formulário.

**Camada 2 — julgamento de informatividade (nó novo: `avaliar_informatividade`,
agêntico, no máximo 2 tentativas).** Uma resposta que passa a Camada 1 ainda
pode não informar de verdade a pergunta feita (fugir do assunto, ser vaga
ou contraditória mesmo sem ser um "não sei" literal) — isso exige o LLM ler
pergunta + resposta e julgar, não é um formato fixo detectável por regra.
`avaliar_informatividade`:
- **informativa** → segue normalmente: grava a resposta final em
  `respostas_ishikawa[categoria_atual]`/`cadeia_porques` (com todas as
  tentativas em `tentativas` e `informativa=True`), limpa
  `tentativas_pergunta_atual`, avança para a próxima categoria/porquê.
- **não informativa, 1ª tentativa** → sinaliza ao operador na tela e volta
  para `perguntar_operador` pedindo a **mesma pergunta de novo** — 2ª e
  última chance.
- **não informativa, 2ª tentativa** → desiste de insistir: grava as 2
  tentativas com `informativa=False` e **segue mesmo assim** para a
  próxima categoria/porquê, sem uma 3ª chance.

**Onde fica registrado:** `RespostaIshikawa` e `PorQue` (`models.py`)
ganham `tentativas: list[str]` (todas as respostas que passaram na Camada
1, na ordem — 1 item no caso normal, 2 quando a 1ª foi não informativa) e
`informativa: bool` (default `True`, só vira `False` quando as 2 tentativas
falharam a Camada 2); `resposta` continua guardando a última tentativa
aceita, pra não quebrar código que só lê esse campo. `AgentState`
(`state.py`) ganha `tentativas_pergunta_atual: list[str]`, resetado sempre
que uma nova pergunta é formulada. Essa validação é reusada nas duas fases
(Ishikawa e 5 Porquês), assim como o próprio `perguntar_operador`.

## Tratamento de falha na chamada ao LLM

**Decisão (2026-07-15, cadeia estendida em 2026-07-18):** antes de qualquer
coisa chegar a virar um erro pro operador, `config.py::get_llm()` já tenta
um **fallback em cadeia**: Gemini (`LLM_PROVIDER`/`LLM_MODEL` — o provedor
oficial deste projeto, gratuito, usado em testes e prototipagem) → Groq
(hospeda modelos open-source como Llama num chip próprio de inferência
rápida — 2º provedor gratuito, usado nos mesmos testes) →
Anthropic → OpenAI, nessa ordem, via `ChatModel.with_fallbacks(...)`. Cada
fallback só entra na cadeia se sua respectiva chave
(`GROQ_API_KEY`/`ANTHROPIC_API_KEY`/`OPENAI_API_KEY`) estiver configurada no
`.env` — rodar só com a chave do Gemini (o cenário mínimo de
testes/prototipagem) continua funcionando sem exigir as outras três;
configurar `GROQ_API_KEY` (pra testar o agente com um 2º LLM de verdade,
também gratuito) e/ou as chaves pagas extras (ex: para uma demonstração)
ativa a resiliência automaticamente, sem mudar nenhum código de nó/grafo.

Só quando **todos os provedores configurados** falham (rede, rate limit, ou
chave inválida/ausente em cada um deles) é que a exceção chega ao nó. Todo
nó agêntico (`formular_pergunta_ishikawa`, `orquestrar_analise`,
`formular_porque`, `avaliar_informatividade`, `gerar_causa_raiz`) envolve
sua chamada ao LLM (`config.py::get_llm()`) num `try/except`, capturando
essa falha. Ao capturar, o nó relança uma exceção própria do projeto,
`FalhaLLMError` (definida em `nodes.py`), a partir da exceção original
(`raise FalhaLLMError(...) from exc`) — assim `backend/main.py` só precisa
tratar um tipo de exceção, independente de qual nó falhou, de qual provedor
principal está configurado via `LLM_PROVIDER`, ou de quantos fallbacks
estavam ativos.

**Na API:** as rotas que efetivamente executam nós do grafo (`POST
/api/investigacoes/{batch_id}/iniciar` e `POST
/api/investigacoes/{thread_id}/responder`) capturam `FalhaLLMError` e
respondem com HTTP 503 e a mensagem "Serviço de IA indisponível, recarregue
a página." — sem deixar a exceção crua vazar pro frontend.

**Por que o checkpoint fica pronto pra tentar de novo, sem trabalho extra:**
o `SqliteSaver` só persiste um novo checkpoint depois que um nó termina com
sucesso. Se um nó agêntico levanta `FalhaLLMError` no meio da execução, a
exceção sobe através de `graph.invoke(...)` antes de qualquer checkpoint
novo ser gravado — o `thread_id` continua exatamente no ponto do último
checkpoint bem-sucedido (o `interrupt()` que originou aquela chamada). Não
é preciso nenhuma lógica extra de "salvar progresso" ou "marcar pra
retry": o operador recarrega a página, refaz a mesma ação (reenviar a
resposta daquela pergunta), e o LangGraph resume a execução do mesmo ponto,
sem repetir perguntas já respondidas nem perder nada do estado.

**Sem retry automático em loop:** se mesmo com o fallback (Gemini → Groq →
Anthropic → OpenAI) nenhum provedor configurado responder, a mensagem "Serviço
de IA indisponível, recarregue a página." permanece na tela — não há
nova tentativa automática em intervalo. O operador precisa aguardar os
provedores voltarem e só então recarregar/reenviar; dado que o checkpoint
já fica pausado no ponto certo (parágrafo acima), esperar não arrisca
perder nada da investigação em andamento.

## Arquitetura de módulos

```
root_cause_agent/
├── models.py    # Pydantic: NaoConformidade, RespostaIshikawa, PorQue, Diagnostico (+ CicloAnterior)
├── state.py     # AgentState: nc_input, regras_setor, messages, respostas_ishikawa, categoria_atual,
│                #             categoria_principal, categorias_descartadas, cadeia_porques, numero_porque,
│                #             pergunta_atual, ciclos_anteriores, diagnostico
├── config.py    # .env, seleção de LLM (init_chat_model), carga do YAML de regras, caminhos dos .db
├── tools.py     # @tool consultar_leituras_biosensor(batch_id, data_inicio, data_fim) -- SELECT em sensor_readings
├── nodes.py     # preparar_contexto, formular_pergunta_ishikawa, orquestrar_analise,
│                #  formular_porque, perguntar_operador (usa interrupt(), Camada 1 de
│                #  validação), avaliar_informatividade (Camada 2), gerar_causa_raiz
├── graph.py     # monta e compila o StateGraph com checkpointer (SqliteSaver)
├── reports.py   # Diagnostico -> reports/{batch_id}_{timestamp}.json + .html (Jinja2)
└── main.py      # harness de teste: roda o grafo com respostas fornecidas em código, sem servidor

backend/         # FastAPI -- depende de root_cause_agent, nunca o contrário
└── main.py      # rotas de lotes/investigação/ajuste, serve reports/ como estático

frontend/        # React + TypeScript + Vite -- única tela, sem router/lib de estado
```

Cada módulo tem uma responsabilidade só — isso é a "separação entre
planejamento, execução, uso de ferramentas e geração da resposta" pedida pelo
rubric, sem precisar de camadas de Clean Architecture completas (fora de
escopo, ver `specs/requirements.md` RNF5).

## Fluxo do grafo (LangGraph)

```
Entrada (batch_id escolhido pelo operador na lista da interface web)
   ↓
preparar_contexto        [determinístico: SELECT em batches (status='COMPLETED'), calcula sensor_metrics,
                           identifica parametros_fora_da_faixa comparando contra config/regras_bioprocesso.yaml,
                           monta a NaoConformidade, inicializa respostas_ishikawa={}, cadeia_porques=[], numero_porque=1]
   ↓
┌─── FASE 1: MAPEAMENTO ISHIKAWA (6 categorias, sempre nesta ordem) ──────────┐
│  formular_pergunta_ishikawa  ←──────────────────────────────┐              │
│     │  [nó LLM: formula a pergunta de contexto da           │              │
│     │   categoria atual (Método/Máquina/Material/           │              │
│     │   Mão de obra/Meio ambiente/Medição); pode             │              │
│     │   chamar a tool se ajudar a contextualizar]           │              │
│     ↓ (tools_condition)                                      │              │
│     ├── usar_ferramenta → volta                              │              │
│     └── pergunta pronta → perguntar_operador                 │              │
│            [interrupt(); Camada 1 (validar_resposta_operador):            │
│             vazia/evasiva conhecida → interrupt() de novo, não conta      │
│             como tentativa; passou → avaliar_informatividade]            │
│            ↓                                                              │
│         avaliar_informatividade  [nó LLM: Camada 2]                       │
│            ├── não informativa, 1ª tentativa → volta pro                  │
│            │    perguntar_operador (2ª e última chance)                   │
│            └── informativa OU 2ª tentativa esgotada →                     │
│                 registra em respostas_ishikawa[categoria]                 │
│            ↓ (ainda falta categoria?)                         │              │
│            ├── sim ────────────────────────────────────────┘              │
│            └── não (6/6 respondidas) ──────────────────────────────────┐  │
└──────────────────────────────────────────────────────────────────────  │  │
                                                                          ↓  │
orquestrar_analise   [nó LLM: analisa as 6 respostas, identifica                │
                       categoria_principal, registra categorias_descartadas    │
                       com motivo, verifica inconsistências]                  │
   ↓                                                                          │
┌─── FASE 2: 5 PORQUÊS (ancorado na categoria_principal) ─────────────────────┐
│  formular_porque  ←──────────────────────────────────────────┐             │
│     │  [nó LLM: 1ª pergunta parte de categoria_principal;    │             │
│     │   2ª-5ª partem da resposta anterior; pode usar a tool]  │             │
│     ↓ (tools_condition)                                       │             │
│     ├── usar_ferramenta → volta                               │             │
│     └── pergunta pronta → perguntar_operador                  │             │
│            [interrupt(); mesma Camada 1 de validação da Fase 1]           │
│            ↓                                                              │
│         avaliar_informatividade  [Camada 2, mesmo nó da Fase 1]           │
│            ├── não informativa, 1ª tentativa → volta pro                  │
│            │    perguntar_operador (2ª e última chance)                   │
│            └── informativa OU 2ª tentativa esgotada →                     │
│                 registra {pergunta, resposta, tentativas, informativa}    │
│                 em cadeia_porques, numero_porque += 1                     │
│            ↓ (numero_porque <= 5 ?)                            │             │
│            ├── sim ─────────────────────────────────────────┘             │
│            └── não → gerar_causa_raiz                                      │
└─────────────────────────────────────────────────────────────────────────────┘
   ↓
gerar_causa_raiz  [nó LLM: sintetiza categoria_principal + cadeia_porques + categorias_descartadas
                    em Diagnostico estruturado por categoria; valida contra o schema]
   ↓
[API: salva reports/{batch_id}_{ts}.json + .html; apresenta a cadeia
 completa ao operador para revisão, já com os links do relatório]
   ↓ (operador decide)
   ├── nada a fazer → relatório já está salvo e disponível
   └── pedir ajuste → arquiva o ciclo atual (já reportado) em
                        ciclos_anteriores; reinicia um novo ciclo completo
                        a partir de preparar_contexto
```

`AgentState.messages` (reducer `add_messages`) é a memória do sub-loop de
tool-calling dentro de uma única pergunta (Ishikawa ou "por quê").
`respostas_ishikawa` e `cadeia_porques` são a memória principal do
agente — o histórico completo das duas fases da conversa com o operador,
que `gerar_causa_raiz` usa pra sintetizar o relatório. `nc_input` e
`regras_setor` são o contexto carregado uma vez em `preparar_contexto` e
mantido no estado durante toda a execução. `perguntar_operador` é reusado
nas duas fases — sua responsabilidade (mostrar pergunta, capturar resposta,
gravar no lugar certo do estado, avançar o contador certo) não muda, só o
destino da resposta depende de em qual fase o grafo está.

## Estratégia de dados

Este agente é o complemento "causa raiz" do
[BiotecPredict](https://github.com/micheleoliveiracod/Projeto-avaliativo-M1-2-BiotecPredict),
que avalia lotes de bioprocesso a partir de biosensores por **dois sinais
independentes**, confirmados lendo o código-fonte real (não só o README,
que descreve os dois sinais mas sem deixar claro que são campos
diferentes):

- **`compliance_score`** (0–100) → classificado em `ACCEPTABLE`/`WARNING`/`CRITICAL`
  por `ComplianceService._classify_score()`
  (`backend/services/compliance_service.py`, linhas ~84-90 — o código que
  roda de fato: `score>=80` ACCEPTABLE, `score>=45` WARNING, `else`
  CRITICAL). Exposto pelo endpoint `GET /api/v1/compliance/{batch_id}`.
  A classificação **não é uma coluna do banco** — só `compliance_score` é
  persistido; `classification` é calculada a cada chamada da API. Achado
  extra: o próprio BiotecPredict tem uma inconsistência real entre duas
  docstrings do mesmo arquivo (uma diz "WARNING (60-79)", a outra e o
  código dizem `>=45`) — usamos o threshold do código que roda (45), não o
  da docstring desatualizada.
- **`risk_prediction`** (`LOW_RISK`/`MEDIUM_RISK`/`HIGH_RISK`) → saída
  categórica direta do modelo de ML (`backend/ml/model.py`,
  `backend/services/ml_service.py`), **persistida** como coluna de
  `batches`, sem relação de threshold com `compliance_score` — é um sinal
  independente que pode até discordar da classificação por score.

### Schema (idêntico ao BiotecPredict, confirmado em `data/biotecpredict.db`)

```sql
CREATE TABLE batches (
  id               INTEGER PRIMARY KEY,
  upload_date      DATETIME,    -- NOT NULL
  status           VARCHAR(50), -- NOT NULL; toda a exportação disponível está 'COMPLETED'
  compliance_score FLOAT,       -- 0-100, pode ser NULL mesmo com status='COMPLETED' (ver abaixo)
  risk_prediction  VARCHAR(50)  -- LOW_RISK | MEDIUM_RISK | HIGH_RISK, NULL junto com compliance_score
);

CREATE TABLE sensor_readings (
  id                INTEGER PRIMARY KEY,
  batch_id          INTEGER,     -- NOT NULL, referencia batches.id
  temperature       FLOAT,       -- °C, NOT NULL
  ph                FLOAT,       -- NOT NULL
  dissolved_oxygen  FLOAT,       -- %, NOT NULL
  pressure          FLOAT,       -- bar, NOT NULL
  agitator_speed    FLOAT,       -- RPM, NOT NULL
  recorded_at       DATETIME     -- NOT NULL
);

-- Tabela adicional existente no schema do BiotecPredict, não usada por este agente:
CREATE TABLE predictions (
  id                    INTEGER PRIMARY KEY,
  batch_id              INTEGER,      -- NOT NULL
  model_version         VARCHAR(50),  -- NOT NULL
  prediction_timestamp  DATETIME,     -- NOT NULL
  confidence_score      FLOAT,        -- NOT NULL
  risk_level            VARCHAR(50)   -- NOT NULL
);
```

1. **`data/biotecpredict.db` — nunca versionado, montado a partir de um
   dataset curado de demonstração.** Colocado manualmente em `data/` (ver
   `.gitignore`) — quem for rodar este projeto precisa gerar ou colocar seu
   próprio arquivo ali (ver README "Como executar"). A versão atual foi
   montada a partir de `data/simulacao_causa_raiz/csv/` — 15 lotes (5
   "ideais"/aprovados + 10 com um desvio de causa física única cada, ex.:
   contaminação do meio de cultura, bomba dosadora de pH com defeito,
   agitador com RPM baixo — ver `data/simulacao_causa_raiz/README.md` para
   a lista completa e a justificativa fisiológica de cada cenário). Os
   valores de sensor são desenhados propositalmente (um só parâmetro, ou
   um par fisiologicamente correlacionado, se desvia por vez — nunca os 5
   juntos), mas `compliance_score`/`classification`/`risk_prediction`
   **não são inventados**: vêm de rodar o `ComplianceService`/`MLModel`
   reais e inalterados do BiotecPredict sobre esses dados (validado em
   2026-07-19, valores documentados no README daquela pasta). Resultado:
   só 2 dos 15 lotes (`WARNING`) ficam elegíveis para investigação — os
   outros 8 lotes com desvio pontuam `ACCEPTABLE` no score real do
   BiotecPredict mesmo tendo uma causa física conhecida, o que é o
   comportamento correto do classificador, não uma falha do dataset. A
   tabela `predictions` existe no schema mas não é populada nem
   consultada. Um gabarito de teste (causa raiz esperada por lote
   elegível, com respostas sugeridas pras 11
   perguntas) fica em `docs/demo/gabarito-testes.md`.
2. **`tests/fixtures/biotecpredict_teste.db` — fixture sintética, só para
   testes automatizados.** Banco pequeno e determinístico, mesmo schema,
   incluindo um lote com `agitator_speed` fora da faixa (categoria Máquina,
   causa de fundo: falta de manutenção preventiva) — usado exclusivamente
   por `tests/`, nunca pela aplicação em execução. Arquivo estático,
   versionado (não há mais um script gerador no projeto — a fixture já
   está pronta e não precisa ser regenerada). Isso separa claramente "dado
   real de demonstração" (não versionado, variável) de "dado de teste"
   (versionado, determinístico, pequeno).
3. **Regras/limiares — três grupos, todos citados em `config/regras_bioprocesso.yaml`.**
   (a) os thresholds de classificação do `compliance_score`
   (`ACCEPTABLE >=80`, `WARNING >=45`, `CRITICAL <45`), replicando
   fielmente `_classify_score()` do BiotecPredict, já que essa lógica não
   está persistida no banco e o agente precisa recalculá-la; (b) faixas
   operacionais por parâmetro de biosensor, em dois níveis — `ideal`
   (ótimo) e `aceitável` (tolerável) — espelhando os campos reais
   `ideal_min`/`ideal_max`/`min_value`/`max_value` do BiotecPredict
   (`get_sensor_metrics()`), baseadas em literatura geral de cultivo
   celular/bioprocessos, sem alegar vínculo com uma instalação real
   específica; (c) as 6 categorias do Ishikawa (Método, Máquina, Material,
   Mão de obra, Meio ambiente, Medição) com uma pergunta-modelo por
   categoria, que `formular_pergunta_ishikawa` usa como ponto de partida
   (adaptando ao contexto da NC, não repetindo literalmente).
4. **Entrada = consulta SQL + cálculo determinístico.** `preparar_contexto`
   faz `SELECT * FROM batches WHERE status='COMPLETED' AND
   compliance_score IS NOT NULL`, aplica os thresholds de
   `config/regras_bioprocesso.yaml` pra calcular a `classification`, filtra
   para `WARNING`/`CRITICAL`; para o lote escolhido pelo operador, calcula
   `sensor_metrics` (média/min/max por parâmetro a partir de
   `sensor_readings`, replicando `get_sensor_metrics()`) e compara contra
   as faixas do YAML pra apontar `parametros_fora_da_faixa` — só então
   monta a `NaoConformidade` completa. Isso replica o mesmo tipo de
   consulta+cálculo que a API real do BiotecPredict faria — e é o que dá ao
   `formular_pergunta_ishikawa` a evidência concreta pra contextualizar a
   primeira rodada de perguntas — o `formular_porque` só entra depois, já
   ancorado na `categoria_principal` identificada pela orquestração.

**Nota de proveniência:** o *schema* (nomes de tabela, colunas, tipos,
enums, inclusive a tabela `predictions` não utilizada) é copiado fielmente
do código-fonte real do BiotecPredict. Os *valores* de demonstração são
curados (não uma captura de uma instância em produção, nem um dataset
público baixado) mas sua classificação/score/risco vêm de rodar o motor de
scoring real e inalterado do BiotecPredict sobre eles — ver ponto 1 acima;
os *valores* usados nos testes automatizados são sintéticos, recalibrados
pra mesma escala do dataset de demonstração, e claramente rotulados como
tal. A troca de domínio (agro → biotec, ver histórico em
`docs/prompts.md`) confirmou que a única coisa que muda de fato é
`config/` e `data/`; o motor (`root_cause_agent/`) permanece o mesmo.

## Camada de LLM plugável

`config.py::get_llm()` lê `LLM_PROVIDER` (default `google_genai`) e
`LLM_MODEL` (default `gemini-2.5-flash`) do `.env`, e usa
`langchain.chat_models.init_chat_model(model, model_provider=provider)`.
Trocar de LLM = mudar as duas variáveis + instalar o pacote de integração
correspondente (`langchain-anthropic`, `langchain-openai`, etc.) — não requer
tocar em `nodes.py` ou `graph.py`.

## Segurança e validação

- Entrada validada via Pydantic (`NaoConformidade`) antes de entrar no grafo.
- Chave de API só via `.env` (gitignored); `.env.example` documenta as
  variáveis sem valores.
- A tool é somente-leitura (`SELECT` apenas, nunca `INSERT`/`UPDATE`/`DELETE`),
  restrita ao banco SQLite local — sem acesso arbitrário a arquivos ou rede.
  **Validação da entrada da própria tool (2026-07-15):** `batch_id` não é
  mais um argumento que o LLM escolhe a cada chamada — vem injetado do
  estado (`nc_input.batch_id`) via `Annotated[AgentState, InjectedState]`
  do LangGraph, removido do schema exposto ao modelo, travando a consulta
  no lote da investigação em andamento. `data_inicio`/`data_fim` são
  validadas com `datetime.fromisoformat(...)`; formato inválido ou
  `data_inicio > data_fim` devolve uma mensagem de erro ao LLM (que pode
  tentar de novo com o formato certo) em vez de uma busca silenciosa que
  não bate com nada e parece "nenhuma leitura encontrada".
- Saída final validada contra o schema `Diagnostico` antes de ser salva.

## Roadmap (processo real completo — fase 2 não implementada nesta entrega)

O processo produtivo de tratamento de NC não termina no relatório gerado
pelo Root-Spector. Mapeado por completo no mapa de processo visual (BPMN,
ver `docs/prompts.md` para o link), a fase seguinte, ainda não
implementada, é:

**Fase 2 — Setor da Qualidade + Agente RAG, fechando em PDCA.** Só quando o
operador aceita o relatório (não pede ajuste) é que o caso sai do
Root-Spector. Ele vai para o setor da
Qualidade, que aciona um **segundo agente**, baseado em RAG
(retrieval-augmented generation), consultando uma base documental da
empresa (procedimentos internos, legislação aplicável ao setor, normas
ANVISA, referências bibliográficas) para recomendar como tratar aquela NC —
uma ação corretiva + um Kaizen de melhoria, estruturados como **Plan** de
um ciclo PDCA. O relatório final consolidado (causa raiz + plano PDCA +
fontes citadas) vai para a **Garantia da Qualidade** — não retorna ao
operador. A Garantia da Qualidade não executa o plano automaticamente:
**avalia junto com a Coordenação da Produção** e decide se mantém a
sugestão do Agente RAG como está ou ajusta algo antes de seguir. Só depois
dessa decisão conjunta o plano é **executado** (Do) e, em seguida,
**verificado quanto à eficácia com base em reincidência do problema**
(Check): sem reincidência, o plano é padronizado; havendo reincidência, um
novo plano é gerado pelo Agente RAG (Act) — a causa raiz identificada
originalmente pode ter sido incompleta.

**Por que isso fica fora do escopo desta entrega:** exige infraestrutura
que este projeto ainda não tem (ingestão de documentos, embeddings, vector
store, um grafo próprio) — construir isso de verdade seria essencialmente
um segundo projeto — ver `specs/requirements.md` "Fora de escopo". O loop
de revisão do operador (relatório já gerado / pedir ajuste), que
originalmente também estava nesta lista, **já está implementado** (ver
"Fluxo do grafo" acima) — era tecnicamente simples de encaixar no motor
atual e passou a fazer parte do escopo real.

## Adaptação a outro setor produtivo

Para adaptar a outro setor (ex: agronegócio, laticínios, metalurgia): (1)
criar um novo `config/regras_<setor>.yaml` com os limiares/parâmetros
daquele setor; (2) apontar `data/` para o dataset de contexto relevante
daquele setor; (3) ajustar os campos de `NaoConformidade` em `models.py` se o
setor tiver atributos muito diferentes de lote/parâmetro de processo. O
grafo, os nós e a lógica do agente não mudam — este projeto nasceu desenhado
para agronegócio/grãos (regras da Embrapa + série do INMET) e foi
re-configurado para bioprocessos exatamente seguindo esses 3 passos.
