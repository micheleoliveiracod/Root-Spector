# Gitflow do projeto — plano operacional

> **Status:** a estrutura do GitHub já foi criada rodando
> `scripts/setup_github.py` — os 6 milestones, as 20 labels (9 padrão do
> GitHub + 11 deste projeto) e as issues (21 definidas no script; 22 no
> repositório no momento, 1 a mais por uma execução anterior — ver nota
> abaixo) existem de verdade, assim como as 6 branches vazias
> (`develop` + as 5 de milestone, sem nenhum commit). O que **não** foi
> feito ainda é o trabalho de Gitflow em si: nenhum código foi commitado
> nessas branches, nenhum PR foi aberto/mergeado além de M1 — todo o
> desenvolvimento de M2 a M5 existe só localmente (ver `docs/prompts.md`
> para o histórico da decisão de concentrar o trabalho local antes de
> formalizar o Gitflow, e `specs/structure.md` § Status).

Ver `specs/gitflow.md` para a convenção (modelo de branches, commits, PRs,
Kanban), verificada contra o Gitflow clássico oficial. Este arquivo aplica
essa convenção ao Root-Spector: quais branches concretas existem, o que
cada uma cobre, e o status de cada issue.

## Passo zero

Automatizado por `scripts/setup_github.py` (idempotente, sem nenhum
commit de código — só estrutura do GitHub):

1. Cria os 6 milestones: M1, M2, M3, M4, M5 e Release (sem data de
   entrega — ver `specs/gitflow.md`, que não fixa prazos).
2. Cria as 5 labels de tipo (`docs`, `chore`, `feature`, `test`,
   `bugfix`) e as 6 labels de etapa (tabela abaixo).
3. Cria 21 issues (no máximo 5 por milestone), agrupando itens
   relacionados do checklist detalhado abaixo numa única issue — o corpo
   de cada issue lista os itens agrupados. Já conectada ao milestone e às
   labels de tipo + etapa. Todas tratadas de forma uniforme: nenhuma cita
   ou pressupõe que M1/M2/parte de M3 já foram concluídas — abrem como se
   nada tivesse começado ainda, todas em Backlog.

`python scripts/setup_github.py` roda os passos acima. Antes de qualquer
chamada ao GitHub, roda uma validação 100% local (`validate_data()`) que
confere se todo milestone/label referenciado nas issues existe de fato e
se não há título duplicado — pega erro de copiar/colar sem criar nada
errado (uma issue criada errada não dá pra desfazer sem sujeira). Rodar
com `--dry-run` mostra o comando `gh issue create` completo — título,
corpo, labels, milestone — de cada issue antes de executar de verdade.
`--branches` também cria `develop` + as 5 branches de milestone, todas
vazias, sem nenhum commit — o código em si continua sendo trabalho manual.

## Branches × Milestones

Todas nascem de `develop` e voltam pra `develop` via PR. O prefixo segue o
tipo de arquivo predominante que a branch sobe (ver `specs/gitflow.md` §
Modelo de branches).

| # | Branch | Milestone | Cobre |
|---|--------|-----------|-------|
| 1 | `docs/especificacao-e-arquitetura` | M1 — Especificação & Arquitetura | `specs/`, estrutura de pastas, stubs dos módulos, docs iniciais (README, slides em rascunho, `docs/gitflow.md`) |
| 2 | `chore/dados-e-configuracao` | M2 — Dados & Configuração | `config/regras_bioprocesso.yaml` (thresholds, faixas por sensor, categorias Ishikawa) e confirmação do schema real via `data/biotecpredict.db`; `tests/fixtures/biotecpredict_teste.db` como fixture estática de teste |
| 3 | `feature/implementacao-agente` | M3 — Implementação do Agente | `root_cause_agent/` completo (`models.py`, `state.py`, `config.py`, `tools.py`, `nodes.py`, `graph.py`, `reports.py`, `main.py` harness), `backend/` (FastAPI, pacote próprio — ver `specs/structure.md`), `frontend/` |
| 4 | `test/testes-e-verificacao` | M4 — Testes & Verificação | `test_tools.py`, `test_graph.py`, `test_config.py` (fallback), `test_backend.py` (rotas + OpenAPI), testes do `frontend/` (Vitest), `tests/e2e/` (Playwright, local + CI), workflow de CI (`.github/workflows/ci.yml`) |
| 5 | `docs/documentacao-final` | M5 — Documentação & Entrega | README completo, `docs/prompts.md` final, slides revisados, checklist do rubric, `deploy/` (Docker + docker-compose) |
| — | `release/v1.0-entrega` | **Release** (6º milestone, não é `feature/*`/`docs/*`/etc.) | Nasce de `develop` só depois das 5 branches acima mergeadas; **PR pra `main`** (nunca push/commit direto), tag `v1.0-entrega` após o merge, e back-merge (também via PR) em `develop` — é esse PR mergeado que vira a submissão no AVA |

