"""Issue #58 (specs/deploy-producao/plano.md): checkpointer condicional,
SqliteSaver local por padrão, PostgresSaver quando DATABASE_URL estiver
definida. O caminho SQLite já é exercitado por toda a suíte de testes
(build_graph nunca recebe DATABASE_URL); aqui cobrimos especificamente a
escolha condicional, sem depender de um Postgres real."""

from __future__ import annotations

from langgraph.checkpoint.sqlite import SqliteSaver

from root_cause_agent import graph as graph_module


def test_sem_database_url_usa_sqlite(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    checkpointer = graph_module._criar_checkpointer(":memory:")

    assert isinstance(checkpointer, SqliteSaver)


def test_com_database_url_usa_postgres_e_chama_setup(monkeypatch):
    """Não conecta a um Postgres real -- Connection.connect e
    PostgresSaver são substituídos por dublês, só pra confirmar que
    _criar_checkpointer escolhe o caminho certo e chama setup() (que cria
    as tabelas de checkpoint na 1ª vez que o banco é usado)."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://usuario:senha@localhost/banco")

    conexao_fake = object()
    monkeypatch.setattr(
        "psycopg.Connection.connect", lambda *args, **kwargs: conexao_fake
    )

    setup_chamado = []

    class _PostgresSaverFake:
        def __init__(self, conn, serde=None):
            self.conn = conn
            self.serde = serde

        def setup(self):
            setup_chamado.append(True)

    monkeypatch.setattr("langgraph.checkpoint.postgres.PostgresSaver", _PostgresSaverFake)

    checkpointer = graph_module._criar_checkpointer(None)

    assert isinstance(checkpointer, _PostgresSaverFake)
    assert checkpointer.conn is conexao_fake
    assert setup_chamado == [True]


def test_com_database_url_ignora_checkpoint_db_path(monkeypatch):
    """checkpoint_db_path (":memory:" ou outro caminho SQLite) só faz
    sentido no caminho SQLite -- com DATABASE_URL definida, o Postgres é
    usado independente do que for passado nesse parâmetro."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://usuario:senha@localhost/banco")
    monkeypatch.setattr("psycopg.Connection.connect", lambda *args, **kwargs: object())

    class _PostgresSaverFake:
        def __init__(self, conn, serde=None):
            pass

        def setup(self):
            pass

    monkeypatch.setattr("langgraph.checkpoint.postgres.PostgresSaver", _PostgresSaverFake)

    checkpointer = graph_module._criar_checkpointer(":memory:")

    assert isinstance(checkpointer, _PostgresSaverFake)
