"""Diagnostico -> tabela `relatorios` (persistência, SQLite local ou
Postgres quando `DATABASE_URL` estiver definida, mesma instância do
checkpointer e do `eventos_log`) + PDF gerado sob demanda
(root_cause_agent.reports.gerar_pdf), nunca salvo em disco. O registro em
banco continua sendo a fonte de dados durável, usada tanto pela revisão
da investigação quanto pela tool `consultar_recorrencia`
(root_cause_agent/tools.py); o PDF é só uma representação de leitura,
recriada a cada pedido (backend/main.py::relatorio_pdf), o clique em
"Gerar relatório" no frontend."""

from __future__ import annotations

import io
import os
import sqlite3

from jinja2 import Template
from xhtml2pdf import pisa

from root_cause_agent.config import OBSERVABILIDADE_DB_PATH
from root_cause_agent.models import Diagnostico

_SQL_CRIAR_TABELA_RELATORIOS_SQLITE = """
CREATE TABLE IF NOT EXISTS relatorios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER NOT NULL,
    gerado_em TEXT NOT NULL,
    diagnostico_json TEXT NOT NULL
)
"""

_SQL_CRIAR_TABELA_RELATORIOS_POSTGRES = """
CREATE TABLE IF NOT EXISTS relatorios (
    id SERIAL PRIMARY KEY,
    batch_id INTEGER NOT NULL,
    gerado_em TEXT NOT NULL,
    diagnostico_json TEXT NOT NULL
)
"""

_BADGE_CLASSE = {
    "ACCEPTABLE": "ok",
    "LOW_RISK": "ok",
    "WARNING": "warn",
    "MEDIUM_RISK": "warn",
    "CRITICAL": "critical",
    "HIGH_RISK": "critical",
}


def _badge(valor: str) -> str:
    return _BADGE_CLASSE.get(valor, "neutral")


