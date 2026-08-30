"""Configuração e composição: .env, seleção de LLM plugável, caminhos dos
bancos e carga das regras do setor. Ver specs/design.md."""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import sys
import threading
import time
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "config" / "regras_bioprocesso.yaml"
DB_PATH = Path(os.getenv("BIOTECPREDICT_DB_PATH", str(REPO_ROOT / "data" / "biotecpredict.db")))
CHECKPOINT_DB_PATH = Path(
    os.getenv("CHECKPOINT_DB_PATH", str(REPO_ROOT / "data" / "checkpoints.db"))
)
# Persistência em banco do log estruturado (além de stdout), usada pelo
# resumo diário (Fase 2, low-code, specs/fase02/design.md § Low-code) para
# agregar eficiência operacional depois do fato, e para permitir conectar
# uma ferramenta de BI direto no banco para análise estatística -- stdout
# sozinho some quando o processo termina, e um arquivo .jsonl não é
# consultável por SQL. SQLite local por padrão, mesma instância de
# Postgres do checkpointer (issue de deploy, Azure) quando configurada em
# produção.
OBSERVABILIDADE_DB_PATH = Path(
    os.getenv("OBSERVABILIDADE_DB_PATH", str(REPO_ROOT / "data" / "observabilidade.db"))
)

# Observabilidade (Fase 2, specs/fase02/design.md § Observabilidade) --
# sinal 1: logging estruturado (JSON), 1 registro por nó do grafo
# executado (thread_id, batch_id, nome do nó, duração). Sinal 2: trace do
# LangSmith, ativado via a env var opcional LANGSMITH_TRACING (lida
# diretamente pelo langsmith/langchain-core a partir do ambiente, sem
# código adicional aqui além do load_dotenv() já existente -- ver .env.example.
NOME_LOGGER = "root_cause_agent"