## Labels de etapa

6 labels (dentro do limite de 10), uma por milestone — aplicada a toda
issue daquele milestone, junto com a label de tipo (`docs`/`chore`/
`feature`/`test`/`bugfix`, passo 4 acima). É a forma mais rápida de ver de
qual etapa do projeto uma issue é, sem abrir o card.

| Label | Cor | Milestone |
|---|---|---|
| `m1: especificação` | 🔵 `#1d76db` | M1 — Especificação & Arquitetura |
| `m2: dados & config` | 🟢 `#0e8a16` | M2 — Dados & Configuração |
| `m3: implementação` | 🟣 `#5319e7` | M3 — Implementação do Agente |
| `m4: testes` | 🟡 `#fbca04` | M4 — Testes & Verificação |
| `m5: documentação` | 🟠 `#d93f0b` | M5 — Documentação & Entrega |
| `release` | 🔴 `#b60205` | Release |

## CI/CD

Ver `specs/ci-cd.md` para o workflow completo (`.github/workflows/ci.yml`,
implementado no milestone M4).

## Como issues, branches e milestones se conectam

- **1 milestone = 1 branch** (tabela acima) — exceto Release, que também é
  milestone + branch, mas fora do padrão `feature/*` (é `release/*`, ver
  `specs/gitflow.md` § Modelo de branches).
- **Itens relacionados do checklist são agrupados numa única issue**
  (máximo 5 por milestone, ver tabela em `scripts/setup_github.py`), não
  1:1 — o corpo de cada issue lista os itens do checklist que ela cobre.
  Cada issue nasce já atribuída ao milestone correspondente (M1…M5 ou
  Release), com a label de tipo compatível com o prefixo da branch
  (`docs`, `chore`, `feature`, `test`, `bugfix`) **e** a label de etapa
  correspondente (`m1: especificação`…`m5: documentação`/`release`, ver
  tabela acima) — duas labels por issue, tipo + etapa. Nenhuma issue cita
  ou pressupõe que o trabalho já foi feito, mesmo pra M1/M2/parte de M3 —
  todas abrem em Backlog, como se nada tivesse começado.
- **1 branch fecha todas as issues do seu milestone** — o PR de
  `feature/implementacao-agente` → `develop`, por exemplo, referencia
  "Closes #N" para cada issue aberta de M3, não uma issue isolada por
  commit.
- **`main` só recebe conteúdo via Pull Request** — nunca commit ou push
  direto, nem nas 5 branches de milestone (que vão pra `develop`) nem na
  release (`release/v1.0-entrega` → `main` via PR, com back-merge também
  via PR pra `develop`).
- **Toda issue nasce no board na coluna Backlog**, anda pra In Progress
  quando a branch do milestone é aberta, In Review quando o PR abre (CI
  rodando/verde), Done quando o PR mergeia em `develop` — ver
  `specs/gitflow.md` § Kanban. Sem automação de workflow (ver
  `specs/ci-cd.md` § Fora do escopo), esse movimento é manual.

## Issues por milestone

Cada `###` abaixo é 1 issue de verdade no GitHub (título em negrito);
os sub-itens são o que o corpo dessa issue lista, não issues à parte —
ver `scripts/setup_github.py::ISSUES` pra fonte exata. 21 issues no total,
no máximo 5 por milestone.

### M1 — Especificação & Arquitetura (3 issues)
- [x] **Estrutura de pastas, stubs do pacote e specs completas**
  - Estrutura de pastas e stubs do pacote
  - `specs/requirements.md`
  - `specs/design.md`
  - `specs/product.md`, `specs/tech.md`, `specs/structure.md`, `specs/ci-cd.md`, `specs/gitflow.md`
- [x] **README.md inicial**
  - README.md inicial (esqueleto)
