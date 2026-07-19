# CI/CD — Root-Spector

Convenção de integração contínua do projeto. Ver `specs/gitflow.md` para o
modelo de branches que esses workflows protegem, e `docs/gitflow.md` para o
status de implementação.

---

## Objetivo

Garantir que nenhum código quebrado chegue em `develop`/`main` — lint e
testes automatizados a cada push/PR, com o resultado visível antes de
qualquer merge.

Dado o tamanho do projeto (entrega individual, escopo deliberadamente
simples — RNF5), o pipeline é **um único workflow**, sem Docker, sem
cobertura mínima obrigatória: o objetivo é demonstrar o hábito de CI/CD do
Gitflow, não construir uma esteira de produção completa. O E2E automatizado
(decisão revista em 2026-07-18 — ver "Fora do escopo" abaixo) roda no mesmo
workflow, contra uma fixture e um LLM fake, nunca contra dados/provedores
reais.

---

## Workflow: CI — Lint & Testes

**Arquivo:** `.github/workflows/ci.yml` — implementado e verificado
localmente (`docs/gitflow.md` M4); commit/push formal ainda pendente, como
o resto do projeto além de M1.

**Dispara em:**
- `push` na branch `develop` (valida o estado da branch de integração após
  cada merge).
- `pull_request` com destino `develop` — cobre, na prática, qualquer PR
  vindo de `docs/*`, `chore/*`, `feature/*`, `test/*` ou `bugfix/*` (ver
  `specs/gitflow.md`), já que essas são as únicas branches que abrem PR
  contra `develop`.

Deliberadamente **não** dispara em `push` direto nas branches de trabalho
(`docs/*`, `chore/*`, `feature/*`, `test/*`, `bugfix/*`) — os testes só
rodam a partir da abertura do PR (evento `pull_request`, que também reroda
a cada novo commit no PR via `synchronize`), não a cada commit local ainda
sem PR. Também não dispara automaticamente em `release/*`/`main` nesta
entrega — ver "Regra de merge" abaixo.

```yaml
on:
  push:
    branches: [develop]
  pull_request:
    branches: [develop]
```

**Jobs:**

| Job | Ferramenta | O que valida |
|---|---|---|
| `lint` | `ruff check .` | Estilo e erros estáticos do Python |
| `test` | `pytest` | `tests/test_tools.py`, `tests/test_graph.py`, `tests/test_config.py` (fallback Gemini→Groq→Anthropic→OpenAI, mockado), `tests/test_backend.py` (rotas do `backend/main.py` via `TestClient` + contrato OpenAPI via `openapi-spec-validator`) — usando exclusivamente `tests/fixtures/biotecpredict_teste.db`, nunca `data/biotecpredict.db`, e sem chamar um provedor de LLM real |
| `frontend-test` | `npm run test` (Vitest + React Testing Library) | Componentes de `frontend/src/components/` (render + interação básica, `api.ts` mockado) |
| `e2e` | `npx playwright test` (`tests/e2e/`) | Fluxo completo pelo navegador: lista de lotes → 11 perguntas → revisão (com link do relatório já gerado) → pedir ajuste. Backend e frontend sobem automaticamente (`webServer` do `playwright.config.ts`), sempre contra a fixture de teste e um LLM fake (`LLM_PROVIDER=fake`) — roda igual local e no CI, mesmo comando |

**Passos (jobs Python — `lint`/`test`):** checkout → setup Python 3.11 →
`pip install -e ".[dev]"` → rodar a ferramenta.
**Passos (`frontend-test`):** checkout → setup Node 20 → `npm ci` em
`frontend/` → `npm run test`.
**Passos (`e2e`, depende de `test` e `frontend-test` passarem primeiro):**
checkout → setup Python 3.11 + Node 20 → instalar dependências dos três
pacotes (`root_cause_agent`+`backend`, `frontend/`, `tests/e2e/`) → instalar o
navegador do Playwright (`npx playwright install --with-deps chromium`) →
`npx playwright test`; em caso de falha, o relatório HTML do Playwright é
publicado como artefato do job.

**Regra de merge:** um PR de `docs/*`, `chore/*`, `feature/*`, `test/*` ou
`bugfix/*` para `develop` só é mergeado com o CI verde (automático, via o
workflow acima).
O merge de `release/*`/`hotfix/*` → `main` **não** dispara este workflow
nesta entrega — como o PR de origem já passou pelo CI ao entrar em
`develop`, a verificação em `main` fica manual (conferir que a branch de
release/hotfix não introduziu nada de novo além de ajustes finais). Sem
branch protection paga, toda regra de merge é seguida manualmente antes de
qualquer merge de qualquer forma — mas o workflow roda de verdade nos casos
acima e o resultado (✅/❌) fica visível no PR.

---

## Configuração

**`pyproject.toml`:**
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]
```

---

## Fora do escopo desta entrega

- Deploy automatizado (CD) — o projeto roda localmente, via `uvicorn` +
  `npm run dev` ou via `deploy/` (Docker + docker-compose, ver
  `specs/structure.md`); não há pipeline de CD nem ambiente de produção
  hospedado a publicar.
- Cobertura mínima obrigatória / Codecov — os critérios de aceitação
  (`specs/requirements.md`) definem o que precisa passar, não uma métrica
  de cobertura.
- Automação do Project Board via workflow (`add-to-project`/`move-card`) —
  a movimentação dos cards é manual (ver `specs/gitflow.md` § Kanban),
  já que é entrega individual e o volume de issues é pequeno.
- Chamada real a um provedor de LLM durante qualquer teste automatizado
  (unitário, de backend ou E2E) — sempre mockado/fake, tanto por custo
  quanto por determinismo no CI.

**Decisão revista em 2026-07-18:** a versão anterior deste documento listava
"testes E2E automatizados" como fora de escopo (verificação manual apenas).
Isso foi revertido — o job `e2e` (Playwright, tabela acima) agora roda de
verdade, local e no CI, com o mesmo comando.

---

## Como Usar

**Rodar localmente antes de push:**
```bash
ruff check .
pytest
npm run test --prefix frontend
npx playwright test --config tests/e2e/playwright.config.ts
```

**Visualizar status:** aba *Actions* do repositório, workflow "CI — Lint & Testes".

---

## Troubleshooting

1. Falha de lint → rodar `ruff check . --fix` localmente e revisar o diff.
2. Falha de teste (Python) → rodar `pytest -v` localmente; conferir se algum
   teste depende acidentalmente de `data/biotecpredict.db` em vez da fixture,
   ou de um provedor de LLM real em vez do mock/fake.
3. Falha de teste (frontend) → rodar `npm run test` dentro de `frontend/`;
   conferir se `api.ts` está mockado no teste, não chamando o backend real.
4. Falha de E2E → rodar `npx playwright test --debug` dentro de `tests/e2e/` pra
   abrir o trace viewer; no CI, baixar o artefato `playwright-report` do job
   que falhou. Confirmar que `LLM_PROVIDER=fake` está setado — sem isso a
   suíte tentaria chamar um provedor real.
5. CI não dispara → conferir se é um `push` em `develop` ou um `pull_request`
   com destino `develop`; push direto em qualquer branch de trabalho
   (`docs/*`/`chore/*`/`feature/*`/`test/*`/`bugfix/*`) não dispara nada —
   é preciso abrir o PR.
