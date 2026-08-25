"""Testes de root_cause_agent/rag.py: retrieval por similaridade sobre a
base de conhecimento curada (data/base_conhecimento/), usando
DeterministicFakeEmbedding (fixture `embeddings_fake`, conftest.py) --
nunca chama a API real de embeddings."""

from __future__ import annotations

import pytest

from root_cause_agent import rag

pytestmark = pytest.mark.usefixtures("embeddings_fake")

CATEGORIAS_ISHIKAWA = [
    "Metodo",
    "Maquina",
    "Material",
    "Mao de obra",
    "Meio ambiente",
    "Medicao",
]


@pytest.mark.parametrize("categoria", CATEGORIAS_ISHIKAWA)
def test_busca_retorna_candidatos_para_cada_categoria_ishikawa(categoria):
    candidatos = rag.buscar_candidatos(categoria, "lote com parâmetro fora da faixa")
    assert candidatos
    assert all(c.texto for c in candidatos)
    assert all(c.fonte.endswith(".md") for c in candidatos)


def test_busca_respeita_k():
    candidatos = rag.buscar_candidatos("Maquina", "resumo qualquer", k=1)
    assert len(candidatos) == 1


def test_base_de_conhecimento_tem_multiplos_documentos_indexados():
    store = rag._vector_store()
    fontes = {item["metadata"]["fonte"] for item in store.store.values()}
    # 1 documento por categoria Ishikawa + 1 de metodologia CAPA/PDCA
    assert len(fontes) >= 6


def test_limpar_cache_forca_reindexacao():
    rag.buscar_candidatos("Metodo", "resumo")
    assert rag._vector_store.cache_info().currsize == 1
    rag.limpar_cache()
    assert rag._vector_store.cache_info().currsize == 0
