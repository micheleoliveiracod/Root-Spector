"""Fixtures compartilhadas: aponta o agente pra fixture de teste (nunca
data/biotecpredict.db) e fornece um LLM fake (nunca um provedor real)."""

from __future__ import annotations

from pathlib import Path

import pytest

from root_cause_agent.fake_llm import FakeChatModel

FIXTURE_DB = Path(__file__).parent / "fixtures" / "biotecpredict_teste.db"


@pytest.fixture(autouse=True)
def usar_fixture_db(monkeypatch, tmp_path):
    """`tools.py` e `nodes.py` importam DB_PATH com `from ... import
    DB_PATH`, então o patch precisa mirar o nome já vinculado em cada
    módulo, não só `config.DB_PATH`. `backend/main.py` importa DB_PATH do
    mesmo jeito -- ver o fixture `client` em test_backend.py, que corrige
    isso no momento certo (após importar o módulo pela 1ª vez).

    Também isola tools.REPORTS_DIR num diretório vazio por padrão -- sem
    isso, a tool `consultar_recorrencia` (chamada por recomendar_tratativa
    sempre que o fake LLM decide chamá-la) varreria os reports/*.json REAIS
    do repositório durante os testes, tornando-os não determinísticos.
    Testes que precisam de relatórios de fixture (test_tool_recorrencia.py)
    sobrescrevem isso explicitamente."""
    from root_cause_agent import nodes, tools

    monkeypatch.setattr(tools, "DB_PATH", FIXTURE_DB)
    monkeypatch.setattr(nodes, "DB_PATH", FIXTURE_DB)
    monkeypatch.setattr(tools, "REPORTS_DIR", tmp_path / "reports_vazio_por_padrao")


@pytest.fixture
def embeddings_fake(monkeypatch):
    """LLM_PROVIDER=fake ativa DeterministicFakeEmbedding em
    root_cause_agent/rag.py (ver rag.py::_obter_embeddings) -- nenhum
    teste automatizado chama a API real de embeddings, mesma regra já
    aplicada ao LLM (fixture `fake_llm` acima). Escopo por teste (não
    autouse global) para não interferir em test_config.py, que testa
    get_llm() com LLM_PROVIDER não setado. O cache do vector store é
    limpo antes e depois para não vazar embeddings de um provedor
    diferente entre testes."""
    from root_cause_agent import rag

    monkeypatch.setenv("LLM_PROVIDER", "fake")
    rag.limpar_cache()
    yield
    rag.limpar_cache()


@pytest.fixture
def fake_llm(monkeypatch, embeddings_fake):
    """Substitui root_cause_agent.nodes.get_llm pelo mesmo FakeChatModel
    usado por LLM_PROVIDER=fake (root_cause_agent/fake_llm.py) -- os nós
    agênticos nunca chamam um provedor real durante os testes. Depende de
    `embeddings_fake` porque o grafo completo passa por pre_busca_rag/
    recomendar_tratativa (Fase 2), que chamam root_cause_agent.rag."""
    from root_cause_agent import nodes

    monkeypatch.setattr(nodes, "get_llm", lambda: FakeChatModel())
    return FakeChatModel
