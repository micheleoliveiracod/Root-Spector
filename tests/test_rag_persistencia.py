"""Testes de root_cause_agent/rag.py: reindexação condicional do backend
Postgres (_vector_store_postgres) via hash do corpus (issue #98) --
psycopg.connect e langchain_postgres.PGVector são substituídos por
dublês, sem depender de um Postgres real, mesmo padrão já usado no
projeto para o caminho Postgres do checkpointer (não coberto por teste
automatizado contra um banco de verdade, só validado manualmente em
produção, ver README § Planejado). Ver tests/test_rag.py para os testes
do backend em memória, o caminho usado por padrão em dev/CI."""

from __future__ import annotations

import pytest

from root_cause_agent import rag


class _CursorFake:
    def __init__(self, linha):
        self._linha = linha

    def fetchone(self):
        return self._linha


class _ConexaoFake:
    """Guarda o hash "persistido" em memória e registra os comandos SQL
    executados, o suficiente pra simular a tabela rag_indice_hash sem um
    Postgres de verdade."""

    def __init__(self, hash_persistido=None):
        self.hash_persistido = hash_persistido
        self.comandos: list[tuple[str, object]] = []

    def execute(self, sql, params=None):
        self.comandos.append((sql, params))
        if sql.strip().upper().startswith("SELECT"):
            linha = (self.hash_persistido,) if self.hash_persistido is not None else None
            return _CursorFake(linha)
        if "INSERT INTO rag_indice_hash" in sql:
            self.hash_persistido = params[1]
        return _CursorFake(None)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class _PGVectorFake:
    """Registra com quais argumentos foi instanciado e se add_texts() foi
    chamado -- é isso que os testes usam pra confirmar que uma reindexação
    (chamada real de embedding) aconteceu ou não."""

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.textos_adicionados: list[str] | None = None

    def add_texts(self, textos, metadatas=None):
        self.textos_adicionados = textos


@pytest.fixture
def postgres_fake(monkeypatch):
    """LLM_PROVIDER=fake evita qualquer chamada real de embedding mesmo se
    o teste falhar em impedir add_texts()."""
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    monkeypatch.setattr("langchain_postgres.PGVector", _PGVectorFake)


def test_reindexa_quando_hash_persistido_difere(postgres_fake, monkeypatch):
    conexao = _ConexaoFake(hash_persistido="hash-de-uma-versao-anterior-do-corpus")
    monkeypatch.setattr("psycopg.connect", lambda *a, **k: conexao)

    store = rag._vector_store_postgres("postgresql://fake")

    assert store.kwargs["pre_delete_collection"] is True
    assert store.textos_adicionados  # reindexou de verdade
    assert conexao.hash_persistido == rag._hash_base_conhecimento()


def test_nao_reindexa_quando_hash_persistido_e_igual(postgres_fake, monkeypatch):
    hash_atual = rag._hash_base_conhecimento()
    conexao = _ConexaoFake(hash_persistido=hash_atual)
    monkeypatch.setattr("psycopg.connect", lambda *a, **k: conexao)

    store = rag._vector_store_postgres("postgresql://fake")

    assert store.kwargs["pre_delete_collection"] is False
    assert store.textos_adicionados is None  # nenhum embedding novo chamado


def test_hash_muda_quando_conteudo_da_base_muda(tmp_path, monkeypatch):
    monkeypatch.setattr(rag, "BASE_CONHECIMENTO_DIR", tmp_path)
    (tmp_path / "a.md").write_text("conteudo original", encoding="utf-8")

    hash_original = rag._hash_base_conhecimento()
    (tmp_path / "a.md").write_text("conteudo alterado", encoding="utf-8")
    hash_alterado = rag._hash_base_conhecimento()

    assert hash_original != hash_alterado


def test_hash_e_estavel_para_o_mesmo_conteudo(tmp_path, monkeypatch):
    monkeypatch.setattr(rag, "BASE_CONHECIMENTO_DIR", tmp_path)
    (tmp_path / "a.md").write_text("conteudo estavel", encoding="utf-8")

    assert rag._hash_base_conhecimento() == rag._hash_base_conhecimento()
