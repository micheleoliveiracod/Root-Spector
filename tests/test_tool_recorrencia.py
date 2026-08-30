"""Issue #47 (specs/fase02/design.md § 7): tool `consultar_recorrencia`,
que lê os relatórios já salvos na tabela `relatorios` (reports.py)
procurando casos anteriores com a mesma categoria Ishikawa principal e ao
menos 1 parâmetro de biosensor fora da faixa em comum, excluindo o
próprio lote. Usa relatórios de fixture em
tests/fixtures/reports_teste/ (nunca a tabela real do repositório),
gravados na tabela via reports.py::salvar_relatorio, o mesmo caminho de
produção."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from root_cause_agent import nodes
from root_cause_agent.models import (
    CategoriaAnalise,
    Classification,
    Diagnostico,
    NaoConformidade,
    RiskPrediction,
)
from root_cause_agent.tools import buscar_casos_semelhantes, consultar_recorrencia

REPORTS_TESTE = Path(__file__).parent / "fixtures" / "reports_teste"


@pytest.fixture(autouse=True)
def usar_reports_de_fixture(monkeypatch, tmp_path):
    from root_cause_agent import reports

    monkeypatch.setattr(reports, "OBSERVABILIDADE_DB_PATH", tmp_path / "relatorios_de_fixture.db")
    for caminho in sorted(REPORTS_TESTE.glob("*.json")):
        diagnostico = Diagnostico.model_validate_json(caminho.read_text(encoding="utf-8"))
        reports.salvar_relatorio(diagnostico)


def _estado(batch_id: int, categoria: str, parametros_fora_da_faixa: list[str]) -> dict:
    nc = NaoConformidade(
        batch_id=batch_id,
        upload_date="2026-07-10T08:00:00+00:00",
        compliance_score=38.0,
        classification=Classification.CRITICAL,
        risk_prediction=RiskPrediction.HIGH_RISK,
        sensor_metrics={},
        parametros_fora_da_faixa=parametros_fora_da_faixa,
    )
    categoria_principal = CategoriaAnalise(categoria=categoria, justificativa="teste")
    return {"nc_input": nc, "categoria_principal": categoria_principal}


# Fixtures em reports_teste/: lote 501 (Maquina, agitator_speed), 502
# (Maquina, temperature), 503 (Material, agitator_speed) -- só o 501 é
# semelhante a um lote "Maquina" com "agitator_speed" fora da faixa.


def test_encontra_casos_semelhantes_por_categoria_e_parametro_em_comum():
    estado = _estado(999, "Maquina", ["agitator_speed"])

    casos = buscar_casos_semelhantes(estado)

    assert len(casos) == 1
    assert casos[0].batch_id == 501
    assert casos[0].categoria_principal == "Maquina"
    assert "agitador" in casos[0].causa_raiz.lower()


def test_nao_encontra_nada_sem_categoria_e_parametro_em_comum():
    estado = _estado(999, "Mao de obra", ["ph"])

    assert buscar_casos_semelhantes(estado) == []


def test_nao_encontra_nada_com_mesma_categoria_mas_parametro_diferente():
    """Fixture 502 é 'Maquina', mas com 'temperature' -- sem sobreposição
    de parametros_fora_da_faixa com o lote 999 (agitator_speed), não deve
    contar como semelhante."""
    estado = _estado(999, "Maquina", ["agitator_speed"])

    batch_ids = {c.batch_id for c in buscar_casos_semelhantes(estado)}
    assert 502 not in batch_ids


def test_exclui_o_proprio_lote_da_busca():
    """Lote 501 buscando por si mesmo (mesma categoria/parâmetro que seu
    próprio relatório de fixture) não deve se encontrar."""
    estado = _estado(501, "Maquina", ["agitator_speed"])

    assert buscar_casos_semelhantes(estado) == []


def test_tool_retorna_texto_indicando_caso_inedito_quando_nada_encontrado():
    estado = _estado(999, "Meio ambiente", ["ph"])

    resultado = consultar_recorrencia.func(state=estado)

    assert "inédita" in resultado


def test_tool_retorna_texto_estruturado_quando_ha_recorrencia():
    estado = _estado(999, "Maquina", ["agitator_speed"])

    resultado = consultar_recorrencia.func(state=estado)

    assert "1 caso" in resultado
    assert "Lote 501" in resultado


def test_tool_nao_expoe_parametros_ao_llm():
    """A tool não recebe categoria/parametros como argumento do LLM -- só
    injeta o estado (mesmo padrão de consultar_leituras_biosensor com
    batch_id, ver test_tools.py)."""
    assert consultar_recorrencia.args == {}


def test_sem_banco_de_relatorios_nao_lanca_excecao(tmp_path, monkeypatch):
    from root_cause_agent import reports

    monkeypatch.setattr(reports, "OBSERVABILIDADE_DB_PATH", tmp_path / "banco_inexistente.db")
    estado = _estado(999, "Maquina", ["agitator_speed"])
    assert buscar_casos_semelhantes(estado) == []


def test_recomendar_tratativa_reflete_recorrencia_no_diagnostico_estruturado(fake_llm):
    """Issue #47: o Diagnostico final reflete a recorrência de forma
    estruturada (casos_semelhantes), não só em texto solto -- exercita
    nodes.py::recomendar_tratativa de ponta a ponta (tool decidida pelo
    FakeChatModel, ver fake_llm.py::_FakeBound.invoke)."""
    estado_base = _estado(999, "Maquina", ["agitator_speed"])
    nc, categoria_principal = estado_base["nc_input"], estado_base["categoria_principal"]
    diagnostico_parcial = Diagnostico(
        nc=nc,
        respostas_ishikawa=[],
        categoria_principal=categoria_principal,
        categorias_descartadas=[],
        cadeia_de_porques=[],
        causa_raiz="causa raiz de teste",
        narrativa="narrativa de teste",
        gerado_em=datetime.now(UTC),
    )
    state = {
        "nc_input": nc,
        "categoria_principal": categoria_principal,
        "candidatos_rag": [],
        "diagnostico": diagnostico_parcial,
    }

    resultado = nodes.recomendar_tratativa(state)

    casos = resultado["diagnostico"].casos_semelhantes
    assert len(casos) == 1
    assert casos[0].batch_id == 501
