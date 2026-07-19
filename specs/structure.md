# Estrutura do Projeto — Root-Spector

Organização de diretórios: motor do agente em Python (`root_cause_agent/`),
API web separada em `backend/`, frontend React minimalista, configuração/dados
separados do código, specs e documentação versionadas.

`root_cause_agent/` é a biblioteca do agente — autossuficiente, sem nenhuma
dependência de FastAPI, importável e executável (via `main.py`, o harness)
sem subir servidor nenhum. `backend/` é a camada web: importa
`root_cause_agent` como dependência e expõe o grafo por HTTP pro `frontend/`.
Essa separação é o que permite reusar o motor do agente em outro contexto
(ex.: um outro setor produtivo, ou uma CLI) sem arrastar FastAPI junto — ver
`specs/product.md` § adaptabilidade.

---

## Estrutura de Diretórios

```
/
├── root_cause_agent/
│   ├── __init__.py
│   ├── models.py         # Pydantic: NaoConformidade, RespostaIshikawa, PorQue,
│   │                      # CategoriaAnalise, CategoriaDescartada, CicloAnterior, Diagnostico
│   ├── state.py           # AgentState (TypedDict) + CATEGORIAS_ISHIKAWA_ORDEM
│   ├── config.py           # .env, get_llm() (fallback Gemini→Groq→Anthropic→OpenAI),
│   │                        # carga do YAML de regras, caminhos dos .db
│   ├── tools.py              # consultar_leituras_biosensor (batch_id via InjectedState,
│   │                          # datas validadas); validar_resposta_operador (Camada 1)
│   ├── nodes.py                # preparar_contexto, formular_pergunta_ishikawa,
│   │                            # orquestrar_analise, formular_porque, perguntar_operador,
│   │                            # avaliar_informatividade, gerar_causa_raiz; FalhaLLMError
│   ├── graph.py                 # monta e compila o StateGraph com checkpointer SqliteSaver
│   ├── reports.py                # Diagnostico -> reports/{batch_id}_{ts}.json + .html (Jinja2)
│   └── main.py                     # harness de teste (roda o grafo com respostas em código)
│
├── backend/                          # FastAPI -- camada web, depende de root_cause_agent
│   ├── __init__.py
│   └── main.py                          # app FastAPI: lotes, investigação, ajuste,
│                                          # serve reports/ como estático (uvicorn backend.main:app)
│
├── frontend/                       # React + TypeScript + Vite — única tela, sem router
│   ├── DESIGN.md                       # tokens, tipografia, padrões de layout do design system
│   └── src/
│       ├── App.tsx                    # máquina de estado: lista → pergunta → revisão (já com o link do relatório)
│       ├── api.ts                      # fetch() helpers pro backend/
│       ├── statusBadge.ts              # classification/risk_prediction -> classe de badge pastel
│       ├── parametroLabel.ts           # chave do sensor (agitator_speed) -> rótulo em português
│       ├── styles/tokens.css           # CSS custom properties (cor, tipografia, raio) do design system
│       └── components/
│           ├── ListaLotes.tsx (+ .test.tsx)          # lista + parâmetro(s) fora da faixa por lote
│           ├── PerguntaAtual.tsx (+ .test.tsx)        # pergunta + histórico de parâmetros do lote
│           └── RevisaoRespostas.tsx (+ .test.tsx)     # cadeia + link do relatório | pedir ajuste
│
├── deploy/
│   ├── backend.Dockerfile
│   ├── frontend.Dockerfile
│   ├── nginx.conf
│   └── docker-compose.yml
│
├── config/
│   └── regras_bioprocesso.yaml     # thresholds, faixas por sensor, categorias Ishikawa
│                                    # (trocar este arquivo adapta o agente a outro setor)
│
├── data/
│   ├── biotecpredict.db                # NUNCA versionado -- montado a partir de simulacao_causa_raiz/
│   ├── checkpoints.db                  # NUNCA versionado -- estado do LangGraph em runtime (gerado)
│   └── simulacao_causa_raiz/           # dataset curado versionado: 15 lotes (5 ideais + 10 com desvio)
│       ├── README.md                      # causa raiz + parâmetro(s) afetado(s) de cada cenário
│       └── csv/                             # 1 arquivo por lote (leituras brutas, sem score/classificação)
│
├── tests/                             # toda a suíte de testes, um único diretório
│   ├── fixtures/
│   │   └── biotecpredict_teste.db      # estático, versionado (pequeno, determinístico)
│   ├── test_tools.py
│   ├── test_graph.py
│   ├── test_config.py                  # fallback de LLM (mockado, ver specs/tech.md)
│   ├── test_backend.py                 # rotas do backend/ + contrato OpenAPI
│   └── e2e/                            # Playwright -- pacote Node próprio, E2E local + CI
│       ├── playwright.config.ts             # webServer: sobe backend + frontend automaticamente
│       └── tests/
│           └── investigacao.spec.ts             # fluxo completo + caso de "pedir ajuste"
│
├── reports/                          # saída em runtime (JSON + HTML); só .gitkeep versionado
│
├── scripts/
│   └── setup_github.py               # administração do GitHub (labels, milestones, issues,
│                                      # branches vazias, board) — não faz parte do agente em
│                                      # execução, ver specs/gitflow.md e docs/gitflow.md
│
├── specs/                            # contexto permanente do projeto (este diretório)
│   ├── product.md                       # visão de produto, problema, solução, escopo
│   ├── tech.md                          # stack tecnológica
│   ├── structure.md                     # este arquivo
│   ├── requirements.md                  # RF/RNF, entrada/saída, critérios de aceitação
│   ├── design.md                        # arquitetura, fluxo do grafo, decisões
│   ├── ci-cd.md                         # workflows do GitHub Actions
│   └── gitflow.md                       # convenção de branches/commits/PRs (metodologia)
│
├── docs/
│   ├── PRD.md                        # documento de requisitos de produto
│   ├── cenarios-de-uso.md            # cenários de uso passo a passo (fluxo principal + erro/ajuste)
│   ├── diagrama-fluxo.md             # diagramas Mermaid: grafo LangGraph + sequência HTTP
│   ├── openapi.yaml                  # contrato da API, gerado a partir do schema real do FastAPI
│   ├── prompts.md                    # registro cronológico dos prompts/decisões do projeto
│   ├── gitflow.md                    # plano operacional: milestones, branches, issues, status
│   ├── apresentacao.md               # fonte em markdown (problema/agente/entrada/saída/ferramenta/fluxo)
│   ├── apresentacao.html             # versão navegável em HTML (2 slides, mesmo conteúdo)
│   ├── mapeamento-processo.html      # mapa BPMN do processo (Fase 1 implementada + Fase 2 roadmap)
│   ├── fluxo-tecnico-agente.html     # fluxo técnico do agente (grafo, interrupt/checkpointer)
│   ├── checklist-fluxo.html          # checklist visual do rubric
│   └── demo/                         # screenshots de demonstração + gabarito-testes.md (roteiro de
│                                      # respostas prontas pra testar os lotes elegíveis do dataset atual)
│
├── .github/
│   └── workflows/
│       └── ci.yml                    # lint (ruff) + testes (pytest), develop/release/PRs
│
├── .dockerignore
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

---

## Responsabilidades por Camada

### `root_cause_agent/`

Motor do agente. Cada módulo tem responsabilidade única — é essa separação
(planejamento/estado, execução determinística, uso de ferramenta, geração
da resposta) que satisfaz o critério do rubric sobre organização do agente,
sem precisar de camadas completas de Clean Architecture (RNF5).

| Módulo | Tipo | Responsabilidade |
|---|---|---|
| `models.py` | Schemas | Contratos de entrada/saída (Pydantic) |
| `state.py` | Estado | `AgentState` — memória compartilhada do grafo |
| `config.py` | Configuração | `.env`, seleção/fallback de LLM, YAML de regras |
| `tools.py` | Ferramenta + validação | Consulta a biosensor; validação determinística da resposta do operador |
| `nodes.py` | Nós do grafo | Lógica determinística + agêntica de cada etapa |
| `graph.py` | Grafo | Monta/compila o `StateGraph` com checkpointer |
| `reports.py` | Saída | Serialização do `Diagnostico` em JSON/HTML |
| `main.py` | Harness | Execução não-interativa do grafo, usada pelos testes |

### `backend/`

Camada web — único lugar do projeto com dependência de FastAPI. Importa
`root_cause_agent` (grafo, models, config) como biblioteca; nunca o
contrário. Responsabilidade: expor o grafo por HTTP (listar lotes, iniciar/
responder/revisar/ajustar investigação — `responder` já gera o relatório ao
concluir o ciclo), tratar `FalhaLLMError` como HTTP 503, e servir `reports/`
como estático pro frontend consumir o link do relatório. Ver
`specs/design.md` § Interface para o contrato completo de rotas.

### `config/`

Regras do setor produtivo — o único lugar com limiares/nomes específicos
(RNF3). Para adaptar a outro setor: trocar este arquivo (mesma estrutura de
chaves), sem tocar em `root_cause_agent/`.

### `data/`

`biotecpredict.db` (a entrada da aplicação) e `checkpoints.db` (estado do
LangGraph em runtime) nunca são versionados. `simulacao_causa_raiz/` é a
exceção — dataset curado e **versionado** (CSVs + README com a causa raiz
de cada cenário), fonte a partir da qual o `biotecpredict.db` local é
montado (colocado manualmente, mesma pasta) — ver `specs/design.md` §
Estratégia de dados.

### `tests/`

Toda a suíte de testes vive num único diretório. `tests/fixtures/biotecpredict_teste.db`
é a única base de dados que os testes automatizados usam — pequena,
determinística, versionada (arquivo estático, sem script gerador no
projeto). Nunca usada pela aplicação em execução. Os testes Python cobrem
o agente (`test_tools.py`, `test_graph.py`), a cadeia de fallback de LLM
(`test_config.py`, mockada) e o `backend/` (`test_backend.py`, via
`TestClient` + contrato OpenAPI) — nenhum desses testes chama um provedor
de LLM real.

`tests/e2e/` é um pacote Node próprio (Playwright), separado de
`frontend/` — a suíte não faz parte do build da aplicação, só do processo
de verificação. `webServer` em `playwright.config.ts` sobe `backend/`
(uvicorn) e `frontend/` (vite dev) automaticamente antes dos testes,
sempre contra `tests/fixtures/biotecpredict_teste.db` e `LLM_PROVIDER=fake`.
Mesmo comando (`npx playwright test`, rodado dentro de `tests/e2e/`) roda
local e no CI (`.github/workflows/ci.yml`, job `e2e`).

### `specs/` vs. `docs/`

Distinção deliberada: `specs/` é contexto **estável** (visão de produto,
stack, estrutura, requisitos, arquitetura, convenções) — muda pouco depois
de definido. `docs/` é acompanhamento **vivo** do projeto (histórico de
prompts, status de milestones/branches/issues) — muda a cada sessão de
trabalho. `specs/gitflow.md` define a convenção; `docs/gitflow.md` aplica
essa convenção ao plano concreto desta entrega.

---

## Convenções

- Nomes de arquivos e módulos em `snake_case` (Python).
- Nomes de componentes em `PascalCase` (React/TypeScript).
- Cada módulo do agente tem responsabilidade única — lógica de decisão de
  conteúdo (LLM) fica em `nodes.py`, nunca em `tools.py`/`config.py`.
- Imports absolutos a partir de `root_cause_agent.*`.
- Nenhum limiar de setor hardcoded fora de `config/`.

---

**Versão**: 0.1.0
**Status**: agente, backend, frontend e testes (pytest + Vitest + Playwright)
implementados e verificados localmente, inclusive via `deploy/`
(Docker) — commits/branches/PRs formais do Gitflow ainda pendentes (ver
`docs/gitflow.md`).
