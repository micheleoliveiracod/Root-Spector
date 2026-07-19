"""Teste básico: config.py::get_llm() monta a cadeia de fallback Gemini ->
Groq -> Anthropic -> OpenAI corretamente conforme as chaves presentes no
ambiente (mockadas, nunca uma chamada real). Cobre pelo menos: só Gemini
configurado (sem fallback), Gemini+Groq (os 2 provedores gratuitos), os 4
provedores, e o caso em que todos os provedores configurados falham -- o nó
agêntico que chama get_llm() deve relançar FalhaLLMError (nodes.py) apenas
nesse último caso, nunca antes de esgotar os fallbacks configurados.
"""

from __future__ import annotations

import pytest

from root_cause_agent.config import get_llm
from root_cause_agent.nodes import FalhaLLMError, _invocar_ou_falhar


class _FakeChatModel:
    def __init__(self, provider: str):
        self.provider = provider
        self.fallbacks: list | None = None

    def with_fallbacks(self, fallbacks):
        self.fallbacks = list(fallbacks)
        return self


def _patch_init_chat_model(mocker):
    criados: list[_FakeChatModel] = []

    def fake_init(model, model_provider):
        modelo = _FakeChatModel(model_provider)
        criados.append(modelo)
        return modelo

    mocker.patch("langchain.chat_models.init_chat_model", side_effect=fake_init)
    return criados


@pytest.fixture(autouse=True)
def sem_chaves_de_fallback_por_padrao(monkeypatch):
    """Garante que nenhum teste herda GROQ_API_KEY/ANTHROPIC_API_KEY/
    OPENAI_API_KEY de um .env real na máquina de quem roda os testes --
    cada teste liga explicitamente só as chaves que quer exercitar."""
    for chave in ("GROQ_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
        monkeypatch.delenv(chave, raising=False)


def test_so_gemini_configurado_sem_fallback(mocker):
    criados = _patch_init_chat_model(mocker)

    llm = get_llm()

    assert [c.provider for c in criados] == ["google_genai"]
    # sem fallback configurado, get_llm() devolve o principal direto --
    # with_fallbacks() nunca é chamado (nada pra encadear)
    assert llm is criados[0]
    assert llm.fallbacks is None


def test_gemini_e_groq_os_2_provedores_gratuitos(mocker, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "chave-fake")
    criados = _patch_init_chat_model(mocker)

    llm = get_llm()

    assert [c.provider for c in criados] == ["google_genai", "groq"]
    assert llm is criados[0]
    assert llm.fallbacks == [criados[1]]


def test_gemini_groq_e_anthropic(mocker, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "chave-fake")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "outra-chave-fake")
    criados = _patch_init_chat_model(mocker)

    llm = get_llm()

    assert [c.provider for c in criados] == ["google_genai", "groq", "anthropic"]
    assert llm.fallbacks == criados[1:]


def test_os_4_provedores_configurados(mocker, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "chave-fake")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "outra-chave-fake")
    monkeypatch.setenv("OPENAI_API_KEY", "mais-uma-chave-fake")
    criados = _patch_init_chat_model(mocker)

    llm = get_llm()

    assert [c.provider for c in criados] == ["google_genai", "groq", "anthropic", "openai"]
    assert llm.fallbacks == criados[1:]


def test_todos_os_provedores_falhando_relanca_falha_llm_error():
    """A falha real de invocação (rede, rate limit, chave inválida) só vira
    FalhaLLMError depois de esgotada a cadeia -- aqui simulada como uma
    exceção genérica do provedor, que _invocar_ou_falhar (nodes.py) deve
    converter."""

    def chamada_que_falha():
        raise RuntimeError("todos os provedores configurados falharam")

    with pytest.raises(FalhaLLMError):
        _invocar_ou_falhar(chamada_que_falha)


def test_falha_llm_error_preserva_a_excecao_original_via_cause():
    original = RuntimeError("rate limit")

    def chamada_que_falha():
        raise original

    try:
        _invocar_ou_falhar(chamada_que_falha)
    except FalhaLLMError as exc:
        assert exc.__cause__ is original
    else:
        pytest.fail("FalhaLLMError não foi levantada")
