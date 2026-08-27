"""Monta e compila o StateGraph. Ver nodes.py para os nós e specs/design.md
para o fluxo completo (Fase 1 Ishikawa -> orquestrar_analise -> Fase 2 5
Porquês)."""

from __future__ import annotations

import sqlite3
import time
from typing import Optional

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from root_cause_agent import models, nodes
from root_cause_agent.config import CHECKPOINT_DB_PATH, configurar_logging, log_no_executado
from root_cause_agent.state import AgentState
from root_cause_agent.tools import TOOLS


def _com_log_estruturado(nome: str, no):
    """Envolve um nó (função simples ou um Runnable como ToolNode, que
    expõe .invoke em vez de ser diretamente chamável) para emitir 1 log
    estruturado por execução -- sinal 1 de observabilidade
    (specs/fase02/design.md § Observabilidade). O wrapper aceita
    `config: RunnableConfig` como 2º parâmetro, o que faz o LangGraph
    injetar automaticamente o config do invoke() em andamento (é de lá que
    vem thread_id, não do AgentState); o nó original continua recebendo só
    `state`, sem precisar mudar assinatura. GraphInterrupt (perguntar_operador
    pausando pra esperar o operador) propaga normalmente através do
    `finally` -- ainda assim gera um log, com a duração até a pausa."""
    chamar = no.invoke if hasattr(no, "invoke") else no

    def envolto(state: AgentState, config: Optional[RunnableConfig] = None) -> dict:  # noqa: UP045
        inicio = time.monotonic()
        try:
            return chamar(state)
        finally:
            duracao = time.monotonic() - inicio
            thread_id = ((config or {}).get("configurable") or {}).get("thread_id")
            log_no_executado(nome, thread_id, state.get("batch_id"), duracao)

    return envolto


def build_graph(checkpoint_db_path: str | None = None):
    """Compila o grafo com um checkpointer SqliteSaver -- por padrão
    data/checkpoints.db (config.CHECKPOINT_DB_PATH), ou ":memory:"/outro
    caminho para testes/harness isolados."""
    configurar_logging()
    g = StateGraph(AgentState)

    # Todo nó passa por _com_log_estruturado (sinal 1 de observabilidade,
    # specs/fase02/design.md § Observabilidade) -- 1 log por execução.
    nos = {
        "preparar_contexto": nodes.preparar_contexto,
        "formular_pergunta_ishikawa": nodes.formular_pergunta_ishikawa,
        "usar_ferramenta": ToolNode(TOOLS),
        "perguntar_operador": nodes.perguntar_operador,
        "avaliar_informatividade": nodes.avaliar_informatividade,
        "orquestrar_analise": nodes.orquestrar_analise,
        "formular_porque": nodes.formular_porque,
        "gerar_causa_raiz": nodes.gerar_causa_raiz,
        "pre_busca_rag": nodes.pre_busca_rag,
        "recomendar_tratativa": nodes.recomendar_tratativa,
    }
    for nome, no in nos.items():
        g.add_node(nome, _com_log_estruturado(nome, no))

    g.set_entry_point("preparar_contexto")
    g.add_edge("preparar_contexto", "formular_pergunta_ishikawa")

    g.add_conditional_edges(
        "formular_pergunta_ishikawa",
        tools_condition,
        {"tools": "usar_ferramenta", END: "perguntar_operador"},
    )
    g.add_conditional_edges(
        "formular_porque",
        tools_condition,
        {"tools": "usar_ferramenta", END: "perguntar_operador"},
    )
    g.add_conditional_edges(
        "usar_ferramenta",
        nodes.rotear_apos_ferramenta,
        {
            "formular_pergunta_ishikawa": "formular_pergunta_ishikawa",
            "formular_porque": "formular_porque",
        },
    )

    g.add_edge("perguntar_operador", "avaliar_informatividade")
    g.add_conditional_edges(
        "avaliar_informatividade",
        nodes.rotear_apos_avaliar,
        {
            "perguntar_operador": "perguntar_operador",
            "formular_pergunta_ishikawa": "formular_pergunta_ishikawa",
            "orquestrar_analise": "orquestrar_analise",
            "formular_porque": "formular_porque",
            "gerar_causa_raiz": "gerar_causa_raiz",
        },
    )

    # Fan-out: 2 ramos independentes a partir de orquestrar_analise
    # (categoria_principal já definida) -- formular_porque (loop dos 5
    # Porquês, com o operador) e pre_busca_rag (busca na base de
    # conhecimento, determinística, sem depender do loop). LangGraph
    # executa os 2 no mesmo superstep (paralelismo real, não disfarçado de
    # sequencial) -- ver specs/fase02/design.md § Grafo.
    #
    # NÃO existe aresta pre_busca_rag -> recomendar_tratativa: um join
    # explícito do LangGraph exige que os 2 ramos completem no mesmo
    # superstep, mas o ramo formular_porque atravessa vários interrupt()
    # (uma pergunta ao operador por vez, em invokes separados) enquanto
    # pre_busca_rag termina no primeiro superstep -- um join formal
    # dispararia recomendar_tratativa cedo demais, com o diagnóstico ainda
    # None (bug encontrado e corrigido nesta branch). candidatos_rag já
    # fica pronto no estado bem antes de gerar_causa_raiz terminar;
    # recomendar_tratativa só precisa ser sequencial depois dele.
    g.add_edge("orquestrar_analise", "formular_porque")
    g.add_edge("orquestrar_analise", "pre_busca_rag")
    g.add_edge("gerar_causa_raiz", "recomendar_tratativa")
    g.add_edge("recomendar_tratativa", END)

    path = checkpoint_db_path if checkpoint_db_path is not None else str(CHECKPOINT_DB_PATH)
    if path != ":memory:":
        CHECKPOINT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    # Os schemas Pydantic de models.py precisam estar na allowlist do
    # checkpointer -- sem isso, toda (de)serialização emite um aviso
    # "unregistered type" (e seria bloqueada numa versão futura do langgraph).
    modelos_permitidos = {("root_cause_agent.models", nome) for nome in models.__all__}
    serde = JsonPlusSerializer(allowed_msgpack_modules=modelos_permitidos)
    checkpointer = SqliteSaver(conn, serde=serde)

    return g.compile(checkpointer=checkpointer)