class _FormatadorJSON(logging.Formatter):
    """1 linha de JSON por registro, usada só no handler de stdout (leitura
    humana em runtime) -- sem dependência nova (stdlib logging), ver
    specs/fase02/design.md § Observabilidade. A persistência consultável
    (para o resumo diário e para análise estatística externa) é o banco,
    ver _HandlerBancoDeDados."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "nivel": record.levelname,
            "mensagem": record.getMessage(),
        }
        payload.update(getattr(record, "dados_estruturados", {}))
        return json.dumps(payload, ensure_ascii=False)


_SQL_CRIAR_TABELA_EVENTOS_LOG_SQLITE = """
CREATE TABLE IF NOT EXISTS eventos_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    nivel TEXT NOT NULL,
    mensagem TEXT NOT NULL,
    thread_id TEXT,
    batch_id INTEGER,
    no TEXT,
    duracao_s REAL,
    provedor TEXT,
    modelo TEXT,
    sucesso INTEGER,
    erro TEXT
)
"""

_SQL_CRIAR_TABELA_EVENTOS_LOG_POSTGRES = """
CREATE TABLE IF NOT EXISTS eventos_log (
    id SERIAL PRIMARY KEY,
    timestamp TEXT NOT NULL,
    nivel TEXT NOT NULL,
    mensagem TEXT NOT NULL,
    thread_id TEXT,
    batch_id INTEGER,
    no TEXT,
    duracao_s DOUBLE PRECISION,
    provedor TEXT,
    modelo TEXT,
    sucesso BOOLEAN,
    erro TEXT
)
"""

_COLUNAS_EVENTOS_LOG = (
    "timestamp",
    "nivel",
    "mensagem",
    "thread_id",
    "batch_id",
    "no",
    "duracao_s",
    "provedor",
    "modelo",
    "sucesso",
    "erro",
)


class _HandlerBancoDeDados(logging.Handler):
    """Grava cada registro estruturado como 1 linha na tabela `eventos_log`,
    em vez de um arquivo .jsonl -- permite conectar uma ferramenta de BI
    direto no banco para análise estatística, não só reler um resumo já
    calculado (ver root_cause_agent/resumo_diario.py). SQLite local
    (OBSERVABILIDADE_DB_PATH) por padrão; Postgres, a mesma instância do
    checkpointer (ver graph.py::_criar_checkpointer), quando `DATABASE_URL`
    estiver definida (deploy, Azure Database for PostgreSQL). Conexão
    aberta 1 vez, com check_same_thread=False no caso SQLite porque o
    LangGraph roda nós em threads diferentes durante o fan-out paralelo
    (ver graph.py); um lock protege as escritas concorrentes."""

    def __init__(self) -> None:
        super().__init__()
        self._lock_escrita = threading.Lock()
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            import psycopg

            self._postgres = True
            self._marcador = "%s"
            self._conexao = psycopg.connect(database_url, autocommit=True)
            self._conexao.execute(_SQL_CRIAR_TABELA_EVENTOS_LOG_POSTGRES)
        else:
            self._postgres = False
            self._marcador = "?"
            OBSERVABILIDADE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            self._conexao = sqlite3.connect(
                str(OBSERVABILIDADE_DB_PATH), check_same_thread=False
            )
            self._conexao.execute(_SQL_CRIAR_TABELA_EVENTOS_LOG_SQLITE)
            self._conexao.commit()

    def emit(self, record: logging.LogRecord) -> None:
        dados = getattr(record, "dados_estruturados", {})
        sucesso = dados.get("sucesso")
        linha = (
            datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            record.levelname,
            record.getMessage(),
            dados.get("thread_id"),
            dados.get("batch_id"),
            dados.get("no"),
            dados.get("duracao_s"),
            dados.get("provedor"),
            dados.get("modelo"),
            None if sucesso is None else bool(sucesso) if self._postgres else int(sucesso),
            dados.get("erro"),
        )
        marcadores = ", ".join([self._marcador] * len(_COLUNAS_EVENTOS_LOG))
        sql = (
            f"INSERT INTO eventos_log ({', '.join(_COLUNAS_EVENTOS_LOG)}) "
            f"VALUES ({marcadores})"
        )
        with self._lock_escrita:
            self._conexao.execute(sql, linha)
            if not self._postgres:
                self._conexao.commit()


def configurar_logging() -> logging.Logger:
    """Configura o logger `root_cause_agent` com saída JSON em stdout
    (leitura humana em runtime) e em OBSERVABILIDADE_DB_PATH (banco,
    consultável por SQL e pelo resumo diário) -- idempotente (chamar de
    novo não duplica os handlers), chamado no startup de graph.py e
    backend/main.py. A checagem de idempotência procura especificamente
    por um _HandlerBancoDeDados já presente, não por `logger.handlers`
    estar vazio -- outras ferramentas (ex. o plugin de logging do pytest)
    podem anexar handlers próprios ao mesmo logger, principalmente depois
    que propagate=False é ligado abaixo."""
    logger = logging.getLogger(NOME_LOGGER)
    ja_configurado = any(isinstance(h, _HandlerBancoDeDados) for h in logger.handlers)
    if not ja_configurado:
        handler_stdout = logging.StreamHandler(sys.stdout)
        handler_stdout.setFormatter(_FormatadorJSON())
        logger.addHandler(handler_stdout)

        logger.addHandler(_HandlerBancoDeDados())

        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def log_no_executado(
    no: str, thread_id: str | None, batch_id: int | None, duracao_s: float
) -> None:
    """Emite o registro estruturado de sinal 1 (specs/fase02/design.md §
    Observabilidade) para 1 execução de nó do grafo -- ver
    graph.py::_com_log_estruturado."""
    logging.getLogger(NOME_LOGGER).info(
        "no_executado",
        extra={
            "dados_estruturados": {
                "thread_id": thread_id,
                "batch_id": batch_id,
                "no": no,
                "duracao_s": round(duracao_s, 4),
            }
        },
    )


def log_chamada_llm(
    provedor: str, modelo: str | None, duracao_s: float, sucesso: bool, erro: str | None = None
) -> None:
    """Emite 1 registro estruturado por tentativa de chamada de LLM,
    incluindo as que falham e acionam o próximo provedor da cadeia de
    fallback (config.py::get_llm) -- permite comparar desempenho e
    confiabilidade entre provedores (ex: Gemini demorando ou atingindo
    limite de taxa, Groq assumindo em seguida), não só contar quantas
    vezes o fallback foi acionado. Ver _CallbackObservabilidadeLLM."""
    logging.getLogger(NOME_LOGGER).info(
        "chamada_llm",
        extra={
            "dados_estruturados": {
                "provedor": provedor,
                "modelo": modelo,
                "duracao_s": round(duracao_s, 4),
                "sucesso": sucesso,
                "erro": erro,
            }
        },
    )


class _CallbackObservabilidadeLLM:
    """Callback do LangChain anexado à cadeia de fallback inteira
    (get_llm(), via `.with_config(callbacks=[...])`) -- os callbacks
    disparam para CADA tentativa dentro de `with_fallbacks()`, inclusive
    as que falham antes do próximo provedor assumir, então isso captura o
    fallback de verdade acontecendo, não só o resultado final. `run_id` é
    único por tentativa, usado para casar o início com o fim/erro
    correspondente."""

    def __init__(self) -> None:
        self._inicios: dict[Any, tuple[float, str, str | None]] = {}

    def _identificar(self, serialized: dict) -> tuple[str, str | None]:
        id_classe = serialized.get("id") or []
        provedor = id_classe[-1] if id_classe else serialized.get("name", "desconhecido")
        modelo = (serialized.get("kwargs") or {}).get("model")
        return provedor, modelo

    def on_chat_model_start(self, serialized, messages, *, run_id, **kwargs) -> None:
        provedor, modelo = self._identificar(serialized)
        self._inicios[run_id] = (time.monotonic(), provedor, modelo)

    def on_llm_end(self, response, *, run_id, **kwargs) -> None:
        inicio = self._inicios.pop(run_id, None)
        if inicio is None:
            return
        momento_inicio, provedor, modelo = inicio
        log_chamada_llm(provedor, modelo, time.monotonic() - momento_inicio, sucesso=True)

    def on_llm_error(self, error, *, run_id, **kwargs) -> None:
        inicio = self._inicios.pop(run_id, None)
        if inicio is None:
            return
        momento_inicio, provedor, modelo = inicio
        log_chamada_llm(
            provedor, modelo, time.monotonic() - momento_inicio, sucesso=False, erro=str(error)
        )


# Instância única (Fase 2, observabilidade) -- o dicionário interno é
# indexado por run_id (1 por tentativa, nunca reaproveitado pelo
# LangChain), então reusar a mesma instância entre chamadas de get_llm()
# não mistura tentativas de investigações diferentes.
_callback_observabilidade_llm = _CallbackObservabilidadeLLM()


@lru_cache
def carregar_regras_setor() -> dict:
    """Carrega config/regras_bioprocesso.yaml (thresholds de classification,
    faixas por parâmetro de biosensor, categorias do Ishikawa)."""
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_llm():
    """Seleciona o provedor/modelo de LLM via variável de ambiente --
    trocar de provedor não exige tocar em nodes.py/graph.py, só o .env
    (e instalar o pacote de integração correspondente, ex:
    langchain-anthropic, langchain-openai).

    Fallback automático: Groq (LLM_PROVIDER/LLM_MODEL -- provedor padrão
    deste projeto, gratuito e com limite diário generoso, hospeda modelos
    open-weight como o gpt-oss da OpenAI num chip próprio de inferência
    rápida) -> Gemini (2º provedor gratuito, mas com cota diária estreita
    no tier gratuito, 20 requisições/dia por modelo -- insuficiente como
    principal pra uma investigação completa, que consome bem mais que
    isso) -> Anthropic -> OpenAI, nessa ordem, via
    ChatModel.with_fallbacks(). Cada fallback só entra na cadeia se sua
    respectiva chave de API estiver configurada no .env -- rodar só com a
    chave do Groq (o cenário mínimo de testes/prototipagem) continua
    funcionando sem exigir as outras três; configurar GOOGLE_API_KEY (2º
    provedor gratuito) e/ou ANTHROPIC_API_KEY/OPENAI_API_KEY (reforço
    pago, ex: pra demonstração) ativa a resiliência extra sem mudar nenhum
    código. DeepSeek foi removido da cadeia (decisão do projeto: provedor
    pago sem crédito carregado, nunca funcionou de fato). Se todos os
    provedores configurados falharem, a exceção original propaga pro nó,
    que a converte em FalhaLLMError (ver nodes.py e specs/design.md §
    Tratamento de falha na chamada ao LLM).

    `LLM_PROVIDER=fake` ativa um provedor determinístico sem rede
    (root_cause_agent.fake_llm.FakeChatModel) -- usado pela suíte E2E
    (tests/e2e/, local e CI) pra rodar o fluxo completo sem custo/flakiness de
    chamar um provedor real. Nunca é o padrão."""
    provider = os.getenv("LLM_PROVIDER", "groq")
    if provider == "fake":
        from root_cause_agent.fake_llm import FakeChatModel

        return FakeChatModel()

    from langchain.chat_models import init_chat_model

    model = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
    principal = init_chat_model(model, model_provider=provider)

    fallbacks = []
    if os.getenv("GOOGLE_API_KEY"):
        fallbacks.append(
            init_chat_model(
                os.getenv("LLM_FALLBACK_GEMINI_MODEL", "gemini-2.5-flash"),
                model_provider="google_genai",
            )
        )
    if os.getenv("ANTHROPIC_API_KEY"):
        fallbacks.append(
            init_chat_model(
                os.getenv("LLM_FALLBACK_ANTHROPIC_MODEL", "claude-3-5-haiku-latest"),
                model_provider="anthropic",
            )
        )
    if os.getenv("OPENAI_API_KEY"):
        fallbacks.append(
            init_chat_model(
                os.getenv("LLM_FALLBACK_OPENAI_MODEL", "gpt-4o-mini"),
                model_provider="openai",
            )
        )

    cadeia = principal.with_fallbacks(fallbacks) if fallbacks else principal
    # Fase 2, observabilidade: anexado na cadeia inteira (não só no
    # principal), o callback dispara para cada tentativa dentro do
    # with_fallbacks(), inclusive as que falham -- ver
    # _CallbackObservabilidadeLLM e log_chamada_llm.
    return cadeia.with_config(callbacks=[_callback_observabilidade_llm])
