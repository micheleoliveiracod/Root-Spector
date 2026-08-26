"""App FastAPI: expõe o grafo de `root_cause_agent` por HTTP pro frontend.

Roda com `uvicorn backend.main:app`. Rotas (ver specs/design.md § Interface
para o contrato completo):

  GET  /api/lotes                                  -- lista lotes elegíveis
  POST /api/investigacoes/{batch_id}/iniciar         -- cria/retoma thread_id,
                                                          roda até o 1º interrupt()
  POST /api/investigacoes/{thread_id}/responder       -- Command(resume=resposta);
                                                          ao concluir o ciclo (5º porquê),
                                                          já gera reports/*.json + *.html
  GET  /api/investigacoes/{thread_id}/revisao          -- cadeia Ishikawa + 5 Porquês
                                                          + links do relatório já gerado
  POST /api/investigacoes/{thread_id}/ajustar            -- arquiva ciclo, reabre um novo
  GET  /reports/{arquivo}                                 -- serve os relatórios estáticos

`iniciar` e `responder` são as únicas rotas que executam nós do grafo --
capturam `FalhaLLMError` (root_cause_agent.nodes) e respondem HTTP 503 com
"Serviço de IA indisponível, recarregue a página.", sem deixar a exceção
crua vazar pro frontend (ver specs/design.md § Tratamento de falha no LLM).
`responder` também captura `LimiteTentativasExcedidoError`
(root_cause_agent.nodes) e responde HTTP 429, guardrail contra um
operador ou cliente automatizado que insista em respostas rejeitadas pela
Camada 1 de validação indefinidamente (ver specs/fase02/design.md §
Governança).

CORS restrito via `CORS_ALLOWED_ORIGINS` (env var, lista separada por
vírgula; padrão `*` em desenvolvimento local) e limite de taxa
(`limitar_taxa`, dependency aplicada a toda a API, 20 requisições por
minuto por IP, sem efeito quando `LLM_PROVIDER=fake`) completam os
guardrails de governança desta fase (ver docs/GOVERNANCA.md).
"""

from __future__ import annotations

import os
import sqlite3
import time
from collections import defaultdict, deque
from datetime import UTC, datetime

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from langgraph.types import Command
from pydantic import BaseModel

from root_cause_agent.config import DB_PATH, REPORTS_DIR, carregar_regras_setor
from root_cause_agent.graph import build_graph
from root_cause_agent.models import CicloAnterior, Classification
from root_cause_agent.nodes import (
    FalhaLLMError,
    LimiteTentativasExcedidoError,
    calcular_sensor_metrics,
)
from root_cause_agent.reports import salvar_relatorio

MENSAGEM_LLM_INDISPONIVEL = "Serviço de IA indisponível, recarregue a página."
MENSAGEM_LIMITE_TENTATIVAS = (
    "Limite de respostas rejeitadas atingido para esta pergunta, "
    "investigação encerrada."
)
MENSAGEM_LIMITE_TAXA = "Limite de requisições excedido, tente novamente em instantes."

# Guardrail (Fase 2, governança, ver specs/fase02/design.md § Governança):
# limite de taxa por IP, aplicado a toda a API. Contador em memória por
# processo (sem dependência nova, sem infraestrutura externa), suficiente
# pro escopo deste projeto -- um deploy com múltiplos processos/réplicas
# precisaria de um contador compartilhado (ex: Redis), fora do escopo
# atual. Sem efeito quando LLM_PROVIDER=fake, sinal já usado em todo o
# projeto pra suíte de testes/E2E, que faz várias requisições em sequência
# sem intenção de abuso.
LIMITE_REQUISICOES_POR_JANELA = 20
JANELA_LIMITE_TAXA_SEGUNDOS = 60
_requisicoes_por_ip: dict[str, deque[float]] = defaultdict(deque)


def limitar_taxa(request: Request) -> None:
    if os.getenv("LLM_PROVIDER") == "fake":
        return
    ip = request.client.host if request.client else "desconhecido"
    agora = time.monotonic()
    janela = _requisicoes_por_ip[ip]
    while janela and agora - janela[0] > JANELA_LIMITE_TAXA_SEGUNDOS:
        janela.popleft()
    if len(janela) >= LIMITE_REQUISICOES_POR_JANELA:
        raise HTTPException(429, MENSAGEM_LIMITE_TAXA)
    janela.append(agora)


def _origens_cors() -> list[str]:
    origens = os.getenv("CORS_ALLOWED_ORIGINS", "*")
    if origens == "*":
        return ["*"]
    return [origem.strip() for origem in origens.split(",") if origem.strip()]


