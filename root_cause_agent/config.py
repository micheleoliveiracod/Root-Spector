"""Configuração e composição: .env, seleção de LLM plugável, caminhos dos
bancos e carga das regras do setor. Ver specs/design.md."""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "config" / "regras_bioprocesso.yaml"
DB_PATH = Path(os.getenv("BIOTECPREDICT_DB_PATH", str(REPO_ROOT / "data" / "biotecpredict.db")))
CHECKPOINT_DB_PATH = Path(
    os.getenv("CHECKPOINT_DB_PATH", str(REPO_ROOT / "data" / "checkpoints.db"))
)
REPORTS_DIR = Path(os.getenv("REPORTS_DIR", str(REPO_ROOT / "reports")))

# Observabilidade (Fase 2, specs/fase02/design.md § Observabilidade) --
# sinal 1: logging estruturado (JSON), 1 registro por nó do grafo
# executado (thread_id, batch_id, nome do nó, duração). Sinal 2: trace do
# LangSmith, ativado via a env var opcional LANGSMITH_TRACING (lida
# diretamente pelo langsmith/langchain-core a partir do ambiente, sem
# código adicional aqui além do load_dotenv() já existente -- ver .env.example.
NOME_LOGGER = "root_cause_agent"


class _FormatadorJSON(logging.Formatter):
    """1 linha de JSON por registro -- sem dependência nova (stdlib
    logging), ver specs/fase02/design.md § Observabilidade."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "nivel": record.levelname,
            "mensagem": record.getMessage(),
        }
        payload.update(getattr(record, "dados_estruturados", {}))
        return json.dumps(payload, ensure_ascii=False)


def configurar_logging() -> logging.Logger:
    """Configura o logger `root_cause_agent` com saída JSON em stdout --
    idempotente (chamar de novo não duplica o handler), chamado no startup
    de graph.py e backend/main.py. A checagem de idempotência procura
    especificamente por um handler já formatado com _FormatadorJSON, não
    por `logger.handlers` estar vazio -- outras ferramentas (ex. o plugin
    de logging do pytest) podem anexar handlers próprios ao mesmo logger,
    principalmente depois que propagate=False é ligado abaixo."""
    logger = logging.getLogger(NOME_LOGGER)
    ja_configurado = any(isinstance(h.formatter, _FormatadorJSON) for h in logger.handlers)
    if not ja_configurado:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_FormatadorJSON())
        logger.addHandler(handler)
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

    Fallback automático: Gemini (LLM_PROVIDER/LLM_MODEL -- o provedor
    oficial deste projeto, gratuito, usado em testes e prototipagem) ->
    Groq (hospeda modelos open-source como Llama num chip próprio de
    inferência rápida, tier gratuito generoso, usado nos mesmos testes) ->
    Anthropic -> OpenAI, nessa ordem, via ChatModel.with_fallbacks(). Cada
    fallback só entra na cadeia se sua respectiva chave de API estiver
    configurada no .env -- rodar só com a chave do Gemini (o cenário mínimo
    de testes/prototipagem) continua funcionando sem exigir as outras três;
    configurar GROQ_API_KEY (2º provedor gratuito pra testar de verdade) e/ou
    ANTHROPIC_API_KEY/OPENAI_API_KEY (reforço pago, ex: pra demonstração)
    ativa a resiliência extra sem mudar nenhum código. Se todos os
    provedores configurados falharem, a exceção original propaga pro nó,
    que a converte em FalhaLLMError (ver nodes.py e specs/design.md §
    Tratamento de falha na chamada ao LLM).

    `LLM_PROVIDER=fake` ativa um provedor determinístico sem rede
    (root_cause_agent.fake_llm.FakeChatModel) -- usado pela suíte E2E
    (tests/e2e/, local e CI) pra rodar o fluxo completo sem custo/flakiness de
    chamar um provedor real. Nunca é o padrão."""
    provider = os.getenv("LLM_PROVIDER", "google_genai")
    if provider == "fake":
        from root_cause_agent.fake_llm import FakeChatModel

        return FakeChatModel()

    from langchain.chat_models import init_chat_model

    model = os.getenv("LLM_MODEL", "gemini-2.5-flash")
    principal = init_chat_model(model, model_provider=provider)

    fallbacks = []
    if os.getenv("GROQ_API_KEY"):
        fallbacks.append(
            init_chat_model(
                os.getenv("LLM_FALLBACK_GROQ_MODEL", "llama-3.3-70b-versatile"),
                model_provider="groq",
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

    return principal.with_fallbacks(fallbacks) if fallbacks else principal
