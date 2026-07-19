"""Monta e compila o StateGraph. Ver nodes.py para os nós e specs/design.md
para o fluxo completo (Fase 1 Ishikawa -> orquestrar_analise -> Fase 2 5
Porquês)."""

from __future__ import annotations

import sqlite3

from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from root_cause_agent import models, nodes
from root_cause_agent.config import CHECKPOINT_DB_PATH
from root_cause_agent.state import AgentState
from root_cause_agent.tools import TOOLS


def build_graph(checkpoint_db_path: str | None = None):
    """Compila o grafo com um checkpointer SqliteSaver -- por padrão
    data/checkpoints.db (config.CHECKPOINT_DB_PATH), ou ":memory:"/outro
    caminho para testes/harness isolados."""
    g = StateGraph(AgentState)

    g.add_node("preparar_contexto", nodes.preparar_contexto)
    g.add_node("formular_pergunta_ishikawa", nodes.formular_pergunta_ishikawa)
    g.add_node("usar_ferramenta", ToolNode(TOOLS))
    g.add_node("perguntar_operador", nodes.perguntar_operador)
    g.add_node("avaliar_informatividade", nodes.avaliar_informatividade)
    g.add_node("orquestrar_analise", nodes.orquestrar_analise)
    g.add_node("formular_porque", nodes.formular_porque)
    g.add_node("gerar_causa_raiz", nodes.gerar_causa_raiz)

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

    g.add_edge("orquestrar_analise", "formular_porque")
    g.add_edge("gerar_causa_raiz", END)

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