app = FastAPI(
    title="Root-Spector API",
    version="0.1.0",
    description=(
        "API local que expõe o agente LangGraph do Root-Spector "
        "(investigação de causa raiz de NC via Ishikawa + 5 Porquês). "
        "Contrato completo em `specs/design.md` § Interface; diagrama do "
        "fluxo em `docs/diagrama-fluxo.md`."
    ),
    dependencies=[Depends(limitar_taxa)],
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origens_cors(),
    allow_methods=["*"],
    allow_headers=["*"],
)

grafo = build_graph()


class RespostaOperador(BaseModel):
    resposta: str


def _config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def _classificar(score: float) -> Classification:
    thresholds = carregar_regras_setor()["classification_thresholds"]
    if score >= thresholds["acceptable_min"]:
        return Classification.ACCEPTABLE
    if score >= thresholds["warning_min"]:
        return Classification.WARNING
    return Classification.CRITICAL


def _payload_pergunta(thread_id: str, resultado: dict) -> dict:
    interrupcao = resultado["__interrupt__"][0].value
    return {"thread_id": thread_id, **interrupcao}


@app.get(
    "/api/lotes",
    tags=["lotes"],
    summary="Listar lotes classificados pelo BiotecPredict",
    description=(
        "Lê `batches` (status COMPLETED, compliance_score não nulo) e "
        "devolve cada lote com `classification` recalculada, `elegivel` "
        "(WARNING/CRITICAL) e `parametros_fora_da_faixa` (calculado a "
        "partir de `sensor_readings`, vazio para lotes ACCEPTABLE)."
    ),
)
def listar_lotes():
    regras = carregar_regras_setor()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT id, upload_date, status, compliance_score, risk_prediction "
            "FROM batches WHERE status = 'COMPLETED' AND compliance_score IS NOT NULL "
            "ORDER BY id"
        ).fetchall()

        lotes = []
        for r in rows:
            classification = _classificar(r["compliance_score"])
            elegivel = classification != Classification.ACCEPTABLE
            parametros_fora_da_faixa: list[str] = []
            if elegivel:
                leituras = conn.execute(
                    "SELECT temperature, ph, dissolved_oxygen, pressure, agitator_speed "
                    "FROM sensor_readings WHERE batch_id = ?",
                    (r["id"],),
                ).fetchall()
                _, parametros_fora_da_faixa = calcular_sensor_metrics(leituras, regras)
            lotes.append(
                {
                    "batch_id": r["id"],
                    "upload_date": r["upload_date"],
                    "compliance_score": r["compliance_score"],
                    "risk_prediction": r["risk_prediction"],
                    "classification": classification.value,
                    "elegivel": elegivel,
                    "parametros_fora_da_faixa": parametros_fora_da_faixa,
                }
            )
    finally:
        conn.close()
    return lotes


@app.post(
    "/api/investigacoes/{batch_id}/iniciar",
    tags=["investigacoes"],
    summary="Iniciar (ou retomar) a investigação de um lote",
    description=(
        "Cria/retoma o `thread_id` (= `batch_id`) e roda o grafo até o "
        "primeiro `interrupt()`. Resposta: `{thread_id, fase: 'ishikawa', "
        "categoria, pergunta, nc: {...}}`. Devolve 503 "
        f"('{MENSAGEM_LLM_INDISPONIVEL}') se todos os provedores de LLM "
        "configurados falharem."
    ),
)
def iniciar_investigacao(batch_id: int):
    thread_id = str(batch_id)
    try:
        resultado = grafo.invoke({"batch_id": batch_id}, config=_config(thread_id))
    except FalhaLLMError as exc:
        raise HTTPException(503, MENSAGEM_LLM_INDISPONIVEL) from exc
    return _payload_pergunta(thread_id, resultado)


