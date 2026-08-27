"""Ferramentas (tools) expostas ao LLM em formular_pergunta_ishikawa e
formular_porque, mais a validação determinística da resposta do operador.
Ver specs/design.md."""

from __future__ import annotations

import sqlite3
import time
from datetime import datetime
from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from root_cause_agent.config import DB_PATH, REPORTS_DIR
from root_cause_agent.models import CasoSemelhante, Diagnostico
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

# Guardrail (Fase 2, governança, ver specs/fase02/design.md § Governança):
# limite de tamanho da resposta do operador. Nenhuma resposta legítima a
# uma pergunta de contexto (Ishikawa) ou de aprofundamento (5 Porquês)
# precisa de mais do que alguns parágrafos -- um valor muito acima disso é
# tratado como abuso (custo de contexto inflado, ou tentativa de
# sobrecarregar o prompt), não como uma resposta detalhada legítima.
TAMANHO_MAXIMO_RESPOSTA = 2000

# Guardrail (Fase 2, observabilidade, ver specs/fase02/design.md §
# Observabilidade): timeout explícito e retry na consulta SQL de
# consultar_leituras_biosensor, protegendo contra banco travado por outro
# processo ou arquivo corrompido (reforça RNF6) -- sem isso, a chamada
# ficaria bloqueada indefinidamente ou propagaria uma exceção crua pro
# LLM em vez de uma mensagem de erro tratável.
TIMEOUT_CONSULTA_SQL = 5.0  # segundos que o sqlite3 espera por um lock antes de desistir
MAX_TENTATIVAS_CONSULTA_SQL = 2
INTERVALO_ENTRE_TENTATIVAS = 0.5  # segundos, entre a 1ª e a última tentativa


def validar_resposta_operador(resposta: str) -> bool:
    """Camada 1 de validação (determinística) da resposta do operador em
    perguntar_operador: rejeita vazio/só espaço, resposta acima de
    TAMANHO_MAXIMO_RESPOSTA caracteres, e uma lista fixa de frases evasivas
    conhecidas. Retorna True se a resposta pode seguir para a Camada 2
    (julgamento de informatividade pelo LLM, em avaliar_informatividade).

    Deliberadamente uma função Python simples, não uma @tool vinculada ao
    LLM: decidir se uma string está vazia, longa demais ou bate com uma
    lista fixa não exige julgamento de modelo, então não há razão para
    pagar uma chamada de LLM por isso -- mesmo princípio de separação
    workflow/agente do resto do grafo (ver specs/design.md § Por que isso é
    um agente).
    """
    texto = resposta.strip().lower()
    if not texto:
        return False
    if len(resposta) > TAMANHO_MAXIMO_RESPOSTA:
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

    rows = None
    for tentativa in range(1, MAX_TENTATIVAS_CONSULTA_SQL + 1):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=TIMEOUT_CONSULTA_SQL)
            conn.row_factory = sqlite3.Row
            try:
                rows = conn.execute(
                    "SELECT temperature, ph, dissolved_oxygen, pressure, agitator_speed, "
                    "recorded_at FROM sensor_readings WHERE batch_id = ? "
                    "AND recorded_at BETWEEN ? AND ? ORDER BY recorded_at",
                    (batch_id, data_inicio, data_fim),
                ).fetchall()
            finally:
                conn.close()
            break
        except sqlite3.OperationalError as exc:
            if tentativa >= MAX_TENTATIVAS_CONSULTA_SQL:
                return (
                    f"Banco de dados indisponível (timeout de {TIMEOUT_CONSULTA_SQL:.0f}s "
                    f"excedido após {tentativa} tentativa(s)): {exc}. Tente novamente em instantes."
                )
            time.sleep(INTERVALO_ENTRE_TENTATIVAS)

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


def _diagnosticos_salvos(excluir_batch_id: int) -> list[Diagnostico]:
    """Lê e valida cada reports/*.json (config.REPORTS_DIR) como um
    Diagnostico, pulando arquivos que não existem/não parseiam (ex.
    relatório corrompido ou de um schema muito antigo) -- exclui o próprio
    lote em investigação, nunca compara um caso com ele mesmo."""
    if not REPORTS_DIR.exists():
        return []
    diagnosticos = []
    for caminho in sorted(REPORTS_DIR.glob("*.json")):
        try:
            diagnostico = Diagnostico.model_validate_json(caminho.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if diagnostico.nc.batch_id != excluir_batch_id:
            diagnosticos.append(diagnostico)
    return diagnosticos


def buscar_casos_semelhantes(state: AgentState) -> list[CasoSemelhante]:
    """Varre reports/*.json procurando investigações anteriores com a
    mesma categoria_principal e ao menos 1 parametro_fora_da_faixa em
    comum com o lote atual, excluindo o próprio lote -- compartilhada pela
    tool `consultar_recorrencia` (texto pro LLM) e por
    nodes.py::recomendar_tratativa (lista estruturada pro Diagnostico
    final), ver specs/fase02/design.md § Tool `consultar_recorrencia`."""
    categoria = state["categoria_principal"].categoria
    parametros_atuais = set(state["nc_input"].parametros_fora_da_faixa)
    batch_id_atual = state["nc_input"].batch_id

    semelhantes = []
    for diagnostico in _diagnosticos_salvos(batch_id_atual):
        mesma_categoria = diagnostico.categoria_principal.categoria == categoria
        parametros_em_comum = parametros_atuais & set(diagnostico.nc.parametros_fora_da_faixa)
        if mesma_categoria and parametros_em_comum:
            semelhantes.append(
                CasoSemelhante(
                    batch_id=diagnostico.nc.batch_id,
                    categoria_principal=diagnostico.categoria_principal.categoria,
                    causa_raiz=diagnostico.causa_raiz,
                    gerado_em=diagnostico.gerado_em,
                )
            )
    return semelhantes


@tool
def consultar_recorrencia(state: Annotated[AgentState, InjectedState]) -> str:
    """Verifica se esta não-conformidade já ocorreu antes, buscando em
    relatórios de investigações anteriores por casos com a mesma categoria
    Ishikawa principal e ao menos 1 parâmetro de biosensor fora da faixa em
    comum. Use antes de recomendar a tratativa, para informar no relatório
    se o caso é inédito ou recorrente."""
    # Assim como batch_id em consultar_leituras_biosensor, categoria e
    # parâmetros vêm do estado via InjectedState -- o LLM decide SE chama
    # a tool, não O QUE ela busca.
    casos = buscar_casos_semelhantes(state)
    if not casos:
        return "Nenhum caso semelhante encontrado -- esta não-conformidade parece inédita."
    linhas = [
        f"- Lote {c.batch_id} ({c.categoria_principal}, {c.gerado_em.date()}): {c.causa_raiz}"
        for c in casos
    ]
    return (
        f"{len(casos)} caso(s) semelhante(s) encontrado(s) em investigações anteriores:\n"
        + "\n".join(linhas)
    )


TOOLS = [consultar_leituras_biosensor]
