"""Ferramentas (tools) expostas ao LLM em formular_pergunta_ishikawa e
formular_porque, mais a validação determinística da resposta do operador.
Ver specs/design.md."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from root_cause_agent.config import DB_PATH
from root_cause_agent.state import AgentState

# Frases evasivas conhecidas que não respondem a pergunta de verdade --
# checagem exata (normalizada: minúsculas, sem espaços nas pontas), não uma
# classificação semântica ampla. "sim"/"não" isolados NÃO entram aqui: podem
# ser respostas curtas mas legítimas a uma pergunta binária -- se forem vagas
# demais no contexto, isso é papel da Camada 2 (avaliar_informatividade),
# não desta lista fixa.
RESPOSTAS_EVASIVAS_CONHECIDAS = {
    "não sei",
    "nao sei",
    "sei lá",
    "sei la",
    "não faço ideia",
    "nao faco ideia",
    "não lembro",
    "nao lembro",
    "não sabe",
    "nao sabe",
    "desconheço",
    "desconheco",
    "n/a",
    "na",
    "-",
}


def validar_resposta_operador(resposta: str) -> bool:
    """Camada 1 de validação (determinística) da resposta do operador em
    perguntar_operador: rejeita vazio/só espaço e uma lista fixa de frases
    evasivas conhecidas. Retorna True se a resposta pode seguir para a
    Camada 2 (julgamento de informatividade pelo LLM, em
    avaliar_informatividade).

    Deliberadamente uma função Python simples, não uma @tool vinculada ao
    LLM: decidir se uma string está vazia ou bate com uma lista fixa não
    exige julgamento de modelo, então não há razão para pagar uma chamada de
    LLM por isso -- mesmo princípio de separação workflow/agente do resto do
    grafo (ver specs/design.md § Por que isso é um agente).
    """
    texto = resposta.strip().lower()
    if not texto:
        return False
    return texto not in RESPOSTAS_EVASIVAS_CONHECIDAS


@tool
def consultar_leituras_biosensor(
    data_inicio: str,
    data_fim: str,
    state: Annotated[AgentState, InjectedState],
) -> str:
    """Consulta o histórico de leituras de biosensor (temperatura, pH,
    oxigênio dissolvido, pressão, velocidade do agitador) do lote sob
    investigação, numa janela de datas. Use para embasar uma pergunta com
    dado bruto quando a evidência agregada não for suficiente.

    Args:
        data_inicio: início da janela, formato ISO (ex: "2026-07-10T00:00:00").
        data_fim: fim da janela, formato ISO.
    """
    # batch_id vem do estado via InjectedState, não é um argumento que o
    # LLM controla -- o ToolNode injeta automaticamente na execução, e o
    # parâmetro nem aparece no schema exposto ao modelo. Isso trava a
    # consulta no lote da investigação em andamento (RNF2), em vez de
    # confiar no LLM para escolher o batch_id certo a cada chamada.
    batch_id = state["nc_input"].batch_id

    try:
        inicio = datetime.fromisoformat(data_inicio)
        fim = datetime.fromisoformat(data_fim)
    except ValueError:
        return (
            f"Datas inválidas: '{data_inicio}' / '{data_fim}'. Use formato "
            "ISO (ex: '2026-07-10T00:00:00')."
        )
    if inicio > fim:
        return f"data_inicio ({data_inicio}) é depois de data_fim ({data_fim}) -- inverta a janela."

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT temperature, ph, dissolved_oxygen, pressure, agitator_speed, recorded_at "
            "FROM sensor_readings WHERE batch_id = ? AND recorded_at BETWEEN ? AND ? "
            "ORDER BY recorded_at",
            (batch_id, data_inicio, data_fim),
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        return (
            f"Nenhuma leitura encontrada para o lote {batch_id} entre "
            f"{data_inicio} e {data_fim}."
        )

    linhas = [
        f"{r['recorded_at']}: temp={r['temperature']}C, pH={r['ph']}, "
        f"OD={r['dissolved_oxygen']}%, pressao={r['pressure']}bar, "
        f"agitador={r['agitator_speed']}RPM"
        for r in rows
    ]
    return f"{len(rows)} leituras do lote {batch_id}:\n" + "\n".join(linhas)


TOOLS = [consultar_leituras_biosensor]