# CSS restrito ao que o xhtml2pdf (motor puro Python, sem dependência de
# sistema como o WeasyPrint exige) sabe renderizar: sem variáveis CSS, sem
# @media, sem flexbox. Paleta fixa clara (papel impresso não tem "modo
# escuro"), inspirada nos mesmos tons de frontend/src/styles/tokens.css.
_TEMPLATE_PDF = Template(
    """<html>
<head>
<style>
  @page { size: A4; margin: 2cm; }
  body { font-family: Helvetica, Arial, sans-serif; color: #14201f; font-size: 10.5pt; }
  .eyebrow { font-size: 9pt; letter-spacing: 2px; text-transform: uppercase; color: #08514c; }
  h1 { font-size: 19pt; margin-bottom: 4pt; }
  h2 { font-size: 11.5pt; text-transform: uppercase; color: #47534f;
       margin-top: 16pt; margin-bottom: 6pt; border-bottom: 1px solid #d8e0dd;
       padding-bottom: 3pt; }
  .badge { padding: 2pt 8pt; border-radius: 8pt; font-size: 8.5pt; margin-right: 4pt; }
  .badge-ok { background-color: #e4f2e9; color: #226a45; }
  .badge-warn { background-color: #f6eedd; color: #8a6423; }
  .badge-critical { background-color: #fbeae6; color: #a23b2e; }
  .badge-neutral { background-color: #edefee; color: #666f6c; }
  .muted { color: #47534f; font-size: 9pt; }
  .callout { background-color: #e1f1ee; color: #08514c; padding: 8pt;
             border-radius: 4pt; font-size: 10pt; }
  table { width: 100%; border-collapse: collapse; font-size: 9.5pt; margin-top: 4pt; }
  th { text-align: left; text-transform: uppercase; font-size: 8pt; color: #47534f;
       border-bottom: 1px solid #d8e0dd; padding: 4pt; }
  td { padding: 4pt; border-bottom: 1px solid #eef1f0; vertical-align: top; }
  .rodape { color: #8a938f; font-size: 8pt; margin-top: 20pt; }
</style>
</head>
<body>
  <p class="eyebrow">Root-Spector</p>
  <h1>Relatorio de causa raiz, lote {{ d.nc.batch_id }}</h1>

  {% set cls = d.nc.classification.value %}
  {% set risco = d.nc.risk_prediction.value %}
  {% set fora_da_faixa = d.nc.parametros_fora_da_faixa | join(", ") or "nenhum" %}
  <p>
    <span class="badge badge-{{ badge(cls) }}">{{ cls }}</span>
    <span class="badge badge-{{ badge(risco) }}">{{ risco }}</span>
    <span class="muted">compliance_score={{ d.nc.compliance_score }}</span>
  </p>
  <p class="muted">Parametro(s) fora da faixa: {{ fora_da_faixa }}</p>

  <div class="callout">
    <strong>Causa raiz:</strong> {{ d.causa_raiz }}<br/>
    <i>{{ d.narrativa }}</i>
  </div>

  <h2>Mapeamento Ishikawa</h2>
  <p>Categoria principal: <strong>{{ d.categoria_principal.categoria }}</strong>,
     {{ d.categoria_principal.justificativa }}</p>
  <table>
    <tr><th>Categoria</th><th>Pergunta</th><th>Resposta</th></tr>
    {% for r in d.respostas_ishikawa %}
    <tr><td>{{ r.categoria }}</td><td>{{ r.pergunta }}</td><td>{{ r.resposta }}</td></tr>
    {% endfor %}
  </table>
  {% if d.categorias_descartadas %}
  <p class="muted">Categorias descartadas:
    {% for c in d.categorias_descartadas %}{{ c.categoria }} ({{ c.motivo }})
    {{- ", " if not loop.last }}{% endfor %}
  </p>
  {% endif %}

  <h2>5 Porques</h2>
  <table>
    <tr><th>#</th><th>Pergunta</th><th>Resposta</th></tr>
    {% for p in d.cadeia_de_porques %}
    <tr><td>{{ p.numero }}</td><td>{{ p.pergunta }}</td><td>{{ p.resposta }}</td></tr>
    {% endfor %}
  </table>

  {% if d.recomendacao_tratativa %}
  <h2>Recomendacao de tratativa</h2>
  <div class="callout">{{ d.recomendacao_tratativa }}</div>
  {% if d.fontes_rag %}
  <p class="muted">Fontes consultadas: {{ d.fontes_rag | join(", ") }}</p>
  {% endif %}
  {% endif %}

  {% if d.casos_semelhantes %}
  <h2>Recorrencia</h2>
  <table>
    <tr><th>Lote</th><th>Categoria</th><th>Causa raiz</th><th>Gerado em</th></tr>
    {% for c in d.casos_semelhantes %}
    <tr><td>{{ c.batch_id }}</td><td>{{ c.categoria_principal }}</td>
        <td>{{ c.causa_raiz }}</td><td>{{ c.gerado_em }}</td></tr>
    {% endfor %}
  </table>
  {% endif %}

  {% if d.ciclos_anteriores %}
  <h2>Ciclos anteriores ({{ d.ciclos_anteriores | length }})</h2>
  {% for c in d.ciclos_anteriores %}
  <p>Ciclo {{ c.numero_ciclo }} (encerrado em {{ c.encerrado_em }}): {{ c.causa_raiz }}</p>
  {% endfor %}
  {% endif %}

  <p class="rodape">Gerado em {{ d.gerado_em }}</p>
</body>
</html>
"""
)
_TEMPLATE_PDF.globals["badge"] = _badge


def gerar_pdf(diagnostico: Diagnostico) -> bytes:
    """Renderiza o Diagnostico em PDF, inteiramente em memória, sem tocar
    disco -- chamada sob demanda (backend/main.py), não no fim automático
    da investigação. Levanta ValueError se o xhtml2pdf reportar erro de
    renderização."""
    buffer = io.BytesIO()
    resultado = pisa.CreatePDF(src=_TEMPLATE_PDF.render(d=diagnostico), dest=buffer)
    if resultado.err:
        raise ValueError(f"Falha ao gerar PDF do relatório ({resultado.err} erro(s)).")
    return buffer.getvalue()


