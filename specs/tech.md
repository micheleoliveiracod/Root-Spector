# Stack Tecnológica — Root-Spector

Definição das tecnologias usadas no projeto. Ver `specs/design.md` para as
decisões de arquitetura por trás de cada escolha.

---

## Backend / Agente

| Tecnologia | Papel | Versão |
|---|---|---|
| **Python** | Linguagem principal | 3.11+ |
| **LangGraph** | Orquestração do grafo (estado, nós, `interrupt()`, checkpointer) | 0.2+ |
| **langgraph-checkpoint-sqlite** | Checkpointer `SqliteSaver` — persiste o estado da investigação por `thread_id`, viabilizando pausa/retomada via API | 2.0+ |
| **LangChain** | `init_chat_model` (seleção de provedor/modelo plugável), `@tool`, `with_fallbacks` | 0.3+ |
| **langchain-google-genai** | Integração com Gemini — provedor oficial, gratuito, usado em testes e prototipagem | 2.0+ |
| **langchain-groq** | Fallback de LLM (2º da cadeia, Groq) — gratuito, ativado se `GROQ_API_KEY` estiver configurada | 0.2+ |
| **langchain-anthropic** | Fallback de LLM (3º da cadeia), ativado se `ANTHROPIC_API_KEY` estiver configurada | 0.3+ |
| **langchain-openai** | Fallback de LLM (4º da cadeia), ativado se `OPENAI_API_KEY` estiver configurada | 0.2+ |
| **Pydantic** | Validação de schemas (`NaoConformidade`, `Diagnostico`, etc.) | 2.9+ |
| **FastAPI** | API web local (lotes, investigação, ajuste de ciclo) | 0.115+ |
| **Uvicorn** | Servidor ASGI | 0.32+ |
| **Jinja2** | Template do relatório HTML | 3.1+ |
| **SQLite** (`sqlite3`, stdlib) | Leitura de `data/biotecpredict.db` e da fixture de teste; persistência do checkpointer | 3.x |
| **PyYAML** | Carga de `config/regras_bioprocesso.yaml` | 6.0+ |
| **python-dotenv** | Carga de `.env` | 1.0+ |
| **pytest** | Testes automatizados | 8.3+ |
| **pytest-mock** | Mock da cadeia de fallback de LLM (simula provedor falhando, sem chamada real) | 3.14+ |
| **httpx** | Cliente HTTP para testes da API FastAPI (via `TestClient`) | 0.27+ |
| **openapi-spec-validator** | Valida que `GET /openapi.json` é um documento OpenAPI bem formado | 0.7+ |
| **ruff** | Lint | 0.7+ |

---

## Frontend

| Tecnologia | Papel | Versão |
|---|---|---|
| **Node.js** | Runtime de build | 20+ |
| **React** | UI — uma única tela, sem router | 18+ |
| **TypeScript** | Tipagem estática | 5.0+ |
| **Vite** | Build tool | 5.0+ |
| **Vitest** | Testes unitários dos componentes | 2.0+ |
| **React Testing Library** | Render + interação nos testes de componente | 16.0+ |

Deliberadamente minimalista (RNF5): sem `react-router`, sem biblioteca de
gerência de estado (Redux/Zustand), sem TailwindCSS — CSS simples. A tela
única implementa uma máquina de estados local (`useState`): lista de lotes
→ pergunta atual → revisão → link do relatório.

---

## E2E

| Tecnologia | Papel | Versão |
|---|---|---|
| **Playwright** (`@playwright/test`) | Suíte E2E em `tests/e2e/`, sobe backend + frontend via `webServer` e roda o fluxo completo no navegador (headless), local e no CI, mesmo comando | 1.48+ |

Sempre contra `tests/fixtures/biotecpredict_teste.db` e `LLM_PROVIDER=fake`
— nunca contra `data/biotecpredict.db` nem um provedor real (custo e
determinismo no CI).

---

## LLM plugável e fallback

`config.py::get_llm()` monta a cadeia principal + fallback:

```
Gemini (LLM_PROVIDER/LLM_MODEL, oficial, gratuito)
   ↓ falha (rede/rate limit/chave)
Groq (só se GROQ_API_KEY estiver no .env — 2º provedor gratuito)
   ↓ falha
Anthropic (só se ANTHROPIC_API_KEY estiver no .env)
   ↓ falha
OpenAI (só se OPENAI_API_KEY estiver no .env)
   ↓ falha (ou nenhum fallback configurado)
FalhaLLMError → API devolve HTTP 503
```

Trocar o provedor principal = mudar `LLM_PROVIDER`/`LLM_MODEL` no `.env` +
instalar o pacote de integração correspondente — não requer tocar em
`nodes.py`/`graph.py`. Rodar só com a chave do Gemini (cenário mínimo de
testes/prototipagem) continua funcionando sem exigir Groq/Anthropic/OpenAI;
configurar `GROQ_API_KEY` permite testar o agente com um 2º LLM de verdade,
também gratuito.

---

## Fluxo de Dados Completo

```
Operador escolhe o lote (interface web)
        ↓
preparar_contexto            → SELECT em batches/sensor_readings (SQLite)
        ↓
Ishikawa (6 perguntas)       → nós LLM, tool consultar_leituras_biosensor quando útil
        ↓
orquestrar_analise           → identifica categoria_principal
        ↓
5 Porquês (ancorado)         → nós LLM, mesma tool
        ↓
gerar_causa_raiz             → Diagnostico (Pydantic)
        ↓
reports.py                   → reports/{batch_id}_{ts}.json + .html
        ↓
Revisão do operador          → link do relatório já disponível | pedir ajuste
```

