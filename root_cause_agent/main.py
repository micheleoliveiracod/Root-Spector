"""Harness de teste: roda o grafo inteiro com respostas fornecidas em
código (não interativo, sem servidor), para tests/test_graph.py validar o
agente sem precisar subir a API/frontend.

A interação real do operador acontece pela interface web (backend/main.py
+ frontend/), não por este módulo -- ver specs/design.md.
"""

from __future__ import annotations

from langgraph.types import Command

from root_cause_agent.graph import build_graph
from root_cause_agent.models import Diagnostico


def rodar_investigacao_com_respostas(
    batch_id: int,
    respostas: list[str],
    *,
    graph=None,
    ciclos_anteriores: list | None = None,
) -> tuple[Diagnostico, object]:
    """Roda o grafo do começo ao fim, respondendo cada interrupt() com a
    próxima resposta de `respostas` (na ordem -- 6 Ishikawa + 5 porquês,
    assumindo que cada resposta é informativa na 1ª tentativa). Usa um
    checkpointer em memória por padrão (build_graph(":memory:")).

    Retorna (diagnostico, graph): o `graph` devolvido permite rodar um
    segundo ciclo no mesmo thread_id (cenário de "pedir ajuste"), passando-o
    de volta como `graph=` e o diagnóstico anterior convertido em
    CicloAnterior via `ciclos_anteriores=[...]`.
    """
    if graph is None:
        graph = build_graph(":memory:")
    config = {"configurable": {"thread_id": str(batch_id)}}

    entrada: dict = {"batch_id": batch_id}
    if ciclos_anteriores is not None:
        entrada["ciclos_anteriores"] = ciclos_anteriores

    respostas_restantes = list(respostas)
    resultado = graph.invoke(entrada, config=config)
    while "__interrupt__" in resultado:
        resposta = respostas_restantes.pop(0)
        resultado = graph.invoke(Command(resume=resposta), config=config)

    return resultado["diagnostico"], graph
