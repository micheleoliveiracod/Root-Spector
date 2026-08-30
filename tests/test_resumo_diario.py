"""Issue #52 (specs/fase02/design.md § 6, Low-code): resumo diário de
investigações, consumido pelo workflow n8n. Usa as tabelas `relatorios` e
`eventos_log` de fixture (tmp_path), nunca o banco real do repositório."""

from __future__ import annotations

import sqlite3
from datetime import UTC, date, datetime

from root_cause_agent import reports, resumo_diario
from root_cause_agent.config import _SQL_CRIAR_TABELA_EVENTOS_LOG_SQLITE
from root_cause_agent.models import (
    CasoSemelhante,
    CategoriaAnalise,
    Classification,
    Diagnostico,
    NaoConformidade,
    PorQue,
    RespostaIshikawa,
    RiskPrediction,
)

DIA = date(2026, 8, 22)


def _nc(batch_id: int) -> NaoConformidade:
    return NaoConformidade(
        batch_id=batch_id,
        upload_date=datetime(2026, 8, 20, tzinfo=UTC),
        compliance_score=48.0,
        classification=Classification.WARNING,
        risk_prediction=RiskPrediction.MEDIUM_RISK,
        sensor_metrics={},
        parametros_fora_da_faixa=["agitator_speed"],
    )


def _diagnostico(
    batch_id: int,
    gerado_em: datetime,
    *,
    tentativas_extra: bool = False,
    casos_semelhantes: list[CasoSemelhante] | None = None,
) -> Diagnostico:
    resposta_ishikawa = RespostaIshikawa(
        categoria="Maquina",
        pergunta="P?",
        resposta="R.",
        tentativas=["R. errada", "R."] if tentativas_extra else ["R."],
    )
    return Diagnostico(
        nc=_nc(batch_id),
        respostas_ishikawa=[resposta_ishikawa],
        categoria_principal=CategoriaAnalise(categoria="Maquina", justificativa="teste"),
        categorias_descartadas=[],
        cadeia_de_porques=[PorQue(numero=1, pergunta="Por que?", resposta="Porque sim.")],
        causa_raiz="causa raiz de teste",
        narrativa="narrativa de teste",
        recomendacao_tratativa="recomendacao de teste",
        casos_semelhantes=casos_semelhantes or [],
        gerado_em=gerado_em,
    )


def _escrever_relatorio(diagnostico: Diagnostico) -> None:
    """Grava o Diagnostico na tabela `relatorios` de fixture, via
    reports.py::salvar_relatorio, o mesmo caminho de produção -- o teste
    precisa ter chamado antes `monkeypatch.setattr(reports,
    'OBSERVABILIDADE_DB_PATH', ...)` pra não tocar no banco real."""
    reports.salvar_relatorio(diagnostico)


def _escrever_eventos(caminho_db, eventos: list[dict]) -> None:
    """Cria a tabela eventos_log num banco SQLite de fixture e insere os
    eventos dados, preenchendo com None qualquer coluna não informada
    (mensagens diferentes usam colunas diferentes, ver
    config.py::_HandlerBancoDeDados.emit)."""
    caminho_db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(caminho_db))
    conn.execute(_SQL_CRIAR_TABELA_EVENTOS_LOG_SQLITE)
    colunas = [
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
    ]
    for evento in eventos:
        valores = [evento.get(c, "INFO" if c == "nivel" else None) for c in colunas]
        placeholders = ", ".join("?" * len(colunas))
        conn.execute(
            f"INSERT INTO eventos_log ({', '.join(colunas)}) VALUES ({placeholders})",
            valores,
        )
    conn.commit()
    conn.close()


def test_dia_sem_investigacoes_devolve_lista_vazia(tmp_path, monkeypatch):
    monkeypatch.setattr(reports, "OBSERVABILIDADE_DB_PATH", tmp_path / "vazio.db")
    monkeypatch.setattr(resumo_diario, "OBSERVABILIDADE_DB_PATH", tmp_path / "vazio.db")

    resultado = resumo_diario.montar_resumo_diario(DIA, base_url="http://localhost:8000")

    assert resultado["data"] == "2026-08-22"
    assert resultado["total_investigacoes"] == 0
    assert resultado["investigacoes"] == []
    assert resultado["eficiencia_operacional"]["tempo_medio_investigacao_s"] == 0.0
    assert resultado["eficiencia_operacional"]["fallback_llm_acionado"] == 0


