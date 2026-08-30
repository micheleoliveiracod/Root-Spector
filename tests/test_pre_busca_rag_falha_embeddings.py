"""Regressão: bug real encontrado testando o agente em produção (Groq e
Gemini). embed_documents/embed_query (langchain_google_genai, usado por
root_cause_agent/rag.py) chama a API de embeddings do Gemini sempre,
independente de LLM_PROVIDER -- não faz parte da cadeia de fallback de
get_llm(). Um erro ali (cota esgotada, rede) derrubava a investigação
inteira com um 500 cru, bem na transição Ishikawa -> orquestrar_analise
(fan-out pre_busca_rag), sem nenhum tratamento. Ver nodes.py::pre_busca_rag.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from root_cause_agent import nodes
from root_cause_agent.models import (
    CategoriaAnalise,
    Classification,
    NaoConformidade,
    RiskPrediction,
)

NC = NaoConformidade(
    batch_id=511,
    upload_date=datetime(2026, 7, 10, tzinfo=UTC),
    compliance_score=38.0,
    classification=Classification.CRITICAL,
    risk_prediction=RiskPrediction.HIGH_RISK,
    sensor_metrics={},
    parametros_fora_da_faixa=["agitator_speed"],
)

STATE = {
    "nc_input": NC,
    "categoria_principal": CategoriaAnalise(categoria="Maquina", justificativa="teste"),
}


def test_pre_busca_rag_degrada_para_vazio_quando_embeddings_falha(monkeypatch):
    def _falha(*args, **kwargs):
        raise RuntimeError("429 RESOURCE_EXHAUSTED (simulado)")

    monkeypatch.setattr(nodes, "buscar_candidatos", _falha)

    resultado = nodes.pre_busca_rag(STATE)

    assert resultado == {"candidatos_rag": []}


def test_pre_busca_rag_devolve_candidatos_normalmente_quando_embeddings_funciona(monkeypatch):
    from root_cause_agent.models import CandidatoRAG

    esperado = [CandidatoRAG(texto="trecho relevante", fonte="maquina.md")]
    monkeypatch.setattr(nodes, "buscar_candidatos", lambda categoria, resumo: esperado)

    resultado = nodes.pre_busca_rag(STATE)

    assert resultado == {"candidatos_rag": esperado}


@pytest.mark.usefixtures("fake_llm")
def test_investigacao_completa_mesmo_com_rag_fora_do_ar(monkeypatch):
    """Fim a fim: com embeddings sempre falhando, a investigação ainda
    chega a um Diagnostico válido, só sem candidatos_rag/fontes_rag --
    RAG é um reforço (recomendar_tratativa já degrada graciosamente, ver
    nodes.py), nunca deveria travar Ishikawa/5-Porques/causa_raiz."""
    from root_cause_agent.main import rodar_investigacao_com_respostas

    def _falha(*args, **kwargs):
        raise RuntimeError("429 RESOURCE_EXHAUSTED (simulado)")

    monkeypatch.setattr(nodes, "buscar_candidatos", _falha)

    respostas = [f"resposta {i}" for i in range(11)]
    diagnostico, _graph = rodar_investigacao_com_respostas(511, respostas)

    assert diagnostico.causa_raiz
    assert diagnostico.fontes_rag == []
    assert diagnostico.recomendacao_tratativa
