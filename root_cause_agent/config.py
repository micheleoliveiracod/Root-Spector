"""Configuração e composição: .env, seleção de LLM plugável, caminhos dos
bancos e carga das regras do setor. Ver specs/design.md."""

from __future__ import annotations

import os
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
