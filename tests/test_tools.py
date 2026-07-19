"""Teste básico: consultar_leituras_biosensor filtra corretamente a janela
de datas em sensor_readings (tests/fixtures/biotecpredict_teste.db), e
validar_resposta_operador rejeita vazio/frases evasivas.
"""

from __future__ import annotations

import pytest

from root_cause_agent.models import Classification, NaoConformidade, RiskPrediction
from root_cause_agent.tools import consultar_leituras_biosensor, validar_resposta_operador


def _estado(batch_id: int) -> dict:
    nc = NaoConformidade(
        batch_id=batch_id,
        upload_date="2026-07-10T08:00:00+00:00",
        compliance_score=38.0,
        classification=Classification.CRITICAL,
        risk_prediction=RiskPrediction.HIGH_RISK,
        sensor_metrics={},
        parametros_fora_da_faixa=[],
    )
    return {"nc_input": nc}


def test_janela_de_datas_filtra_corretamente():
    # leituras do lote 511 na fixture vão de 2026-07-08T08:00:00+00:00 até
    # 2026-07-10T07:00:00+00:00
    resultado = consultar_leituras_biosensor.func(
        data_inicio="2026-07-08T00:00:00",
        data_fim="2026-07-10T08:00:00",
        state=_estado(511),
    )
    assert "leituras do lote 511" in resultado
    assert "Nenhuma leitura" not in resultado


def test_janela_sem_leituras_correspondentes():
    resultado = consultar_leituras_biosensor.func(
        data_inicio="2020-01-01T00:00:00",
        data_fim="2020-01-02T00:00:00",
        state=_estado(511),
    )
    assert "Nenhuma leitura encontrada" in resultado


def test_data_invalida_retorna_mensagem_de_erro_sem_lancar_excecao():
    resultado = consultar_leituras_biosensor.func(
        data_inicio="não-é-uma-data",
        data_fim="2026-07-11T08:00:00",
        state=_estado(511),
    )
    assert "Datas inválidas" in resultado


def test_janela_invertida_retorna_mensagem_de_erro():
    resultado = consultar_leituras_biosensor.func(
        data_inicio="2026-07-11T08:00:00",
        data_fim="2026-07-10T08:00:00",
        state=_estado(511),
    )
    assert "inverta a janela" in resultado


def test_consulta_restrita_ao_batch_id_do_estado_nao_ao_argumento():
    """batch_id nunca é um parâmetro exposto ao LLM -- vem de state via
    InjectedState. Confirma que a tool nem aceita esse argumento."""
    assert "batch_id" not in consultar_leituras_biosensor.args


@pytest.mark.parametrize(
    "resposta",
    ["", "   ", "não sei", "Não Sei", "sei lá", "não lembro", "n/a", "-", "desconheço"],
)
def test_validar_resposta_operador_rejeita_vazia_ou_evasiva(resposta):
    assert validar_resposta_operador(resposta) is False


@pytest.mark.parametrize(
    "resposta",
    ["sim", "não", "a manutenção estava atrasada", "Sim, seguimos o procedimento padrão"],
)
def test_validar_resposta_operador_aceita_respostas_curtas_legitimas(resposta):
    assert validar_resposta_operador(resposta) is True
