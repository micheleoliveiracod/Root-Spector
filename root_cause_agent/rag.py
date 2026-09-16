"""RAG (retrieval-augmented generation): chunking + embedding + vector
store sobre a base de conhecimento curada (data/base_conhecimento/),
consultada por pre_busca_rag para embasar recomendar_tratativa
(nodes.py). Ver specs/fase02/design.md § RAG.

Não é retrieval por palavra-chave: chunking real
(langchain-text-splitters), embedding de verdade
(GoogleGenerativeAIEmbeddings, reaproveitando GOOGLE_API_KEY) e busca por
similaridade semântica (.similarity_search).

Armazenamento: `InMemoryVectorStore` local por padrão, reconstruído (e
reembedado) a cada início de processo -- corpus pequeno o suficiente pra
não incomodar em desenvolvimento. Quando `DATABASE_URL` estiver definida
(mesma instância Postgres do checkpointer e do eventos_log, ver
config.py/graph.py), os embeddings passam a ser persistidos em `PGVector`
(`langchain-postgres`), e só são regerados quando o conteúdo de
data/base_conhecimento/ muda de fato (hash comparado contra
rag_indice_hash), não a cada reinício."""

from __future__ import annotations

import hashlib
import os
from functools import lru_cache
from pathlib import Path

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

# Nome da coleção no Postgres (langchain-postgres agrupa os embeddings por
# `collection_name`) e da tabela que guarda o hash do corpus já indexado
# nela, pra decidir se precisa reindexar ou só reaproveitar o que já está
# persistido.
_COLECAO_RAG = "root_spector_base_conhecimento"
_SQL_CRIAR_TABELA_INDICE_HASH = """
CREATE TABLE IF NOT EXISTS rag_indice_hash (
    colecao TEXT PRIMARY KEY,
    hash TEXT NOT NULL
)
"""


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


def _hash_base_conhecimento() -> str:
    """Hash determinístico do conteúdo atual de data/base_conhecimento/
    (nome + bytes de cada arquivo, em ordem alfabética) -- usado só pelo
    backend Postgres, pra saber se o índice já persistido continua
    correspondendo aos arquivos .md de verdade ou se precisa reindexar."""
    hasher = hashlib.sha256()
    for caminho in sorted(BASE_CONHECIMENTO_DIR.glob("*.md")):
        hasher.update(caminho.name.encode("utf-8"))
        hasher.update(caminho.read_bytes())
    return hasher.hexdigest()


def _chunkear_base_conhecimento(caminho_dir: Path) -> tuple[list[str], list[dict]]:
    """Percorre *.md em ordem alfabética e aplica o splitter, registrando
    o arquivo de origem como metadado (`fonte`) -- compartilhado pelos
    dois backends de armazenamento (memória e Postgres)."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    textos: list[str] = []
    metadados: list[dict] = []
    for caminho in sorted(caminho_dir.glob("*.md")):
        for chunk in splitter.split_text(caminho.read_text(encoding="utf-8")):
            textos.append(chunk)
            metadados.append({"fonte": caminho.name})
    return textos, metadados


def _vector_store_memoria() -> InMemoryVectorStore:
    """Indexa toda data/base_conhecimento/*.md uma vez por processo,
    reconstruído no startup (mesmo padrão de carregar_regras_setor() em
    config.py) -- corpus pequeno o suficiente para não incomodar em
    desenvolvimento, quando não há Postgres configurado."""
    store = InMemoryVectorStore(_obter_embeddings())
    textos, metadados = _chunkear_base_conhecimento(BASE_CONHECIMENTO_DIR)
    if textos:
        store.add_texts(textos, metadatas=metadados)
    return store


def _url_para_sqlalchemy(database_url: str) -> str:
    """PGVector usa SQLAlchemy internamente, que por padrão resolve um
    esquema `postgresql://` puro para o driver `psycopg2` -- não instalado
    neste projeto (a dependência real é `psycopg` v3, `psycopg[binary,pool]`
    em pyproject.toml, usado diretamente por psycopg.connect() acima e pelo
    checkpointer em graph.py::_criar_checkpointer). Sem essa troca de
    esquema, a 1ª chamada a PGVector() falha com `ModuleNotFoundError: No
    module named 'psycopg2'` assim que uma investigação real chega em
    pre_busca_rag."""
    if database_url.startswith("postgresql://"):
        return "postgresql+psycopg://" + database_url[len("postgresql://") :]
    return database_url


def _vector_store_postgres(database_url: str):
    """PGVector (`langchain-postgres`) sobre a mesma instância apontada
    por DATABASE_URL (checkpointer, eventos_log -- ver graph.py/config.py).
    Reindexa (chunking + chamadas reais de embedding) só quando o hash do
    corpus atual difere do último hash persistido em `rag_indice_hash`;
    caso contrário, reaproveita a coleção já existente sem gerar nenhum
    embedding novo, mesmo que o processo tenha acabado de subir."""
    import psycopg
    from langchain_postgres import PGVector

    hash_atual = _hash_base_conhecimento()
    with psycopg.connect(database_url, autocommit=True) as conn:
        conn.execute(_SQL_CRIAR_TABELA_INDICE_HASH)
        linha = conn.execute(
            "SELECT hash FROM rag_indice_hash WHERE colecao = %s", (_COLECAO_RAG,)
        ).fetchone()
        hash_persistido = linha[0] if linha else None
        precisa_reindexar = hash_persistido != hash_atual

        # pre_delete_collection=True apaga a coleção anterior antes de
        # recriá-la -- só quando o corpus mudou de fato, nunca no caminho
        # "hash igual", que só reabre a coleção já persistida.
        store = PGVector(
            embeddings=_obter_embeddings(),
            collection_name=_COLECAO_RAG,
            connection=_url_para_sqlalchemy(database_url),
            use_jsonb=True,
            pre_delete_collection=precisa_reindexar,
        )

        if precisa_reindexar:
            textos, metadados = _chunkear_base_conhecimento(BASE_CONHECIMENTO_DIR)
            if textos:
                store.add_texts(textos, metadatas=metadados)
            conn.execute(
                "INSERT INTO rag_indice_hash (colecao, hash) VALUES (%s, %s) "
                "ON CONFLICT (colecao) DO UPDATE SET hash = EXCLUDED.hash",
                (_COLECAO_RAG, hash_atual),
            )
    return store


@lru_cache
def _vector_store():
    """SqliteSaver-like: memória por padrão, Postgres quando `DATABASE_URL`
    estiver definida (mesmo sinal do checkpointer, ver
    graph.py::_criar_checkpointer). Cacheado por processo (`lru_cache`),
    então mesmo no backend Postgres a consulta ao hash acontece só uma vez
    por processo, não a cada chamada de buscar_candidatos()."""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return _vector_store_postgres(database_url)
    return _vector_store_memoria()


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