@app.post(
    "/api/investigacoes/{thread_id}/responder",
    tags=["investigacoes"],
    summary="Enviar a resposta do operador à pergunta atual",
    description=(
        "`Command(resume=resposta)` — retoma o grafo a partir do "
        "`interrupt()` pausado. Se ainda houver perguntas, devolve a "
        "próxima (`{thread_id, fase, categoria|numero, pergunta, ...}`); "
        "ao concluir o 5º porquê, já gera `reports/*.json`+`.html` e "
        "devolve `{thread_id, status: 'pronto_para_revisao'}`. Devolve "
        f"503 ('{MENSAGEM_LLM_INDISPONIVEL}') se todos os provedores de "
        f"LLM configurados falharem, ou 429 ('{MENSAGEM_LIMITE_TENTATIVAS}') "
        "se o limite de respostas rejeitadas pela Camada 1 de validação for "
        "excedido (guardrail, ver root_cause_agent/nodes.py::MAX_TENTATIVAS_CAMADA_1)."
    ),
)
def responder(thread_id: str, corpo: RespostaOperador):
    try:
        resultado = grafo.invoke(Command(resume=corpo.resposta), config=_config(thread_id))
    except FalhaLLMError as exc:
        raise HTTPException(503, MENSAGEM_LLM_INDISPONIVEL) from exc
    except LimiteTentativasExcedidoError as exc:
        raise HTTPException(429, MENSAGEM_LIMITE_TENTATIVAS) from exc
    if "__interrupt__" in resultado:
        return _payload_pergunta(thread_id, resultado)

    json_path, html_path = salvar_relatorio(resultado["diagnostico"])
    grafo.update_state(
        _config(thread_id),
        {
            "relatorio_json": f"/reports/{json_path.name}",
            "relatorio_html": f"/reports/{html_path.name}",
        },
    )
    return {"thread_id": thread_id, "status": "pronto_para_revisao"}


@app.get(
    "/api/investigacoes/{thread_id}/revisao",
    tags=["investigacoes"],
    summary="Consultar o diagnóstico concluído para revisão",
    description=(
        "Devolve a cadeia Ishikawa + 5 Porquês, `categoria_principal`, "
        "`categorias_descartadas`, `causa_raiz`, `narrativa`, "
        "`recomendacao_tratativa` + `fontes_rag` (Fase 2, RAG) e os links "
        "`relatorio.json`/`relatorio.html` já gerados. Devolve 400 se o "
        "ciclo ainda não chegou à revisão (5º porquê ainda não "
        "respondido)."
    ),
)
def revisao(thread_id: str):
    estado = grafo.get_state(_config(thread_id)).values
    diagnostico = estado.get("diagnostico")
    if diagnostico is None:
        raise HTTPException(400, "Investigação ainda não chegou à revisão.")
    return {
        "thread_id": thread_id,
        "respostas_ishikawa": [r.model_dump() for r in diagnostico.respostas_ishikawa],
        "categoria_principal": diagnostico.categoria_principal.model_dump(),
        "categorias_descartadas": [c.model_dump() for c in diagnostico.categorias_descartadas],
        "cadeia_de_porques": [p.model_dump() for p in diagnostico.cadeia_de_porques],
        "causa_raiz": diagnostico.causa_raiz,
        "narrativa": diagnostico.narrativa,
        "recomendacao_tratativa": diagnostico.recomendacao_tratativa,
        "fontes_rag": diagnostico.fontes_rag,
        "relatorio": {
            "json": estado["relatorio_json"],
            "html": estado["relatorio_html"],
        },
    }


@app.post(
    "/api/investigacoes/{thread_id}/ajustar",
    tags=["investigacoes"],
    summary="Pedir ajuste — arquivar o ciclo atual e reabrir um novo",
    description=(
        "Move o diagnóstico atual para `ciclos_anteriores` (auditoria, "
        "nunca sobrescrito) e reinicia o grafo para o mesmo `batch_id`, "
        "devolvendo a 1ª pergunta do novo ciclo Ishikawa (mesmo formato de "
        "`iniciar`). Devolve 400 se não houver diagnóstico em revisão."
    ),
)
def ajustar(thread_id: str):
    estado = grafo.get_state(_config(thread_id)).values
    diagnostico = estado.get("diagnostico")
    if diagnostico is None:
        raise HTTPException(400, "Nenhum diagnóstico em revisão para ajustar.")

    ciclo = CicloAnterior(
        numero_ciclo=len(estado.get("ciclos_anteriores", [])) + 1,
        respostas_ishikawa=diagnostico.respostas_ishikawa,
        categoria_principal=diagnostico.categoria_principal,
        categorias_descartadas=diagnostico.categorias_descartadas,
        cadeia_de_porques=diagnostico.cadeia_de_porques,
        causa_raiz=diagnostico.causa_raiz,
        encerrado_em=datetime.now(UTC),
    )
    novos_ciclos = [*estado.get("ciclos_anteriores", []), ciclo]

    try:
        resultado = grafo.invoke(
            {"batch_id": int(thread_id), "ciclos_anteriores": novos_ciclos},
            config=_config(thread_id),
        )
    except FalhaLLMError as exc:
        raise HTTPException(503, MENSAGEM_LLM_INDISPONIVEL) from exc
    return _payload_pergunta(thread_id, resultado)


REPORTS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/reports", StaticFiles(directory=str(REPORTS_DIR)), name="reports")
