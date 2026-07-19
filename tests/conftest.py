"""Fixtures compartilhadas: aponta o agente pra fixture de teste (nunca
data/biotecpredict.db) e fornece um LLM fake (nunca um provedor real)."""

from __future__ import annotations

from pathlib import Path

import pytest

from root_cause_agent.fake_llm import FakeChatModel

FIXTURE_DB = Path(__file__).parent / "fixtures" / "biotecpredict_teste.db"


@pytest.fixture(autouse=True)
def usar_fixture_db(monkeypatch):
    """`tools.py` e `nodes.py` importam DB_PATH com `from ... import
    DB_PATH`, então o patch precisa mirar o nome já vinculado em cada
    módulo, não só `config.DB_PATH`. `backend/main.py` importa DB_PATH do
    mesmo jeito -- ver o fixture `client` em test_backend.py, que corrige
    isso no momento certo (após importar o módulo pela 1ª vez)."""
    from root_cause_agent import nodes, tools

    monkeypatch.setattr(tools, "DB_PATH", FIXTURE_DB)
    monkeypatch.setattr(nodes, "DB_PATH", FIXTURE_DB)


@pytest.fixture
def fake_llm(monkeypatch):
    """Substitui root_cause_agent.nodes.get_llm pelo mesmo FakeChatModel
    usado por LLM_PROVIDER=fake (root_cause_agent/fake_llm.py) -- os nós
    agênticos nunca chamam um provedor real durante os testes."""
    from root_cause_agent import nodes

    monkeypatch.setattr(nodes, "get_llm", lambda: FakeChatModel())
    return FakeChatModel