---

## Dataset

**Fonte de demonstração:** `data/biotecpredict.db`, colocada manualmente,
nunca versionada — montada a partir do dataset curado e versionado
`data/simulacao_causa_raiz/csv/` (15 lotes), classificado pelo motor real do
[BiotecPredict](https://github.com/micheleoliveiracod/Projeto-avaliativo-M1-2-BiotecPredict)
(`ComplianceService`/`MLModel`, não reimplementado por este projeto).

**Fonte de teste:** `tests/fixtures/biotecpredict_teste.db` — fixture
sintética e determinística, estática e versionada, mesmo schema, usada só
por `tests/`.

Ver `specs/design.md` § Estratégia de dados para o schema completo
(`batches`, `sensor_readings`, `predictions`) e a proveniência de cada
valor.

---

## Arquitetura de Processamento

Root-Spector **não** é um pipeline ETL como o BiotecPredict — é um grafo de
estado (LangGraph) que intercala etapas determinísticas (workflow) com
etapas de decisão de conteúdo (agente). Ver `specs/design.md` § Por que
isso é um agente para a distinção completa.

| Etapa | Tipo | Componente | Localização |
|---|---|---|---|
| Identificar parâmetros fora da faixa | Determinístico | `preparar_contexto` | `nodes.py` |
| Formular pergunta (Ishikawa/5 Porquês) | Agêntico (LLM) | `formular_pergunta_ishikawa`, `formular_porque` | `nodes.py` |
| Consultar biosensor | Ferramenta | `consultar_leituras_biosensor` | `tools.py` |
| Validar resposta (Camada 1) | Determinístico | `validar_resposta_operador` | `tools.py` |
| Julgar informatividade (Camada 2) | Agêntico (LLM) | `avaliar_informatividade` | `nodes.py` |
| Identificar categoria principal | Agêntico (LLM) | `orquestrar_analise` | `nodes.py` |
| Sintetizar causa raiz | Agêntico (LLM) | `gerar_causa_raiz` | `nodes.py` |
| Persistir relatório | Determinístico | `reports.py` | `reports.py` |

---

## Padrões de Testes

- `tests/fixtures/biotecpredict_teste.db` — arquivo estático, versionado,
  nunca usado pela aplicação em execução.
- `test_tools.py` — valida a janela de datas e a rejeição de formato
  inválido em `consultar_leituras_biosensor`.
- `test_graph.py` — roda o grafo completo via o harness de `main.py`
  (`rodar_investigacao_com_respostas`), sem subir servidor, com 11
  respostas fornecidas (6 Ishikawa + 5 porquês); cobre também o caso de
  "pedir ajuste" gerando um segundo ciclo.
- `test_config.py` — cadeia de fallback de LLM (Gemini → Groq → Anthropic →
  OpenAI) com provedores mockados (`pytest-mock`), nunca uma chamada real;
  cobre o caso de todos os provedores configurados falhando (`FalhaLLMError`).
- `test_backend.py` — rotas do `backend/main.py` via `TestClient`
  (`httpx`), com o grafo mockado onde precisa executar um nó agêntico; e o
  contrato `GET /openapi.json` validado com `openapi-spec-validator`.
- `frontend/src/**/*.test.tsx` (Vitest + React Testing Library) — cada
  componente principal (`ListaLotes`, `PerguntaAtual`, `RevisaoRespostas`)
  com pelo menos um teste de render e um de interação, `api.ts` mockado.
- `tests/e2e/tests/*.spec.ts` (Playwright) — fluxo completo pelo navegador contra
  backend + frontend reais (subidos pelo `webServer`), sempre com
  `LLM_PROVIDER=fake` e a fixture de teste.
- SQLite local (arquivo, não in-memory) — não há necessidade de um padrão
  de pool especial como no BiotecPredict, já que os testes usam um arquivo
  de fixture próprio, isolado do banco real.

---

## Restrições e Decisões Técnicas

- **Sem Clean Architecture em camadas completas** — separação por
  responsabilidade única (`models`, `state`, `config`, `tools`, `nodes`,
  `graph`, `reports` em `root_cause_agent/`, mais `backend/main.py` pra API)
  já satisfaz o rubric, sem overhead adicional (RNF5).
- **`backend/` separado de `root_cause_agent/`** — FastAPI só existe em
  `backend/`, que depende do motor do agente como biblioteca (nunca o
  contrário); mesma separação backend/frontend do BiotecPredict, e o que
  permite reusar o motor sem FastAPI em outro contexto.
- **Sem persistência de saída em banco** — o `Diagnostico` é salvo como
  arquivos (JSON+HTML); só a entrada (lotes/leituras) vem de SQLite.
- **Sem router nem lib de estado no frontend** — uma tela, um `useState`.
- **Human-in-the-loop via `interrupt()`, não `input()`** — obrigatório
  numa API web, que não pode bloquear esperando o navegador.
- **Nenhum limiar/nome de setor hardcoded** — tudo vem de `config/`
  (RNF3), validado na prática pelo próprio histórico do projeto (nasceu
  desenhado para agronegócio, foi reconfigurado para bioprocessos trocando
  só `config/` e `data/`).

---

## Ambiente de Desenvolvimento

Claude Code, com specs versionadas em `specs/` guiando a implementação —
ver `docs/prompts.md` para o histórico completo de decisões.