- [x] **Apresentação e plano operacional do Gitflow**
  - `docs/apresentacao.md` esqueleto
  - Este arquivo (`docs/gitflow.md`)

### M2 — Dados & Configuração (2 issues)
- [x] **Configuração do setor e fixture de teste**
  - `config/regras_bioprocesso.yaml` (thresholds de classification, faixas por sensor, 6 categorias Ishikawa)
  - `tests/fixtures/biotecpredict_teste.db` — fixture sintética estática, usada só pelos testes automatizados, nunca pela aplicação (sem script gerador no projeto — o arquivo já está pronto e versionado)
- [x] **Confirmar schema real via `data/biotecpredict.db`**
  - Schema real do BiotecPredict confirmado via exportação real, colocada manualmente, não versionada — inclui tabela `predictions` (não usada) e lotes com `compliance_score` nulo (tratados como não elegíveis)
  - Dataset de demonstração atual: `data/simulacao_causa_raiz/` (versionado, 15 lotes curados), a partir do qual `data/biotecpredict.db` é montado localmente, classificado pelo motor real do BiotecPredict — ver `specs/design.md` § Estratégia de dados

### M3 — Implementação do Agente (5 issues)
- [x] **Schemas, estado e configuração (models, state, config, pyproject)**
  - `models.py` (schemas Pydantic: NaoConformidade, RespostaIshikawa, PorQue, Diagnostico, CicloAnterior)
  - `state.py` (AgentState: nc_input, regras_setor, messages, respostas_ishikawa, categoria_atual, categoria_principal, categorias_descartadas, cadeia_porques, numero_porque, pergunta_atual, tentativas_pergunta_atual, ciclos_anteriores, diagnostico)
  - `config.py` (seleção de LLM via `init_chat_model`, carga do YAML de regras, caminhos dos `.db`; fallback em cadeia Gemini → Groq → Anthropic → OpenAI via `with_fallbacks(...)`, cada camada só ativa se a respectiva chave estiver no `.env`)
  - `pyproject.toml` com as dependências reais (langgraph, langgraph-checkpoint-sqlite, langchain, langchain-google-genai, langchain-anthropic, langchain-openai, pyyaml, python-dotenv, fastapi, uvicorn, jinja2)
- [x] **Ferramenta e validação da resposta do operador (tools.py)**
  - `consultar_leituras_biosensor` (SQL somente-leitura em `sensor_readings`, `batch_id` injetado do estado via `InjectedState` — não escolhido pelo LLM —, `data_inicio`/`data_fim` validadas)
  - `validar_resposta_operador`, Camada 1 de validação da resposta do operador
- [x] **Núcleo do grafo (nodes.py, graph.py)**
  - `nodes.py` (preparar_contexto [+ cálculo de sensor_metrics/parametros_fora_da_faixa], formular_pergunta_ishikawa, orquestrar_analise, formular_porque, perguntar_operador [human-in-the-loop via `interrupt()`, Camada 1 de validação, reusado nas duas fases], avaliar_informatividade [Camada 2, até 2 tentativas por pergunta], gerar_causa_raiz; `FalhaLLMError` capturada em cada nó agêntico)
  - `graph.py` (StateGraph com dois loops em sequência + checkpointer `SqliteSaver` para suportar pausa/retomada via API)
- [x] **Relatórios e API (reports.py, api.py, main.py harness)**
  - `root_cause_agent/reports.py` (Diagnostico → `reports/{batch_id}_{timestamp}.json` + `.html`, template Jinja2)
  - `backend/main.py` (FastAPI, pacote próprio, depende de `root_cause_agent`: listar lotes, iniciar/responder/revisar/ajustar investigação, servir relatórios — `responder` já gera o relatório ao concluir o ciclo; captura `FalhaLLMError` e devolve HTTP 503 "Serviço de IA indisponível, recarregue a página.")
  - Converter `root_cause_agent/main.py` em harness de teste (roda o grafo com respostas fornecidas em código, sem servidor)
- [x] **Scaffold frontend/ (React + TypeScript + Vite)**
  - Lista de lotes → pergunta atual (+ histórico de parâmetros do lote) → revisão (já com o link do relatório)
  - Design system próprio (`frontend/DESIGN.md`, `styles/tokens.css`), badges pastel de status, indicador de carregamento durante chamadas ao LLM

