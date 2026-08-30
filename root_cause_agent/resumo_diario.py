"""Resumo diário de investigações (Fase 2, low-code, §4.9 do PDF, ver
specs/fase02/design.md § Low-code). Consumido pelo workflow n8n via
`GET /api/relatorios/resumo-diario` (backend/main.py). Nenhuma
dependência nova, nenhuma variável de ambiente nova no lado do
Root-Spector: o n8n é quem inicia a chamada, não o contrário.

Duas fontes de dados, ambas já existentes: a tabela `relatorios` (1
Diagnostico por investigação concluída, ver reports.py) e a tabela
`eventos_log` em OBSERVABILIDADE_DB_PATH (1 linha por evento, sinal 1 de
observabilidade e o callback de LLM, ver config.py). O banco também pode
ser consultado diretamente por uma ferramenta de BI, para análise
estatística além do que este módulo agrega."""

from __future__ import annotations

import os
import sqlite3
from collections import defaultdict
from datetime import date

from root_cause_agent.config import OBSERVABILIDADE_DB_PATH
from root_cause_agent.models import Diagnostico
from root_cause_agent.reports import listar_relatorios


def _diagnosticos_do_dia(dia: date) -> list[Diagnostico]:
    return [d for d in listar_relatorios() if d.gerado_em.date() == dia]


def _resumo_recorrencia(diagnostico: Diagnostico) -> str:
    if not diagnostico.casos_semelhantes:
        return "Primeiro caso registrado com esse padrão."
    n = len(diagnostico.casos_semelhantes)
    return f"{n} caso(s) semelhante(s) encontrado(s) anteriormente."


def _respostas_com_2_tentativas(diagnostico: Diagnostico) -> int:
    todas = diagnostico.respostas_ishikawa + diagnostico.cadeia_de_porques
    return sum(1 for r in todas if len(r.tentativas) == 2)


def _eventos_do_dia(dia: date, mensagem: str) -> list:
    """Lê da tabela eventos_log, filtrando pelo dia e pelo tipo de evento
    -- Postgres (a mesma instância do checkpointer, ver
    graph.py::_criar_checkpointer) quando `DATABASE_URL` estiver definida,
    SQLite local (OBSERVABILIDADE_DB_PATH) senão. O filtro por dia usa
    LIKE sobre o prefixo do timestamp ISO 8601 (`AAAA-MM-DD%`), em vez de
    uma função de data específica de cada banco, pra funcionar igual nos
    dois. Devolve lista vazia se o banco/tabela ainda não existir
    (processo novo, sem nenhum log gravado ainda), sem lançar exceção."""
    prefixo_dia = f"{dia.isoformat()}%"
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        import psycopg
        from psycopg.rows import dict_row

        try:
            with psycopg.connect(database_url, row_factory=dict_row) as conn:
                return conn.execute(
                    "SELECT * FROM eventos_log WHERE mensagem = %s AND timestamp LIKE %s",
                    (mensagem, prefixo_dia),
                ).fetchall()
        except psycopg.errors.UndefinedTable:
            return []

    if not OBSERVABILIDADE_DB_PATH.exists():
        return []
    conn = sqlite3.connect(str(OBSERVABILIDADE_DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(
            "SELECT * FROM eventos_log WHERE mensagem = ? AND timestamp LIKE ?",
            (mensagem, prefixo_dia),
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()


def _eficiencia_operacional(dia: date, diagnosticos: list[Diagnostico]) -> dict:
    """Agregada da tabela eventos_log do dia (nunca existiu em nenhum
    outro lugar do projeto antes da Fase 2): tempo médio por investigação,
    tempo médio por nó, quantas tentativas de LLM falharam antes do
    próximo provedor da cadeia de fallback assumir, e desempenho por
    provedor (chamadas, sucessos, falhas, duração média), para investigar
    problemas reais de fallback, não só contar quantas vezes ele foi
    acionado. Quem quiser ir além deste resumo pode consultar o banco
    direto com uma ferramenta de BI."""
    duracoes_por_no: dict[str, list[float]] = defaultdict(list)
    duracao_por_thread: dict[str, float] = defaultdict(float)
    for evento in _eventos_do_dia(dia, "no_executado"):
        duracoes_por_no[evento["no"]].append(evento["duracao_s"])
        # Soma por thread_id (uma execução de nó por vez, exceto o curto
        # fan-out formular_porque/pre_busca_rag) aproxima o tempo de
        # PROCESSAMENTO da investigação -- diferente do tempo de relógio
        # entre 1º e último evento, que incluiria o tempo de espera pela
        # resposta do operador, não é isso que "tempo médio de execução
        # por investigação" deveria significar.
        duracao_por_thread[evento["thread_id"]] += evento["duracao_s"]

    por_provedor: dict[str, dict[str, float]] = defaultdict(
        lambda: {"chamadas": 0, "sucessos": 0, "falhas": 0, "duracao_total_s": 0.0}
    )
    fallback_llm_acionado = 0
    for evento in _eventos_do_dia(dia, "chamada_llm"):
        stats = por_provedor[evento["provedor"]]
        stats["chamadas"] += 1
        stats["duracao_total_s"] += evento["duracao_s"]
        if evento["sucesso"]:
            stats["sucessos"] += 1
        else:
            stats["falhas"] += 1
            fallback_llm_acionado += 1

    tempo_medio_por_no = {
        no: round(sum(duracoes) / len(duracoes), 3) for no, duracoes in duracoes_por_no.items()
    }
    tempo_medio_investigacao_s = (
        round(sum(duracao_por_thread.values()) / len(duracao_por_thread), 3)
        if duracao_por_thread
        else 0.0
    )
    desempenho_llm_por_provedor = {
        provedor: {
            "chamadas": int(stats["chamadas"]),
            "sucessos": int(stats["sucessos"]),
            "falhas": int(stats["falhas"]),
            "duracao_media_s": (
                round(stats["duracao_total_s"] / stats["chamadas"], 3) if stats["chamadas"] else 0.0
            ),
        }
        for provedor, stats in por_provedor.items()
    }

    return {
        "tempo_medio_investigacao_s": tempo_medio_investigacao_s,
        "tempo_medio_por_no": tempo_medio_por_no,
        "fallback_llm_acionado": fallback_llm_acionado,
        "respostas_com_2_tentativas": sum(_respostas_com_2_tentativas(d) for d in diagnosticos),
        "desempenho_llm_por_provedor": desempenho_llm_por_provedor,
    }


def montar_resumo_diario(dia: date, base_url: str) -> dict:
    """Monta o payload completo do resumo diário -- ver
    specs/fase02/design.md § Low-code para o formato exato. `base_url` (ex:
    "http://localhost:8000") monta o link do PDF sob demanda de cada
    investigação, já que o PDF nunca é salvo em disco."""
    diagnosticos = _diagnosticos_do_dia(dia)

    investigacoes = [
        {
            "batch_id": d.nc.batch_id,
            "classification": d.nc.classification.value,
            "risk_prediction": d.nc.risk_prediction.value,
            "categoria_principal": d.categoria_principal.categoria,
            "causa_raiz": d.causa_raiz,
            "recorrencia": _resumo_recorrencia(d),
            "recomendacao_tratativa": d.recomendacao_tratativa,
            "link_relatorio_pdf": f"{base_url}/api/investigacoes/{d.nc.batch_id}/relatorio.pdf",
        }
        for d in diagnosticos
    ]

    return {
        "data": dia.isoformat(),
        "total_investigacoes": len(investigacoes),
        "investigacoes": investigacoes,
        "eficiencia_operacional": _eficiencia_operacional(dia, diagnosticos),
    }
