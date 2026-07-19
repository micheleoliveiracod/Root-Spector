# Gitflow — Convenção do Projeto

Convenção estável de branches, commits e Pull Requests do Root-Spector. Ver
`docs/gitflow.md` para o plano operacional (milestones, branches concretas,
issues, status de execução) — este arquivo define **as regras**, aquele
aplica **as regras ao projeto**.

---

## Modelo de branches (oficial)

| Branch | Nasce de | Faz merge em | Convenção de nome |
|---|---|---|---|
| `main` | — | — | fixo |
| `develop` | `main` (uma vez, no início) | — | fixo |
| `docs/*` | `develop` | `develop` | `docs/<nome-descritivo>` |
| `chore/*` | `develop` | `develop` | `chore/<nome-descritivo>` |
| `feature/*` | `develop` | `develop` | `feature/<nome-descritivo>` |
| `test/*` | `develop` | `develop` | `test/<nome-descritivo>` |
| `bugfix/*` | `develop` | `develop` | `bugfix/<nome-descritivo>` |
| `release/*` | `develop` | `main` **e** `develop` | `release/<versao>` |
| `hotfix/*` | `main` | `main` **e** `develop` | `hotfix/<nome-descritivo>` |

- **`main`** — sempre entregável. `HEAD` reflete um estado
  pronto-para-produção (aqui: pronto-para-submissão). Só recebe merge de
  `release/*` ou `hotfix/*`.
- **`develop`** — branch de integração. `HEAD` reflete o estado mais
  recente do desenvolvimento para a próxima entrega. É onde o **CI roda a
  cada push/PR** (ver `specs/ci-cd.md`).
- **`docs/*`, `chore/*`, `feature/*`, `test/*`** — todas nascem de
  `develop`, voltam pra `develop` via PR com CI verde, são apagadas depois
  do merge. O prefixo segue o tipo predominante do conteúdo da branch, a
  mesma taxonomia da Convenção de commits abaixo: `docs/*` para
  specs/documentação, `chore/*` para configuração/infraestrutura de dados,
  `feature/*` para código novo do agente, `test/*` para testes e CI (ver a
  tabela em `docs/gitflow.md` para qual branch cobre qual milestone).
- **`bugfix/*`** — nasce de `develop`, volta pra `develop` via PR com CI
  verde, mesma regra das anteriores. Reservada pra corrigir um bug
  encontrado *durante o desenvolvimento* (antes de qualquer release) —
  separado do trabalho planejado dos milestones e de uma correção
  emergencial *depois* de já estar em produção (`hotfix/*`, que nasce de
  `main`, não de `develop`).
- **`release/*`** — nasce de `develop` quando o projeto estiver pronto pra
  ser entregue. Só correções finais pequenas e ajustes de documentação são
  permitidos aqui (nada de feature nova). Ao final, faz merge em **`main`
  e de volta em `develop`**, e recebe uma tag em `main` (ex:
  `v1.0-entrega`). **`main` nunca recebe commit ou push direto** — o merge
  é sempre via Pull Request (`release/*` → `main`), mesmo sendo entrega
  individual (checkpoint de autorrevisão antes de fechar, ver § Kanban).
- **`hotfix/*`** — só se algo quebrar depois de já ter ido pra `main`.
  Nasce de `main`, corrige, faz merge em **`main` e em `develop`**.

**Regra de merge:** sempre `--no-ff` (commit de merge explícito, sem
fast-forward e sem squash) — é assim que o Gitflow preserva no histórico o
formato de cada branch que existiu.

---

## Convenção de commits (Conventional Commits)

```
<tipo>(<escopo>): <descrição curta, no imperativo, minúscula>
```

- **Tipos:** `feat`, `fix`, `docs`, `test`, `chore`, `refactor`, `ci`,
  `style`, `build`, `perf`.
- **Escopo:** o milestone (`m1`…`m5`) ou o módulo afetado (`tools`,
  `graph`, `nodes`…) — o que for mais claro pro commit específico.
- **Exemplos:**
  - `feat(tools): implementa consultar_leituras_biosensor`
  - `fix(graph): corrige condição de parada do loop agente-ferramenta`
  - `chore(m2): adiciona gerador de fixture sintética para os testes`
  - `docs(m5): completa exemplos de entrada/saída no README`
  - `test(m4): adiciona teste de filtro de janela de datas`
  - `ci: adiciona workflow de lint e testes na develop`
- Commits pequenos e descritivos — nunca um único commit gigante por
  branch.

---

## Convenção de Pull Requests

- **Título:** mesmo padrão do commit — `<tipo>(<escopo>): <descrição>`.
- **Destino:** `docs/*`/`chore/*`/`feature/*`/`test/*`/`bugfix/*` →
  `develop`; `hotfix/*` → `main` (+ back-merge em `develop`); `release/*` →
  `main` (+ back-merge em `develop`).
- **Corpo do PR (template):**
  ```markdown
  ## Contexto
  Qual milestone/issue isso resolve.

  ## O que mudou
  Lista curta das mudanças.

  ## Como testar
  Comando(s) pra verificar localmente.

  ## Checklist
  - [ ] CI verde (lint + testes)
  - [ ] Critérios de aceitação relevantes em specs/requirements.md conferidos
  - [ ] docs/prompts.md atualizado se algum prompt novo foi usado
  ```
- **Merge:** `--no-ff`, nunca squash — mantém o histórico fiel ao Gitflow.

---

## Kanban (GitHub Projects, 4 colunas)

Nomes padrão do template do projeto (não renomeados — ver
`specs/ci-cd.md` § Fora do escopo):

`Backlog` → `In Progress` → `In Review` → `Done`

- **Backlog** — issue existe, ainda não começou.
- **In Progress** — branch de trabalho aberta (a partir de `develop`), código
  sendo escrito.
- **In Review** — PR aberto pra `develop`, CI rodando/verde; conferir
  contra os critérios de aceitação do `specs/requirements.md` e contra a
  issue antes de dar merge (checkpoint de autorrevisão, já que é entrega
  individual e o rubric é fixo, sem meio-termo).
- **Done** — PR mergeado em `develop` (ou, no passo final,
  `release/*` mergeado em `main`).

Cada issue vira um card, movido manualmente entre colunas conforme o
progresso (ver `specs/ci-cd.md` § Fora do escopo — sem automação de board
via workflow nesta entrega).