### M4 — Testes & Verificação (5 issues)
- [x] **Testes automatizados (test_tools.py, test_graph.py)**
  - `test_tools.py` (janela de datas filtrada corretamente, usando a fixture sintética)
  - `test_graph.py` (via harness de `main.py`, sem servidor: roda o grafo com 11 respostas fornecidas — 6 Ishikawa + 5 porquês —, produz `Diagnostico` válido com `categoria_principal` e `cadeia_de_porques` de tamanho 5; cobre também o caso de "pedir ajuste" gerando um segundo ciclo)
  - `test_config.py` (cadeia de fallback Gemini → Groq → Anthropic → OpenAI, provedores mockados; cobre o caso de todos falharem → `FalhaLLMError`)
- [x] **Testes do backend (FastAPI: rotas + contrato OpenAPI)**
  - `test_backend.py` — rotas de `backend/main.py` via `TestClient`, grafo mockado onde executa um nó agêntico
  - Caminho de erro: `FalhaLLMError` simulada → HTTP 503 com a mensagem exata
  - Contrato `GET /openapi.json` validado com `openapi-spec-validator`
- [x] **Testes do frontend (componentes React)**
  - Vitest + React Testing Library configurados em `frontend/`
  - `ListaLotes`, `PerguntaAtual`, `RevisaoRespostas` — render + interação básica, `api.ts` mockado
- [x] **Testes E2E (Playwright, local + GitHub Actions)**
  - `tests/e2e/` (Playwright): `webServer` sobe backend + frontend automaticamente
  - Cenário principal: lista de lotes → 11 perguntas → revisão → conferir link do relatório já gerado
  - Cenário de ajuste: revisão → pedir ajuste → novo ciclo → conferir link do novo relatório + `ciclos_anteriores`
  - Sempre contra `tests/fixtures/biotecpredict_teste.db` e `LLM_PROVIDER=fake` — mesmo comando local e no CI
- [x] **Workflow de CI (.github/workflows/ci.yml)**
  - Jobs: `lint` (ruff), `test` (pytest — agente + backend), `frontend-test` (Vitest), `e2e` (Playwright) — ver `specs/ci-cd.md` para os triggers

**Nota:** todos os itens acima ([x]) estão implementados, testados e
verificados **localmente** (33 pytest + Vitest + 2 cenários Playwright,
todos verdes; verificado também rodando via `deploy/` no Docker) — os
commits/branches/PRs formais do Gitflow (`chore/dados-e-configuracao`,
`feature/implementacao-agente`, `test/testes-e-verificacao`) ainda não
foram executados, só M1 está de fato commitado/mergeado. Ver `docs/prompts.md`
para o histórico da decisão de concentrar o trabalho local antes de
formalizar o Gitflow.

### M5 — Documentação & Entrega (3 issues)
- [x] **README completo + checklist final do rubric**
  - README com todas as seções (como executar, exemplo real de entrada/saída
    alinhado ao dataset atual) preenchidas e revisadas
  - `deploy/` (Docker + docker-compose) implementado e verificado (build + up
    + investigação completa rodando via container)
  - `docs/PRD.md`, `docs/cenarios-de-uso.md`, `docs/diagrama-fluxo.md`
    (Mermaid) e `docs/openapi.yaml` adicionados como documentação
    complementar do escopo atual
- [x] **Revisar docs/apresentacao.md**
- [ ] **Issue final: subir docs/prompts.md completo**
  - Registro de todos os prompts do projeto, do M1 ao M5 — só fecha depois de tudo o mais acima, já que o log só está completo no fim

### Release (3 issues)
- [x] **Abrir release/v1.0-entrega e conferir CI verde**
  - `release/v1.0-entrega` aberta a partir de `develop` (já com M2–M5
    mergeados), PR aberto contra `main`
  - CI: workflow disparado no PR de M4 (#36) apresentou `startup_failure`
    antes de qualquer job rodar (config/permissão de Actions da conta,
    não um problema do `ci.yml` — YAML validado); conferir localmente
    (`pytest`, `npm run test`, `npx playwright test`) enquanto isso não
    for resolvido
- [ ] **Merge em main + tag v1.0-entrega + back-merge em develop**
  - Abrir PR `release/v1.0-entrega` → `main` (nunca commit/push direto em `main`), revisar e mergear com `--no-ff`
  - Tag `v1.0-entrega` em `main` após o merge
  - Back-merge de `release/v1.0-entrega` em `develop`, também via PR
- [ ] **Submissão do link do repositório no AVA**