def salvar_relatorio(diagnostico: Diagnostico) -> int:
    """Grava o Diagnostico como 1 registro na tabela `relatorios`, SQLite
    local (OBSERVABILIDADE_DB_PATH) por padrão, Postgres, a mesma
    instância do checkpointer e do `eventos_log`, quando `DATABASE_URL`
    estiver definida -- única persistência do relatório; o PDF nunca é
    salvo, só gerado sob demanda (ver gerar_pdf). Retorna o id do
    registro criado."""
    linha = (
        diagnostico.nc.batch_id,
        diagnostico.gerado_em.isoformat(),
        diagnostico.model_dump_json(),
    )
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        import psycopg

        with psycopg.connect(database_url) as conn:
            conn.execute(_SQL_CRIAR_TABELA_RELATORIOS_POSTGRES)
            cursor = conn.execute(
                "INSERT INTO relatorios (batch_id, gerado_em, diagnostico_json) "
                "VALUES (%s, %s, %s) RETURNING id",
                linha,
            )
            relatorio_id = cursor.fetchone()[0]
            conn.commit()
        return relatorio_id

    OBSERVABILIDADE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(OBSERVABILIDADE_DB_PATH))
    try:
        conn.execute(_SQL_CRIAR_TABELA_RELATORIOS_SQLITE)
        cursor = conn.execute(
            "INSERT INTO relatorios (batch_id, gerado_em, diagnostico_json) VALUES (?, ?, ?)",
            linha,
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def buscar_relatorio(relatorio_id: int) -> Diagnostico | None:
    """Lê 1 registro da tabela `relatorios` pelo id -- usado pela rota
    `GET /api/relatorios/{relatorio_id}` (backend/main.py), no lugar do
    antigo `GET /reports/{arquivo}` estático. Devolve None se o id não
    existir ou se a tabela ainda não tiver sido criada."""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        import psycopg

        try:
            with psycopg.connect(database_url) as conn:
                linha = conn.execute(
                    "SELECT diagnostico_json FROM relatorios WHERE id = %s", (relatorio_id,)
                ).fetchone()
        except psycopg.errors.UndefinedTable:
            return None
        if linha is None:
            return None
        return Diagnostico.model_validate_json(linha[0])

    if not OBSERVABILIDADE_DB_PATH.exists():
        return None
    conn = sqlite3.connect(str(OBSERVABILIDADE_DB_PATH))
    try:
        linha = conn.execute(
            "SELECT diagnostico_json FROM relatorios WHERE id = ?", (relatorio_id,)
        ).fetchone()
    except sqlite3.OperationalError:
        return None
    finally:
        conn.close()
    if linha is None:
        return None
    return Diagnostico.model_validate_json(linha[0])


def listar_relatorios() -> list[Diagnostico]:
    """Lê todos os registros da tabela `relatorios` -- usado pela tool
    `consultar_recorrencia` (tools.py) e pelo resumo diário
    (resumo_diario.py), no lugar de varrer `reports/*.json` em disco.
    Devolve lista vazia se a tabela ainda não tiver sido criada (processo
    novo, nenhum relatório salvo ainda)."""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        import psycopg

        try:
            with psycopg.connect(database_url) as conn:
                linhas = conn.execute("SELECT diagnostico_json FROM relatorios").fetchall()
        except psycopg.errors.UndefinedTable:
            return []
        return [Diagnostico.model_validate_json(linha[0]) for linha in linhas]

    if not OBSERVABILIDADE_DB_PATH.exists():
        return []
    conn = sqlite3.connect(str(OBSERVABILIDADE_DB_PATH))
    try:
        linhas = conn.execute("SELECT diagnostico_json FROM relatorios").fetchall()
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()
    return [Diagnostico.model_validate_json(linha[0]) for linha in linhas]
