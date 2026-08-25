"""RAG (retrieval-augmented generation): chunking + embedding + vector
store em memória sobre a base de conhecimento curada
(data/base_conhecimento/), consultada por pre_busca_rag para embasar
recomendar_tratativa (nodes.py). Ver specs/fase02/design.md § RAG.

Não é retrieval por palavra-chave: chunking real
(langchain-text-splitters), embedding de verdade
(GoogleGenerativeAIEmbeddings, reaproveitando GOOGLE_API_KEY) e busca por
similaridade semântica (InMemoryVectorStore.similarity_search)."""

from __future__ import annotations

import os
from functools import lru_cache

from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

from root_cause_agent.config import REPO_ROOT
from root_cause_agent.models import CandidatoRAG

BASE_CONHECIMENTO_DIR = REPO_ROOT / "data" / "base_conhecimento"

# Documentos curados: 1 por categoria Ishikawa (prática operacional) + 1
# por tópico metodológico/regulatório com referências bibliográficas
# reais (Ishikawa, 5 Porquês, CAPA/PDCA, legislação BPF/ANVISA,
# compliance e governança de dados) -- corpus pequeno mas real
# (specs/fase02/design.md § RAG).
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def _obter_embeddings():
    """LLM_PROVIDER=fake (mesmo sinal usado em todo o projeto para o LLM,
    ver config.py::get_llm) ativa DeterministicFakeEmbedding --
    determinístico, sem chamada de rede, usado em testes/CI. Nenhum teste
    automatizado chama a API real de embeddings, mesma regra já aplicada
    ao LLM (fake_llm.py)."""
    if os.getenv("LLM_PROVIDER") == "fake":
        from langchain_core.embeddings import DeterministicFakeEmbedding

        return DeterministicFakeEmbedding(size=768)

    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    # "models/text-embedding-004" (citado em specs/fase02/design.md, na
    # época da escrita do design) foi descontinuado pela Google --
    # confirmado via client.models.list() que só "models/gemini-embedding-001"
    # (estável) segue disponível para embedContent nesta conta/API.
    return GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")


@lru_cache
def _vector_store() -> InMemoryVectorStore:
    """Indexa toda data/base_conhecimento/*.md uma vez por processo,
    reconstruído no startup (mesmo padrão de carregar_regras_setor() em
    config.py) -- corpus pequeno o suficiente para não precisar persistir
    em disco."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    store = InMemoryVectorStore(_obter_embeddings())

    textos: list[str] = []
    metadados: list[dict] = []
    for caminho in sorted(BASE_CONHECIMENTO_DIR.glob("*.md")):
        for chunk in splitter.split_text(caminho.read_text(encoding="utf-8")):
            textos.append(chunk)
            metadados.append({"fonte": caminho.name})

    if textos:
        store.add_texts(textos, metadatas=metadados)
    return store


def limpar_cache() -> None:
    """Descarta o vector store indexado -- usado por testes que alternam
    LLM_PROVIDER entre chamadas, para não reaproveitar embeddings de um
    provedor diferente do configurado no momento da busca."""
    _vector_store.cache_clear()


def buscar_candidatos(categoria: str, resumo_nc: str, k: int = 3) -> list[CandidatoRAG]:
    """Busca semântica por similaridade na base de conhecimento, pela
    categoria Ishikawa principal + resumo da não-conformidade -- consulta
    real por significado, não correspondência exata de string."""
    query = f"Categoria: {categoria}. {resumo_nc}"
    resultados = _vector_store().similarity_search(query, k=k)
    return [
        CandidatoRAG(texto=doc.page_content, fonte=doc.metadata["fonte"]) for doc in resultados
    ]