def test_investigacao_do_dia_aparece_com_link_de_pdf_e_recorrencia(tmp_path, monkeypatch):
    caminho_db = tmp_path / "banco.db"
    monkeypatch.setattr(reports, "OBSERVABILIDADE_DB_PATH", caminho_db)
    monkeypatch.setattr(resumo_diario, "OBSERVABILIDADE_DB_PATH", caminho_db)

    caso = CasoSemelhante(
        batch_id=1, categoria_principal="Maquina", causa_raiz="antiga", gerado_em=datetime.now(UTC)
    )
    diagnostico = _diagnostico(
        11, datetime(2026, 8, 22, 10, 0, tzinfo=UTC), casos_semelhantes=[caso]
    )
    _escrever_relatorio(diagnostico)

    resultado = resumo_diario.montar_resumo_diario(DIA, base_url="http://localhost:8000")

    assert resultado["total_investigacoes"] == 1
    investigacao = resultado["investigacoes"][0]
    assert investigacao["batch_id"] == 11
    assert investigacao["classification"] == "WARNING"
    assert investigacao["risk_prediction"] == "MEDIUM_RISK"
    assert investigacao["categoria_principal"] == "Maquina"
    assert investigacao["causa_raiz"] == "causa raiz de teste"
    assert "1 caso" in investigacao["recorrencia"]
    link_esperado = "http://localhost:8000/api/investigacoes/11/relatorio.pdf"
    assert investigacao["link_relatorio_pdf"] == link_esperado


def test_investigacao_sem_casos_semelhantes_mostra_caso_inedito(tmp_path, monkeypatch):
    caminho_db = tmp_path / "banco.db"
    monkeypatch.setattr(reports, "OBSERVABILIDADE_DB_PATH", caminho_db)
    monkeypatch.setattr(resumo_diario, "OBSERVABILIDADE_DB_PATH", caminho_db)

    diagnostico = _diagnostico(12, datetime(2026, 8, 22, 10, 0, tzinfo=UTC))
    _escrever_relatorio(diagnostico)

    resultado = resumo_diario.montar_resumo_diario(DIA, base_url="http://localhost:8000")

    esperado = "Primeiro caso registrado com esse padrão."
    assert resultado["investigacoes"][0]["recorrencia"] == esperado


def test_relatorios_de_outro_dia_nao_entram_no_resumo(tmp_path, monkeypatch):
    caminho_db = tmp_path / "banco.db"
    monkeypatch.setattr(reports, "OBSERVABILIDADE_DB_PATH", caminho_db)
    monkeypatch.setattr(resumo_diario, "OBSERVABILIDADE_DB_PATH", caminho_db)

    _escrever_relatorio(_diagnostico(13, datetime(2026, 8, 21, 23, 59, tzinfo=UTC)))
    _escrever_relatorio(_diagnostico(14, datetime(2026, 8, 23, 0, 0, tzinfo=UTC)))

    resultado = resumo_diario.montar_resumo_diario(DIA, base_url="http://localhost:8000")

    assert resultado["total_investigacoes"] == 0


def test_respostas_com_2_tentativas_e_contada(tmp_path, monkeypatch):
    caminho_db = tmp_path / "banco.db"
    monkeypatch.setattr(reports, "OBSERVABILIDADE_DB_PATH", caminho_db)
    monkeypatch.setattr(resumo_diario, "OBSERVABILIDADE_DB_PATH", caminho_db)

    diagnostico = _diagnostico(
        15, datetime(2026, 8, 22, 10, 0, tzinfo=UTC), tentativas_extra=True
    )
    _escrever_relatorio(diagnostico)

    resultado = resumo_diario.montar_resumo_diario(DIA, base_url="http://localhost:8000")

    assert resultado["eficiencia_operacional"]["respostas_com_2_tentativas"] == 1


