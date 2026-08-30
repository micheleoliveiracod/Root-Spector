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
    """Chamar 2x não duplica os handlers (stdout + banco) -- outros
    handlers podem estar presentes no logger (ex. o plugin de logging do
    pytest), então a checagem é pelo tipo do handler, não pela contagem
    total."""
    config.configurar_logging()
    config.configurar_logging()
    handlers_stdout = [
        h for h in logger_limpo.handlers if isinstance(h.formatter, config._FormatadorJSON)
    ]
    handlers_banco = [
        h for h in logger_limpo.handlers if isinstance(h, config._HandlerBancoDeDados)
    ]
    assert len(handlers_stdout) == 1
    assert len(handlers_banco) == 1


def test_configurar_logging_persiste_no_banco(logger_limpo):
    """O log estruturado também é gravado na tabela eventos_log
    (OBSERVABILIDADE_DB_PATH), não só em stdout -- é essa cópia em banco
    que o resumo diário (Fase 2, low-code) relê depois, já que stdout some
    quando o processo termina, e permite conectar uma ferramenta de BI
    direto no banco para análise estatística."""
    import sqlite3

    config.configurar_logging()
    config.log_no_executado("preparar_contexto", "thread-999", 512, 0.1)

    conn = sqlite3.connect(str(config.OBSERVABILIDADE_DB_PATH))
    conn.row_factory = sqlite3.Row
    linha = conn.execute(
        "SELECT * FROM eventos_log WHERE mensagem = 'no_executado' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()

    assert linha["no"] == "preparar_contexto"
    assert linha["batch_id"] == 512
    assert linha["thread_id"] == "thread-999"
    assert linha["duracao_s"] == 0.1


def test_handler_banco_usa_postgres_quando_database_url_definida(monkeypatch):
    """Issue #58 (specs/deploy-producao/plano.md): eventos_log vai para o
    Postgres da mesma instância do checkpointer quando DATABASE_URL
    estiver definida, não para o SQLite local -- sem conectar a um
    Postgres real, psycopg.connect é substituído por um dublê."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://usuario:senha@localhost/banco")

    comandos_executados = []

    class _ConexaoFake:
        def execute(self, sql, parametros=None):
            comandos_executados.append((sql, parametros))

    monkeypatch.setattr("psycopg.connect", lambda *args, **kwargs: _ConexaoFake())

    handler = config._HandlerBancoDeDados()

    assert handler._postgres is True
    assert handler._marcador == "%s"
    assert "CREATE TABLE IF NOT EXISTS eventos_log" in comandos_executados[0][0]
    assert "SERIAL PRIMARY KEY" in comandos_executados[0][0]

    registro = logging.LogRecord(
        name=config.NOME_LOGGER,
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="no_executado",
        args=(),
        exc_info=None,
    )
    registro.dados_estruturados = {
        "thread_id": "511",
        "batch_id": 511,
        "no": "preparar_contexto",
        "duracao_s": 1.5,
    }
    handler.emit(registro)

    sql_insercao, parametros = comandos_executados[1]
    assert "%s" in sql_insercao
    assert parametros[5] == "preparar_contexto"  # coluna "no"


def test_callback_llm_loga_sucesso_com_provedor_e_modelo(logger_limpo, capsys):
    """_CallbackObservabilidadeLLM (config.py) é o callback anexado à
    cadeia de fallback inteira em get_llm() -- aqui exercitado
    diretamente, sem precisar montar a cadeia real, simulando o ciclo de
    vida de 1 tentativa bem-sucedida (on_chat_model_start -> on_llm_end)."""
    config.configurar_logging()
    callback = config._CallbackObservabilidadeLLM()
    run_id = "run-1"
    serialized = {"id": ["langchain_google_genai", "chat_models", "ChatGoogleGenerativeAI"],
                  "kwargs": {"model": "gemini-2.5-flash"}}

    callback.on_chat_model_start(serialized, [[]], run_id=run_id)
    callback.on_llm_end(response=None, run_id=run_id)

    registro = json.loads(capsys.readouterr().out.strip())
    assert registro["mensagem"] == "chamada_llm"
    assert registro["provedor"] == "ChatGoogleGenerativeAI"
    assert registro["modelo"] == "gemini-2.5-flash"
    assert registro["sucesso"] is True
    assert registro["erro"] is None
    assert isinstance(registro["duracao_s"], float)


def test_callback_llm_loga_falha_antes_do_proximo_provedor_assumir(logger_limpo, capsys):
    """Quando uma tentativa falha (ex: Gemini atingiu limite de taxa), o
    callback registra sucesso=False com o erro, permitindo distinguir essa
    tentativa da que o próximo provedor da cadeia de fallback faz em
    seguida."""
    config.configurar_logging()
    callback = config._CallbackObservabilidadeLLM()
    run_id = "run-2"
    serialized = {
        "id": ["langchain_groq", "chat_models", "ChatGroq"],
        "kwargs": {"model": "llama-3.3-70b-versatile"},
    }

    callback.on_chat_model_start(serialized, [[]], run_id=run_id)
    callback.on_llm_error(RuntimeError("rate limit"), run_id=run_id)

    registro = json.loads(capsys.readouterr().out.strip())
    assert registro["provedor"] == "ChatGroq"
    assert registro["sucesso"] is False
    assert "rate limit" in registro["erro"]


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
