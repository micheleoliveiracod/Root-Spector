"""Teste básico do backend/main.py via FastAPI TestClient, sem subir
servidor real e sem chamar um LLM de verdade (fake_llm, ver conftest.py).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from openapi_spec_validator import validate

from root_cause_agent.graph import build_graph
from root_cause_agent.nodes import FalhaLLMError

MENSAGEM_LLM_INDISPONIVEL = "Serviço de IA indisponível, recarregue a página."
FIXTURE_DB = Path(__file__).parent / "fixtures" / "biotecpredict_teste.db"


@pytest.fixture
def client(fake_llm, monkeypatch):
    import backend.main as backend_main

    monkeypatch.setattr(backend_main, "DB_PATH", FIXTURE_DB)
    grafo_teste = build_graph(":memory:")
    monkeypatch.setattr(backend_main, "grafo", grafo_teste)
    return TestClient(backend_main.app)


def _responder_11x(client, thread_id, prefixo="resposta"):
    ultimo = None
    for i in range(11):
        corpo = {"resposta": f"{prefixo} {i}"}
        r = client.post(f"/api/investigacoes/{thread_id}/responder", json=corpo)
        assert r.status_code == 200, r.text
        ultimo = r.json()
    return ultimo


def test_listar_lotes(client):
    resposta = client.get("/api/lotes")
    assert resposta.status_code == 200
    lotes = resposta.json()
    assert {lote["batch_id"] for lote in lotes} == {501, 502, 503, 511, 512}
    elegiveis = {lote["batch_id"] for lote in lotes if lote["elegivel"]}
    assert elegiveis == {511, 512}

    lote_511 = next(lote for lote in lotes if lote["batch_id"] == 511)
    assert "agitator_speed" in lote_511["parametros_fora_da_faixa"]

    lote_501 = next(lote for lote in lotes if lote["batch_id"] == 501)
    assert lote_501["parametros_fora_da_faixa"] == []


def test_investigacao_completa_ate_revisao_com_relatorio_ja_gerado(client):
    resposta = client.post("/api/investigacoes/511/iniciar")
    assert resposta.status_code == 200
    thread_id = resposta.json()["thread_id"]
    assert resposta.json()["fase"] == "ishikawa"
    assert "agitator_speed" in resposta.json()["nc"]["parametros_fora_da_faixa"]

    ultimo = _responder_11x(client, thread_id)
    assert ultimo["status"] == "pronto_para_revisao"

    r = client.get(f"/api/investigacoes/{thread_id}/revisao")
    assert r.status_code == 200
    corpo = r.json()
    assert len(corpo["respostas_ishikawa"]) == 6
    assert len(corpo["cadeia_de_porques"]) == 5

    links = corpo["relatorio"]
    assert links["json"].startswith("/reports/511_")
    assert links["html"].startswith("/reports/511_")

    r_html = client.get(links["html"])
    assert r_html.status_code == 200
    assert "Relatório de causa raiz" in r_html.text


def test_ajustar_arquiva_ciclo_e_reabre_novo(client):
    client.post("/api/investigacoes/512/iniciar")
    _responder_11x(client, 512)

    r = client.post("/api/investigacoes/512/ajustar")
    assert r.status_code == 200
    assert r.json()["fase"] == "ishikawa"

    ultimo = _responder_11x(client, 512, prefixo="resposta ciclo2")
    assert ultimo["status"] == "pronto_para_revisao"

    r = client.get("/api/investigacoes/512/revisao")
    assert r.status_code == 200
    assert r.json()["relatorio"]["html"].startswith("/reports/512_")


def test_falha_llm_error_vira_http_503(client, monkeypatch):
    import backend.main as backend_main

    def _sempre_falha(*args, **kwargs):
        raise FalhaLLMError("todos os provedores falharam")

    monkeypatch.setattr(backend_main.grafo, "invoke", _sempre_falha)

    r = client.post("/api/investigacoes/511/iniciar")
    assert r.status_code == 503
    assert r.json()["detail"] == MENSAGEM_LLM_INDISPONIVEL


def test_revisao_sem_diagnostico_pronto_devolve_400(client):
    client.post("/api/investigacoes/511/iniciar")
    r = client.get("/api/investigacoes/511/revisao")
    assert r.status_code == 400


def test_contrato_openapi_valido_e_cobre_as_rotas(client):
    esquema = client.get("/openapi.json").json()
    validate(esquema)  # levanta se o documento não for um OpenAPI válido

    rotas_esperadas = {
        "/api/lotes",
        "/api/investigacoes/{batch_id}/iniciar",
        "/api/investigacoes/{thread_id}/responder",
        "/api/investigacoes/{thread_id}/revisao",
        "/api/investigacoes/{thread_id}/ajustar",
    }
    assert rotas_esperadas <= set(esquema["paths"])