def test_eficiencia_operacional_agrega_eventos_do_dia(tmp_path, monkeypatch):
    caminho_db = tmp_path / "observabilidade.db"
    monkeypatch.setattr(reports, "OBSERVABILIDADE_DB_PATH", caminho_db)
    monkeypatch.setattr(resumo_diario, "OBSERVABILIDADE_DB_PATH", caminho_db)

    _escrever_eventos(
        caminho_db,
        [
            {
                "timestamp": "2026-08-22T10:00:00+00:00",
                "mensagem": "no_executado",
                "thread_id": "16",
                "no": "preparar_contexto",
                "duracao_s": 1.0,
            },
            {
                "timestamp": "2026-08-22T10:00:05+00:00",
                "mensagem": "no_executado",
                "thread_id": "16",
                "no": "orquestrar_analise",
                "duracao_s": 3.0,
            },
            {
                "timestamp": "2026-08-22T10:00:02+00:00",
                "mensagem": "chamada_llm",
                "provedor": "ChatGoogleGenerativeAI",
                "modelo": "gemini-2.5-flash",
                "duracao_s": 8.0,
                "sucesso": 0,
                "erro": "rate limit",
            },
            {
                "timestamp": "2026-08-22T10:00:03+00:00",
                "mensagem": "chamada_llm",
                "provedor": "ChatGroq",
                "modelo": "llama-3.3-70b-versatile",
                "duracao_s": 0.5,
                "sucesso": 1,
                "erro": None,
            },
            # evento de outro dia, não deve entrar na agregação
            {
                "timestamp": "2026-08-21T10:00:00+00:00",
                "mensagem": "no_executado",
                "thread_id": "17",
                "no": "preparar_contexto",
                "duracao_s": 99.0,
            },
        ],
    )

    resultado = resumo_diario.montar_resumo_diario(DIA, base_url="http://localhost:8000")
    eficiencia = resultado["eficiencia_operacional"]

    assert eficiencia["tempo_medio_investigacao_s"] == 4.0  # 1.0 + 3.0, 1 thread só
    assert eficiencia["tempo_medio_por_no"] == {
        "preparar_contexto": 1.0,
        "orquestrar_analise": 3.0,
    }
    assert eficiencia["fallback_llm_acionado"] == 1
    assert eficiencia["desempenho_llm_por_provedor"]["ChatGoogleGenerativeAI"] == {
        "chamadas": 1,
        "sucessos": 0,
        "falhas": 1,
        "duracao_media_s": 8.0,
    }
    assert eficiencia["desempenho_llm_por_provedor"]["ChatGroq"] == {
        "chamadas": 1,
        "sucessos": 1,
        "falhas": 0,
        "duracao_media_s": 0.5,
    }


def test_eventos_do_dia_usa_postgres_quando_database_url_definida(tmp_path, monkeypatch):
    """Issue #58: quando DATABASE_URL estiver definida, o resumo diário lê
    de lá, não do SQLite local -- sem conectar a um Postgres real,
    psycopg.connect é substituído por um dublê. `listar_relatorios()`
    também passa pelo mesmo dublê (sem nenhum relatório salvo nessa
    tabela fake, devolve lista vazia)."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://usuario:senha@localhost/banco")

    linhas_por_mensagem = {
        "no_executado": [
            {
                "no": "preparar_contexto",
                "thread_id": "16",
                "duracao_s": 2.0,
                "provedor": None,
                "modelo": None,
                "sucesso": None,
            }
        ],
        "chamada_llm": [],
    }

    class _ConexaoFake:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def execute(self, sql, parametros=None):
            if "relatorios" in sql:
                return _CursorFake([])
            mensagem = parametros[0]
            return _CursorFake(linhas_por_mensagem[mensagem])

    class _CursorFake:
        def __init__(self, linhas):
            self._linhas = linhas

        def fetchall(self):
            return self._linhas

    monkeypatch.setattr("psycopg.connect", lambda *args, **kwargs: _ConexaoFake())

    resultado = resumo_diario.montar_resumo_diario(DIA, base_url="http://localhost:8000")

    assert resultado["eficiencia_operacional"]["tempo_medio_por_no"] == {
        "preparar_contexto": 2.0
    }
    assert resultado["eficiencia_operacional"]["tempo_medio_investigacao_s"] == 2.0
