"""Issue #48 (specs/fase02/design.md § 4, sinal 1): logging estruturado
(JSON) em stdout, 1 registro por nó do grafo executado, com thread_id,
batch_id, nome do nó e duração. Sinal 2 (LANGSMITH_TRACING) não tem
código próprio para testar -- é lido diretamente pelo langsmith a partir
do ambiente, documentado em .env.example e docs/fase02/observabilidade/.
"""

from __future__ import annotations

import json
import logging

import pytest

from root_cause_agent import config
from root_cause_agent.main import rodar_investigacao_com_respostas

RESPOSTAS = [f"resposta {i}" for i in range(11)]


@pytest.fixture
def logger_limpo():
    """O handler de configurar_logging() prende uma referência ao
    sys.stdout vigente no momento da configuração -- para o capsys deste
    teste conseguir capturar a saída, o logger precisa ser reconfigurado
    depois que o capsys já substituiu sys.stdout (ou seja, dentro do
    teste, não antes). Remove qualquer handler herdado de um teste
    anterior e restaura o estado original ao final."""
    logger = logging.getLogger(config.NOME_LOGGER)
    handlers_originais = list(logger.handlers)
    nivel_original = logger.level
    logger.handlers.clear()
    yield logger
    logger.handlers.clear()
    logger.handlers.extend(handlers_originais)
    logger.setLevel(nivel_original)


def test_configurar_logging_emite_json_estruturado_por_no(logger_limpo, capsys):
    config.configurar_logging()
    config.log_no_executado("preparar_contexto", "thread-123", 511, 0.042)

    saida = capsys.readouterr().out.strip()
    registro = json.loads(saida)

    assert registro["no"] == "preparar_contexto"
    assert registro["thread_id"] == "thread-123"
    assert registro["batch_id"] == 511
    assert registro["duracao_s"] == 0.042
    assert registro["nivel"] == "INFO"
    assert "timestamp" in registro


def test_configurar_logging_e_idempotente(logger_limpo):
    """Chamar 2x não duplica o handler JSON -- outros handlers podem estar
    presentes no logger (ex. o plugin de logging do pytest), então a
    checagem é pelo tipo do formatter, não pela contagem total."""
    config.configurar_logging()
    config.configurar_logging()
    handlers_json = [
        h for h in logger_limpo.handlers if isinstance(h.formatter, config._FormatadorJSON)
    ]
    assert len(handlers_json) == 1


def test_ciclo_completo_emite_1_log_estruturado_por_no_executado(
    logger_limpo, capsys, fake_llm
):
    config.configurar_logging()

    rodar_investigacao_com_respostas(511, RESPOSTAS)

    linhas = capsys.readouterr().out.strip().splitlines()
    registros = [json.loads(linha) for linha in linhas if linha]
    nos_logados = {r["no"] for r in registros}

    # Nós executados exatamente 1 vez num ciclo sem "pedir ajuste".
    for no in (
        "preparar_contexto",
        "orquestrar_analise",
        "pre_busca_rag",
        "gerar_causa_raiz",
        "recomendar_tratativa",
    ):
        assert no in nos_logados

    # thread_id (config.configurable, injetado pelo LangGraph) e batch_id
    # (do próprio AgentState) aparecem em todo registro, não só no exemplo
    # isolado do teste acima.
    assert all(r["thread_id"] == "511" for r in registros)
    assert all(r["batch_id"] == 511 for r in registros)
    assert all(isinstance(r["duracao_s"], float) for r in registros)

    # formular_pergunta_ishikawa roda 1x por categoria (6) -- prova que o
    # log é por execução de nó, não um resumo único do ciclo inteiro.
    assert sum(1 for r in registros if r["no"] == "formular_pergunta_ishikawa") == 6
    # perguntar_operador roda 2x por pergunta (6 Ishikawa + 5 porquês): o
    # LangGraph reexecuta o nó do zero ao retomar de um checkpoint, então a
    # 1ª chamada levanta o GraphInterrupt (ainda logada, via o `finally` em
    # _com_log_estruturado) e a 2ª, após o resume, é quem de fato retorna.
    assert sum(1 for r in registros if r["no"] == "perguntar_operador") == 2 * len(RESPOSTAS)
