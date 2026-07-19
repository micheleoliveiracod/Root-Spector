"""Teste básico: via o harness de main.py (rodar_investigacao_com_respostas),
o grafo roda ponta a ponta com 11 respostas fornecidas (6 Ishikawa + 5
porquês) sobre um lote de tests/fixtures/biotecpredict_teste.db, produzindo
um Diagnostico válido conforme o schema Pydantic. Cobre também o caso de
"pedir ajuste" gerando um segundo ciclo.
"""

from __future__ import annotations

from datetime import UTC, datetime

from root_cause_agent.main import rodar_investigacao_com_respostas
from root_cause_agent.models import CicloAnterior
from root_cause_agent.state import CATEGORIAS_ISHIKAWA_ORDEM

RESPOSTAS = [f"resposta {i}" for i in range(11)]


def test_ciclo_completo_produz_diagnostico_valido(fake_llm):
    diagnostico, _graph = rodar_investigacao_com_respostas(511, RESPOSTAS)

    assert diagnostico.nc.batch_id == 511
    assert diagnostico.nc.parametros_fora_da_faixa == ["agitator_speed"]
    assert len(diagnostico.respostas_ishikawa) == 6
    assert [r.categoria for r in diagnostico.respostas_ishikawa] == CATEGORIAS_ISHIKAWA_ORDEM
    assert len(diagnostico.cadeia_de_porques) == 5
    assert [p.numero for p in diagnostico.cadeia_de_porques] == [1, 2, 3, 4, 5]
    assert diagnostico.categoria_principal is not None
    assert diagnostico.causa_raiz
    assert diagnostico.ciclos_anteriores == []


def test_lote_aceitavel_nao_identifica_parametro_fora_da_faixa(fake_llm):
    diagnostico, _graph = rodar_investigacao_com_respostas(501, RESPOSTAS)
    assert diagnostico.nc.parametros_fora_da_faixa == []


def test_pedir_ajuste_preserva_ciclo_anterior_e_reinicia(fake_llm):
    diagnostico1, graph = rodar_investigacao_com_respostas(512, RESPOSTAS)

    ciclo_anterior = CicloAnterior(
        numero_ciclo=1,
        respostas_ishikawa=diagnostico1.respostas_ishikawa,
        categoria_principal=diagnostico1.categoria_principal,
        categorias_descartadas=diagnostico1.categorias_descartadas,
        cadeia_de_porques=diagnostico1.cadeia_de_porques,
        causa_raiz=diagnostico1.causa_raiz,
        encerrado_em=datetime.now(UTC),
    )

    diagnostico2, _graph = rodar_investigacao_com_respostas(
        512,
        RESPOSTAS,
        graph=graph,
        ciclos_anteriores=[ciclo_anterior],
    )

    assert len(diagnostico2.ciclos_anteriores) == 1
    assert diagnostico2.ciclos_anteriores[0].causa_raiz == diagnostico1.causa_raiz
    # o segundo ciclo tem sua própria cadeia completa, não reaproveita a do primeiro
    assert len(diagnostico2.respostas_ishikawa) == 6
    assert len(diagnostico2.cadeia_de_porques) == 5
