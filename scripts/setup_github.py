#!/usr/bin/env python3
"""Automatiza SO a estrutura do GitHub do Root-Spector, conforme
docs/gitflow.md -- nenhum commit de codigo e feito por este script.

  0. validate_data(): checagem 100% local (sem chamada de rede) das
     estruturas abaixo -- milestone/label referenciado existe mesmo,
     titulo de issue nao duplicado, nenhum milestone com mais de 5 issues.
     Roda antes de qualquer coisa tocar o GitHub; para tudo (sem criar
     nada) se achar inconsistencia.
  1. Labels (5 de tipo + 6 de etapa).
  2. Milestones (M1-M5 + Release).
  3. Branch `develop` a partir de `main` (vazia -- so um ponteiro, sem
     commit novo).
  4. Branches de M1 a M5, cada uma vazia, criada a partir de `develop` e
     empurrada pro remoto (sem nenhum arquivo commitado -- o codigo em si
     e trabalho manual/de outra sessao, isso aqui e so a estrutura).
  5. 21 issues (no maximo 5 por milestone), agrupando itens relacionados
     do checklist detalhado de docs/gitflow.md numa unica issue. Cada
     issue segue o padrao convencional de Gitflow do projeto -- corpo
     estruturado em Contexto / Escopo / Criterios de Aceite / Branch (ver
     build_issue_body) -- e nasce com milestone + label de tipo + label de
     etapa. Tratadas de forma uniforme -- nenhuma menciona ou pressupoe
     que M1/M2/parte de M3 ja foram concluidas; toda issue nasce como se o
     trabalho ainda nao tivesse comecado.
  6. Board do GitHub Projects: adiciona cada issue criada como item do
     board, todas na coluna "Backlog" (nome padrao do projeto, nao
     renomeado por este script).

Por enquanto a conexao branch<->milestone<->issue
e via nomenclatura e a tabela em docs/gitflow.md; vira link nativo do
GitHub automaticamente assim que o PR de cada branch for aberto (mais
tarde, com o codigo de verdade).

Idempotente: confere labels/milestones/branches existentes antes de criar,
pode rodar de novo sem duplicar nada. Issues sao a excecao parcial -- se ja
existem (por titulo), o script nao duplica, mas RE-ESCREVE o corpo pra
bater com ISSUES/build_issue_body, entao editar o texto aqui e rodar de
novo e a forma correta de corrigir uma issue ja criada.

Requer `gh` autenticado (escopos repo + project) e `git` com origin
apontando pro repo, rodado a partir da raiz do repositorio Root-Spector.

Uso:
    python scripts/setup_github.py             # roda tudo, de verdade
    python scripts/setup_github.py --dry-run   # le o estado real, so simula as escritas
    python scripts/setup_github.py --branches  # tambem cria develop + branches vazias
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

OWNER = "micheleoliveiracod"
REPO = "Root-Spector"
REPO_FULL = f"{OWNER}/{REPO}"
PROJECT_NUMBER = 9

DRY_RUN = False


def run(cmd: list[str], check: bool = True, mutate: bool = False) -> str:
    """Leituras (mutate=False) sempre rodam de verdade, mesmo em --dry-run
    (sao inofensivas e o dry-run precisa do estado real). Escritas
    (mutate=True) so sao impressas em --dry-run."""
    if mutate and DRY_RUN:
        print(f"  [dry-run] {' '.join(cmd)}")
        return ""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"ERRO: {' '.join(cmd)}\n{result.stderr}", file=sys.stderr)
        raise SystemExit(1)
    return result.stdout.strip()


def gh_json(args: list[str], mutate: bool = False):
    out = run(["gh", *args], mutate=mutate)
    return json.loads(out) if out else None


# --------------------------------------------------------------- labels --

TYPE_LABELS = [
    ("docs", "0075ca", "Trabalho de documentacao/specs"),
    ("chore", "6f42c1", "Configuracao/infraestrutura, sem logica de produto"),
    ("feature", "0e8a16", "Codigo novo do agente"),
    ("test", "fbca04", "Testes automatizados/CI"),
    ("bugfix", "d93f0b", "Correcao de bug encontrado durante o desenvolvimento"),
]

STAGE_LABELS = [
    ("m1: especificação", "1d76db", "M1 - Especificacao & Arquitetura"),
    ("m2: dados & config", "0e8a16", "M2 - Dados & Configuracao"),
    ("m3: implementação", "5319e7", "M3 - Implementacao do Agente"),
    ("m4: testes", "fbca04", "M4 - Testes & Verificacao"),
    ("m5: documentação", "d93f0b", "M5 - Documentacao & Entrega"),
    ("release", "b60205", "Release"),
]


def ensure_labels() -> None:
    print("\n== Labels ==")
    for name, color, desc in TYPE_LABELS + STAGE_LABELS:
        print(f"  {name}")
        run(
            [
                "gh", "label", "create", name,
                "--repo", REPO_FULL,
                "--color", color,
                "--description", desc,
                "--force",
            ],
            mutate=True,
        )


# ----------------------------------------------------------- milestones --

MILESTONES = [
    ("M1 — Especificação & Arquitetura", "Specs, estrutura de pastas, stubs, docs iniciais."),
    ("M2 — Dados & Configuração", "config/regras_bioprocesso.yaml, confirmacao do schema real, fixture de teste."),
    ("M3 — Implementação do Agente", "models, state, config, tools, nodes, graph, reports, api, main, frontend."),
    ("M4 — Testes & Verificação", "test_tools.py, test_graph.py, test_config.py (fallback), test_backend.py (OpenAPI), testes de frontend, E2E (Playwright), CI."),
    ("M5 — Documentação & Entrega", "README completo, prompts.md final, slides revisados, checklist do rubric."),
    ("Release", "release/v1.0-entrega -> main, tag, back-merge, submissao no AVA."),
]


def ensure_milestones() -> None:
    print("\n== Milestones ==")
    existing = gh_json(["api", f"repos/{REPO_FULL}/milestones", "--paginate"]) or []
    existing_titles = {m["title"] for m in existing}
    for title, desc in MILESTONES:
        if title in existing_titles:
            print(f"  ja existe: {title}")
            continue
        print(f"  criando: {title}")
        run(
            [
                "gh", "api", f"repos/{REPO_FULL}/milestones",
                "-f", f"title={title}",
                "-f", f"description={desc}",
            ],
            mutate=True,
        )


# ------------------------------------------------------------- branches --
# Todas vazias -- so criadas e empurradas pro remoto, sem nenhum commit de
# arquivo. Release fica de fora: por definicao (docs/gitflow.md) so nasce
# depois que as 5 branches abaixo estiverem mergeadas em develop.

BRANCHES = [
    "docs/especificacao-e-arquitetura",
    "chore/dados-e-configuracao",
    "feature/implementacao-agente",
    "test/testes-e-verificacao",
    "docs/documentacao-final",
]


def branch_exists_remote(name: str) -> bool:
    out = run(["git", "ls-remote", "--heads", "origin", name], check=False)
    return bool(out.strip())


def ensure_develop() -> None:
    print("\n== develop ==")
    if branch_exists_remote("develop"):
        print("  ja existe no remoto")
        return
    print("  criando a partir de main (vazia, sem commit novo)")
    run(["git", "fetch", "origin", "main"], mutate=True)
    run(["git", "checkout", "-B", "develop", "origin/main"], mutate=True)
    run(["git", "push", "-u", "origin", "develop"], mutate=True)


def ensure_branches() -> None:
    print("\n== Branches de milestone ==")
    for name in BRANCHES:
        if branch_exists_remote(name):
            print(f"  ja existe: {name}")
            continue
        print(f"  criando {name} a partir de develop (vazia)")
        run(["git", "fetch", "origin", "develop"], mutate=True)
        run(["git", "checkout", "-B", name, "origin/develop"], mutate=True)
        run(["git", "push", "-u", "origin", name], mutate=True)
    run(["git", "checkout", "develop"], check=False, mutate=True)


# --------------------------------------------------------------- issues --
# TODOS os itens do checklist viram issue, de M1 a Release, tratadas de
# forma uniforme -- nenhuma cita ou pressupoe conclusao previa, mesmo pra
# M1/M2/parte de M3 (ja concluidas na arvore de trabalho, mas isso nao e
# mencionado aqui). Toda issue abre em Backlog, como se nada tivesse
# comecado ainda. Compactadas em no maximo 5 por milestone, agrupando
# itens relacionados do checklist detalhado de docs/gitflow.md numa unica
# issue. Cada issue segue o padrao convencional de Gitflow do projeto:
# Contexto / Escopo / Criterios de Aceite / Branch (ver build_issue_body).

STAGE_LABEL_BY_MILESTONE = {
    "M1 — Especificação & Arquitetura": "m1: especificação",
    "M2 — Dados & Configuração": "m2: dados & config",
    "M3 — Implementação do Agente": "m3: implementação",
    "M4 — Testes & Verificação": "m4: testes",
    "M5 — Documentação & Entrega": "m5: documentação",
    "Release": "release",
}

MILESTONE_BRANCH = {
    "M1 — Especificação & Arquitetura": "docs/especificacao-e-arquitetura",
    "M2 — Dados & Configuração": "chore/dados-e-configuracao",
    "M3 — Implementação do Agente": "feature/implementacao-agente",
    "M4 — Testes & Verificação": "test/testes-e-verificacao",
    "M5 — Documentação & Entrega": "docs/documentacao-final",
    "Release": "release/v1.0-entrega",
}


class Issue:
    def __init__(
        self,
        milestone: str,
        type_label: str | None,
        title: str,
        contexto: str,
        escopo: list[str],
        criterios: list[str],
    ) -> None:
        self.milestone = milestone
        self.type_label = type_label
        self.title = title
        self.contexto = contexto
        self.escopo = escopo
        self.criterios = criterios

    @property
    def branch(self) -> str:
        return MILESTONE_BRANCH[self.milestone]


def build_issue_body(issue: Issue) -> str:
    escopo_md = "\n".join(f"* {item}" for item in issue.escopo)
    criterios_md = "\n".join(f"* {item}" for item in issue.criterios)
    return (
        f"## Contexto\n{issue.contexto}\n\n"
        f"## Escopo\n{escopo_md}\n\n"
        f"## Critérios de Aceite\n{criterios_md}\n\n"
        f"## Branch\n`{issue.branch}`"
    )


ISSUES: list[Issue] = [
    # M1 -- Especificacao & Arquitetura (3)
    Issue(
        "M1 — Especificação & Arquitetura", "docs",
        "Estrutura de pastas, stubs do pacote e specs completas",
        "Base do projeto — organização de pastas e os documentos de especificação "
        "que orientam toda a implementação seguinte (requisitos, arquitetura, "
        "decisões técnicas).",
        [
            "Estrutura de pastas e stubs do pacote `root_cause_agent/`",
            "`specs/requirements.md` (requisitos funcionais e não-funcionais)",
            "`specs/design.md` (arquitetura, decisões técnicas, human-in-the-loop)",
            "`specs/product.md`, `specs/tech.md`, `specs/structure.md`, "
            "`specs/ci-cd.md`, `specs/gitflow.md`",
        ],
        [
            "Estrutura de pastas reflete `specs/structure.md`",
            "Todos os arquivos de `specs/` presentes, sem referência a escopo "
            "obsoleto (ex.: descrição genérica reaproveitada do BiotecPredict)",
            "`specs/requirements.md` cobre todos os RFs/RNFs do projeto",
        ],
    ),
    Issue(
        "M1 — Especificação & Arquitetura", "docs",
        "README.md inicial",
        "Ponto de entrada do repositório pra quem for avaliar o projeto — "
        "precisa situar rapidamente o que é o Root-Spector e sua relação com "
        "o BiotecPredict.",
        ["README.md inicial (esqueleto): visão geral, motivação, relação com o BiotecPredict"],
        [
            "README explica o que é o projeto e como se relaciona com o BiotecPredict em poucos parágrafos",
            "Estrutura pronta pra receber as seções finais em M5 (como executar, exemplo de saída)",
        ],
    ),
    Issue(
        "M1 — Especificação & Arquitetura", "docs",
        "Apresentação e plano operacional do Gitflow",
        "Necessário documentar o fluxo de trabalho (Gitflow) que será seguido "
        "durante toda a implementação, e ter um esqueleto de apresentação pra "
        "evoluir junto com o projeto.",
        [
            "`docs/apresentacao.md` (esqueleto)",
            "`docs/gitflow.md` (plano operacional: milestones, branches, issues, labels)",
        ],
        [
            "`docs/gitflow.md` conecta milestones ↔ branches ↔ issues ↔ labels sem lacunas",
            "`docs/apresentacao.md` tem a estrutura mínima pra ser preenchida em M5",
        ],
    ),
    # M2 -- Dados & Configuracao (2)
    Issue(
        "M2 — Dados & Configuração", "chore",
        "Configuração do setor e fixture de teste",
        "O agente precisa de regras de negócio (thresholds/faixas por sensor, "
        "categorias Ishikawa) e de uma base de dados determinística pros testes "
        "automatizados.",
        [
            "`config/regras_bioprocesso.yaml` (thresholds de classification, "
            "faixas por sensor, 6 categorias Ishikawa)",
            "`tests/fixtures/biotecpredict_teste.db` — fixture estática de teste, "
            "versionada (sem script gerador no projeto)",
        ],
        [
            "YAML cobre as faixas de todos os sensores usados no diagnóstico",
            "Fixture de teste é determinística — mesmos dados a cada execução dos testes",
        ],
    ),
    Issue(
        "M2 — Dados & Configuração", "chore",
        "Confirmar schema real via data/biotecpredict.db",
        "O agente lê o banco real de saída do BiotecPredict — é preciso confirmar "
        "que o schema documentado bate com o real antes de escrever o código de "
        "acesso a dados em M3.",
        ["Confirmação do schema real via `data/biotecpredict.db` (exportação real, não versionada)"],
        [
            "Schema documentado em `specs/design.md` bate com o schema real da tabela `sensor_readings`",
            "Casos de borda documentados (ex.: `compliance_score` nulo = lote não elegível)",
        ],
    ),
    # M3 -- Implementacao do Agente (5)
    Issue(
        "M3 — Implementação do Agente", "feature",
        "Schemas, estado e configuração (models, state, config, pyproject)",
        "Base de tipos e configuração compartilhada por todos os nós do grafo do agente.",
        [
            "`models.py` (schemas Pydantic: NaoConformidade, RespostaIshikawa, PorQue, Diagnostico, CicloAnterior)",
            "`state.py` (AgentState completo)",
            "`config.py` (seleção de LLM plugável via `init_chat_model` + fallback em cadeia Gemini → Groq → Anthropic → OpenAI)",
            "`pyproject.toml` com as dependências reais",
        ],
        [
            "Todos os schemas Pydantic validam os dados esperados sem erro",
            "`get_llm()` monta a cadeia de fallback corretamente quando as chaves opcionais estão ausentes do `.env`",
            "`pip install -e .` resolve sem conflito de dependências",
        ],
    ),
    Issue(
        "M3 — Implementação do Agente", "feature",
        "Ferramenta e validação da resposta do operador (tools.py)",
        "Ferramenta de leitura do biosensor que o agente chama durante a análise, "
        "e a primeira camada de validação da resposta do operador humano.",
        [
            "`consultar_leituras_biosensor` (SQL somente-leitura em `sensor_readings`, "
            "`batch_id` injetado do estado via `InjectedState` — não escolhido pelo LLM —, "
            "`data_inicio`/`data_fim` validadas)",
            "`validar_resposta_operador` — Camada 1 de validação (hard-reject de resposta vazia/evasiva)",
        ],
        [
            "Tool rejeita datas em formato inválido sem lançar exceção não tratada",
            "`batch_id` nunca é controlável pelo LLM, só vem do estado",
            "`validar_resposta_operador` rejeita respostas vazias e evasivas conhecidas",
        ],
    ),
    Issue(
        "M3 — Implementação do Agente", "feature",
        "Núcleo do grafo (nodes.py, graph.py)",
        "O coração do agente — os nós do grafo LangGraph e a montagem do fluxo "
        "com os dois loops (Ishikawa e 5 Porquês) e o checkpointer que sustenta "
        "o human-in-the-loop.",
        [
            "`nodes.py` (preparar_contexto, formular_pergunta_ishikawa, orquestrar_analise, "
            "formular_porque, perguntar_operador com `interrupt()` + Camada 1, "
            "avaliar_informatividade com Camada 2 — até 2 tentativas —, gerar_causa_raiz)",
            "`FalhaLLMError` capturada de forma uniforme em cada nó agêntico",
            "`graph.py` (StateGraph com os dois loops em sequência + checkpointer `SqliteSaver`)",
        ],
        [
            "Grafo compila sem erro e todos os nós estão conectados conforme `specs/design.md`",
            "`FalhaLLMError` é levantada de forma uniforme por todos os nós agênticos em caso de falha do LLM",
            "Checkpointer permite pausar em `interrupt()` e retomar via `Command(resume=...)`",
        ],
    ),
    Issue(
        "M3 — Implementação do Agente", "feature",
        "Relatórios e API (reports.py, api.py, main.py harness)",
        "Camada que expõe o agente pra fora: geração dos relatórios finais "
        "(`root_cause_agent/reports.py`) e a API que o frontend consome. A "
        "API vive num pacote próprio, `backend/` — separado de "
        "`root_cause_agent/`, que fica sem nenhuma dependência de FastAPI —, "
        "importando o motor do agente como biblioteca (ver `specs/design.md` "
        "§ Interface e `specs/structure.md` § backend/).",
        [
            "`root_cause_agent/reports.py` (Diagnostico → `reports/{batch_id}_{timestamp}.json` + `.html` via Jinja2)",
            "`backend/main.py` (FastAPI, pacote próprio: listar lotes, iniciar/responder/revisar/ajustar "
            "investigação — `responder` já gera o relatório ao concluir o ciclo —, servir relatórios; "
            "captura `FalhaLLMError` → HTTP 503)",
            "Converter `root_cause_agent/main.py` em harness de teste (roda o grafo com respostas fixas, sem servidor)",
        ],
        [
            "`reports.py` gera JSON e HTML válidos a partir de um `Diagnostico` de exemplo",
            "`backend/main.py` devolve HTTP 503 com a mensagem \"Serviço de IA indisponível, recarregue a página.\" quando `FalhaLLMError` é levantada",
            "`backend/` não é importado por `root_cause_agent/` em nenhuma direção — só o contrário",
            "`main.py` (harness) roda o grafo ponta a ponta com respostas fixas, sem subir servidor",
        ],
    ),
    Issue(
        "M3 — Implementação do Agente", "feature",
        "Scaffold frontend/ (React + TypeScript + Vite)",
        "Interface pra demonstração ao vivo: única tela que lista os lotes, "
        "conduz as perguntas ao operador e mostra o relatório final.",
        ["`frontend/` completo: lista de lotes → pergunta atual → revisão (já com o link do relatório)"],
        [
            "`npm run dev` sobe a aplicação sem erro",
            "Fluxo completo (lista → pergunta → revisão com link do relatório → pedir ajuste) navegável na tela",
        ],
    ),
    # M4 -- Testes & Verificação (5)
    Issue(
        "M4 — Testes & Verificação", "test",
        "Testes automatizados (test_tools.py, test_graph.py)",
        "Cobertura automatizada do comportamento crítico do agente antes da entrega, "
        "incluindo a cadeia de fallback de LLM — o agente não pode quebrar silenciosamente "
        "se um provedor cair.",
        [
            "`tests/test_tools.py` (janela de datas filtrada corretamente, usando a fixture sintética)",
            "`tests/test_graph.py` (via harness de `main.py`: roda o grafo com 11 respostas "
            "fornecidas — 6 Ishikawa + 5 porquês —, produz `Diagnostico` válido; cobre também "
            "o caso de \"pedir ajuste\" gerando um segundo ciclo)",
            "`tests/test_config.py` (cadeia de fallback Gemini → Groq → Anthropic → OpenAI, "
            "provedores mockados via `pytest-mock`, nunca uma chamada real; cobre o caso "
            "de todos os provedores configurados falhando → `FalhaLLMError`)",
        ],
        [
            "`pytest` passa 100% localmente",
            "`test_graph.py` cobre tanto o ciclo único quanto o caso de reabertura (\"ajustar\")",
            "`test_config.py` cobre pelo menos: só Gemini, Gemini+Groq, Gemini+Groq+Anthropic, "
            "os 4 provedores, e todos falhando",
        ],
    ),
    Issue(
        "M4 — Testes & Verificação", "test",
        "Testes do backend (FastAPI: rotas + contrato OpenAPI)",
        "`backend/main.py` expõe o grafo por HTTP — precisa de testes de contrato (rotas "
        "respondem como esperado) e de schema (OpenAPI gerado é válido e cobre as rotas "
        "documentadas em `specs/design.md`), sem depender de um LLM real.",
        [
            "`tests/test_backend.py` — `TestClient` (FastAPI) cobrindo as 6 rotas: "
            "`/api/lotes`, iniciar, responder, revisão, ajustar, `/reports/{arquivo}`",
            "Teste de contrato OpenAPI: `GET /openapi.json` válido "
            "(`openapi-spec-validator`) e cobre as 6 rotas documentadas",
            "Teste do caminho de erro: `FalhaLLMError` simulada → HTTP 503 com a mensagem "
            "\"Serviço de IA indisponível, recarregue a página.\"",
        ],
        [
            "Todas as rotas testadas retornam o status/schema esperado",
            "`/openapi.json` é um documento OpenAPI válido e cobre as 6 rotas",
            "Rota que aciona o LLM, com `FalhaLLMError` mockada, devolve HTTP 503 e a mensagem exata",
        ],
    ),
    Issue(
        "M4 — Testes & Verificação", "test",
        "Testes do frontend (componentes React)",
        "Garantir que a única tela do frontend (lista → pergunta → revisão com link do "
        "relatório) não quebra silenciosamente.",
        [
            "Configuração do Vitest + React Testing Library em `frontend/`",
            "Testes de `ListaLotes`, `PerguntaAtual`, `RevisaoRespostas` "
            "(render + interação básica, `api.ts` mockado)",
        ],
        [
            "`npm run test` passa 100% localmente e no CI",
            "Cada componente principal tem pelo menos 1 teste de render e 1 de interação",
        ],
    ),
    Issue(
        "M4 — Testes & Verificação", "test",
        "Verificação local (pytest + aplicação ponta a ponta)",
        "Verificação ponta a ponta real — subir backend (uvicorn) + frontend (vite), rodar "
        "uma investigação completa pelo navegador (headless), incluindo o caso de \"pedir "
        "ajuste\", e conferir que o relatório final é gerado. Roda igual local e no CI, "
        "mesmo comando — nunca contra um provedor de LLM real nem `data/biotecpredict.db`.",
        [
            "Playwright configurado em `tests/e2e/` (Node, pacote próprio, `webServer` sobe "
            "backend + frontend automaticamente)",
            "Cenário principal: escolher lote elegível → responder as 11 perguntas → "
            "revisar → conferir link do relatório já gerado",
            "Cenário de ajuste: revisar → pedir ajuste → novo ciclo → conferir "
            "`ciclos_anteriores` no relatório do novo ciclo",
        ],
        [
            "`npx playwright test` passa 100% localmente",
            "Mesmo comando roda verde no GitHub Actions (job `e2e` em `ci.yml`)",
            "Suíte nunca toca `data/biotecpredict.db` nem chama um provedor de LLM real "
            "(usa a fixture de teste e `LLM_PROVIDER=fake`)",
        ],
    ),
    Issue(
        "M4 — Testes & Verificação", "test",
        "Workflow de CI (.github/workflows/ci.yml)",
        "Verificação automática a cada push/PR pra `develop`, conforme `specs/ci-cd.md`: "
        "lint, testes do agente/backend, testes do frontend e E2E, tudo num único workflow.",
        [
            "Job `lint`: `ruff check .`",
            "Job `test`: `pytest` (`test_tools.py`, `test_graph.py`, `test_config.py`, `test_backend.py`)",
            "Job `frontend-test`: `npm run test` (Vitest) em `frontend/`",
            "Job `e2e`: sobe backend+frontend e roda `npx playwright test` em `tests/e2e/`",
        ],
        [
            "Os 4 jobs rodam em todo push/PR pra `develop` e ficam visíveis no PR",
            "Nenhum job depende de credenciais reais de LLM (usa fixture + mocks/fake pro fallback)",
        ],
    ),
    # M5 -- Documentação & Entrega (3)
    Issue(
        "M5 — Documentação & Entrega", "docs",
        "README completo + checklist final do rubric",
        "Documentação final de entrega — o README precisa estar completo, e o "
        "projeto conferido contra todo o rubric antes da submissão.",
        [
            "Preencher as seções pendentes do README (como executar, exemplo real de saída)",
            "Checklist final contra o rubric completo",
        ],
        [
            "README permite a qualquer pessoa rodar o projeto do zero seguindo só as instruções",
            "Todo item do rubric conferido e sem pendência",
        ],
    ),
    Issue(
        "M5 — Documentação & Entrega", "docs",
        "Revisar docs/apresentacao.md",
        "Revisão final do material de apresentação ao professor.",
        ["Revisão final dos slides"],
        ["Slides refletem o estado real e final do projeto, sem informação desatualizada"],
    ),
    Issue(
        "M5 — Documentação & Entrega", "docs",
        "Issue final: subir docs/prompts.md completo",
        "Log de decisões do projeto — só fica completo depois que todo o resto "
        "foi feito, por isso fecha por último.",
        ["Registro completo de todos os prompts do projeto, do M1 ao M5"],
        ["`docs/prompts.md` cobre cronologicamente todas as decisões do M1 ao M5, sem lacuna"],
    ),
    # Release (3)
    Issue(
        "Release", None,
        "Abrir release/v1.0-entrega e conferir CI verde",
        "Passo final antes da entrega — a branch de release isola os últimos "
        "ajustes de documentação, sem código novo, e confirma que o CI está "
        "verde antes de abrir o PR pra `main`.",
        [
            "Abrir `release/v1.0-entrega` a partir de `develop`",
            "Só ajustes finais de documentação (nenhuma feature nova)",
            "Conferir CI verde na branch de release",
        ],
        [
            "CI verde em `release/v1.0-entrega`",
            "Nenhum commit de feature nova nessa branch, só ajustes finais",
        ],
    ),
    Issue(
        "Release", None,
        "Merge em main + tag v1.0-entrega + back-merge em develop",
        "O merge em `main` acontece exclusivamente por Pull Request, nunca por "
        "commit ou push direto — `main` só recebe código já revisado e com CI "
        "verde, mesmo sendo entrega individual (checkpoint de autorrevisão, ver "
        "`specs/gitflow.md` § Kanban).",
        [
            "Abrir PR `release/v1.0-entrega` → `main`, revisar e mergear com `--no-ff`",
            "Criar tag `v1.0-entrega` em `main` após o merge",
            "Back-merge de `release/v1.0-entrega` em `develop`, também via PR",
        ],
        [
            "Nenhum commit ou push direto em `main` — todo o conteúdo chega via PR mergeado",
            "Tag `v1.0-entrega` existe em `main` apontando pro commit de merge",
            "`develop` recebe o back-merge, sem divergir de `main`",
        ],
    ),
    Issue(
        "Release", None,
        "Submissão do link do repositório no AVA",
        "Passo administrativo final da entrega do curso.",
        [
            "Conferir que `main` está no estado de entrega (tag `v1.0-entrega`)",
            "Submeter o link do repositório no AVA",
        ],
        ["Link submetido aponta pra `main` na tag `v1.0-entrega`"],
    ),
]


def validate_data() -> None:
    """Checagem 100% local (nenhuma chamada de rede) das estruturas acima,
    antes de qualquer coisa tocar o GitHub -- pega erro de copiar/colar
    (milestone com nome errado, label que nao existe, titulo duplicado)
    antes de criar qualquer issue de verdade. Uma issue criada errada nao
    da pra desfazer sem sujeira; esta checagem e a rede de seguranca."""
    errors: list[str] = []

    milestone_titles = {m[0] for m in MILESTONES}
    type_label_names = {t[0] for t in TYPE_LABELS}
    stage_label_names = {s[0] for s in STAGE_LABELS}

    if set(STAGE_LABEL_BY_MILESTONE) != milestone_titles:
        missing = milestone_titles - set(STAGE_LABEL_BY_MILESTONE)
        extra = set(STAGE_LABEL_BY_MILESTONE) - milestone_titles
        if missing:
            errors.append(f"STAGE_LABEL_BY_MILESTONE sem entrada pra: {missing}")
        if extra:
            errors.append(f"STAGE_LABEL_BY_MILESTONE com milestone que nao existe em MILESTONES: {extra}")

    for name in STAGE_LABEL_BY_MILESTONE.values():
        if name not in stage_label_names:
            errors.append(f"STAGE_LABEL_BY_MILESTONE aponta pra label de etapa inexistente: {name!r}")

    per_milestone_count: dict[str, int] = {}
    seen_titles: set[str] = set()
    for issue in ISSUES:
        if issue.milestone not in milestone_titles:
            errors.append(f"issue {issue.title!r} referencia milestone inexistente: {issue.milestone!r}")
        if issue.type_label is not None and issue.type_label not in type_label_names:
            errors.append(f"issue {issue.title!r} referencia label de tipo inexistente: {issue.type_label!r}")
        if issue.milestone not in MILESTONE_BRANCH:
            errors.append(f"issue {issue.title!r} referencia milestone sem branch em MILESTONE_BRANCH: {issue.milestone!r}")
        if not issue.escopo:
            errors.append(f"issue {issue.title!r} sem escopo")
        if not issue.criterios:
            errors.append(f"issue {issue.title!r} sem criterios de aceite")
        if issue.title in seen_titles:
            errors.append(f"titulo de issue duplicado dentro de ISSUES: {issue.title!r}")
        seen_titles.add(issue.title)
        per_milestone_count[issue.milestone] = per_milestone_count.get(issue.milestone, 0) + 1

    for milestone_title, count in per_milestone_count.items():
        if count > 5:
            errors.append(f"{milestone_title!r} tem {count} issues, mais que o limite de 5")

    branch_names = [b for b in BRANCHES]
    if len(branch_names) != len(set(branch_names)):
        errors.append("BRANCHES tem nome duplicado")

    if errors:
        print("\n== Validação local (antes de tocar o GitHub) ==")
        for e in errors:
            print(f"  ERRO: {e}")
        print(f"\n{len(errors)} erro(s) de estrutura encontrado(s) -- nada foi criado. Corrija ISSUES/MILESTONES/labels e rode de novo.")
        raise SystemExit(1)
    print("\n== Validação local: OK ==")
    print(f"  {len(ISSUES)} issues planejadas, {max(per_milestone_count.values())} no maior milestone")


def existing_issues_by_title() -> dict[str, int]:
    data = gh_json(
        [
            "issue", "list", "--repo", REPO_FULL, "--state", "all",
            "--limit", "300", "--json", "number,title",
        ]
    ) or []
    return {i["title"]: i["number"] for i in data}


def ensure_issues() -> list[str]:
    """Cria as issues que ainda nao existem e sincroniza o corpo (Contexto /
    Escopo / Criterios de Aceite / Branch) das que ja existem, pra ISSUES
    continuar sendo a fonte da verdade mesmo depois de editar o texto.
    Retorna as URLs das issues CRIADAS nesta execucao (as sincronizadas nao
    entram na lista -- ja devem estar no board de uma execucao anterior)."""
    print("\n== Issues ==")
    existing = existing_issues_by_title()
    created: list[str] = []
    for issue in ISSUES:
        labels = [STAGE_LABEL_BY_MILESTONE[issue.milestone]]
        if issue.type_label:
            labels.append(issue.type_label)
        body = build_issue_body(issue)
        if issue.title in existing:
            number = existing[issue.title]
            print(f"  sincronizando corpo: #{number} {issue.title}")
            run(
                ["gh", "issue", "edit", str(number), "--repo", REPO_FULL, "--body", body],
                mutate=True,
            )
            continue
        print(f"  criando: {issue.title}  [{issue.milestone}]  labels={labels}")
        url = run(
            [
                "gh", "issue", "create",
                "--repo", REPO_FULL,
                "--title", issue.title,
                "--body", body,
                "--milestone", issue.milestone,
                "--label", ",".join(labels),
            ],
            mutate=True,
        )
        if url:
            created.append(url)
    return created


# ----------------------------------------------------------------- board --

def get_project_and_status_field() -> tuple[str, dict]:
    proj = gh_json(["project", "view", str(PROJECT_NUMBER), "--owner", OWNER, "--format", "json"])
    fields = gh_json(["project", "field-list", str(PROJECT_NUMBER), "--owner", OWNER, "--format", "json"])
    status_field = next(f for f in fields["fields"] if f["name"] == "Status")
    return proj["id"], status_field


def add_issues_to_board(issue_urls: list[str], status_field: dict) -> None:
    if not issue_urls:
        return
    print("\n== Board: adicionar issues (Backlog) ==")
    project_id, refreshed_status_field = get_project_and_status_field()
    backlog_id = next(
        (o["id"] for o in refreshed_status_field["options"] if o["name"] == "Backlog"),
        next(o["id"] for o in status_field["options"] if o["name"] == "Backlog"),
    )

    for url in issue_urls:
        print(f"  {url}")
        item = gh_json(
            ["project", "item-add", str(PROJECT_NUMBER), "--owner", OWNER, "--url", url, "--format", "json"],
            mutate=True,
        )
        item_id = item["id"] if item else "<dry-run-item-id>"
        run(
            [
                "gh", "project", "item-edit",
                "--id", item_id,
                "--project-id", project_id,
                "--field-id", refreshed_status_field["id"],
                "--single-select-option-id", backlog_id,
            ],
            mutate=True,
        )


# ------------------------------------------------------------------ main --

def main() -> None:
    global DRY_RUN
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="le o estado real, so simula as escritas")
    parser.add_argument(
        "--branches",
        action="store_true",
        help="tambem cria develop + as 5 branches de milestone (vazias, sem commit). "
        "Por padrao NAO roda -- so labels, milestones, issues (conectadas a "
        "milestone+label na criacao) e o board.",
    )
    args = parser.parse_args()
    DRY_RUN = args.dry_run

    validate_data()  # 100% local, roda mesmo sem --dry-run, antes de tocar o GitHub

    if DRY_RUN:
        print("*** DRY RUN — nenhuma escrita sera feita, so leituras reais pra planejar ***")

    ensure_labels()
    ensure_milestones()

    if args.branches:
        ensure_develop()
        ensure_branches()
    else:
        print("\n== Branches ==\n  pulando (rode com --branches pra criar develop + branches vazias)")

    _, status_field = get_project_and_status_field()

    # cada issue ja nasce conectada ao milestone (--milestone) e a label
    # de tipo + etapa (--label) no momento da criacao -- ver ensure_issues()
    created_issues = ensure_issues()
    add_issues_to_board(created_issues, status_field)

    print("\nConcluido.")


if __name__ == "__main__":
    main()
