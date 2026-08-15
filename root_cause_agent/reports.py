"""Diagnostico -> reports/{batch_id}_{timestamp}.json + .html (Jinja2).

O CSS inline abaixo usa os mesmos tokens de frontend/src/styles/tokens.css
e a mesma paleta "semáforo" pastel de frontend/src/statusBadge.ts -- ver
frontend/DESIGN.md. Duplicado (não importado do frontend) porque o
relatório é um HTML estático servido pelo backend, sem build step."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Template

from root_cause_agent.config import REPORTS_DIR
from root_cause_agent.models import Diagnostico

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


_TEMPLATE_HTML = Template(
    """<!doctype html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<title>Relatório de Causa Raiz — Lote {{ d.nc.batch_id }}</title>
<style>
  :root {
    --paper: #f3f6f5; --paper-raised: #ffffff; --ink: #14201f; --ink-soft: #47534f;
    --line: #d8e0dd; --accent: #0e8a82; --accent-ink: #08514c; --accent-soft: #e1f1ee;
    --shadow: 0 1px 2px rgba(20, 33, 32, 0.06), 0 8px 24px rgba(20, 33, 32, 0.06);
    --ok-bg: #e4f2e9; --ok-fg: #226a45;
    --warn-bg: #f6eedd; --warn-fg: #8a6423;
    --critical-bg: #fbeae6; --critical-fg: #a23b2e;
    --neutral-bg: #edefee; --neutral-fg: #666f6c;
    --font-serif: Charter, "Iowan Old Style", "Palatino Linotype", Georgia, "Noto Serif", serif;
    --font-sans: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    --font-mono: ui-monospace, "SF Mono", "Cascadia Code", Consolas, monospace;
    --radius: 10px; --radius-sm: 6px;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --paper: #10171a; --paper-raised: #16201f; --ink: #e7edea; --ink-soft: #a7b4af;
      --line: #253230; --accent: #38b4a9; --accent-ink: #9be0d6; --accent-soft: #12302d;
      --shadow: 0 1px 2px rgba(0, 0, 0, 0.4), 0 8px 24px rgba(0, 0, 0, 0.35);
      --ok-bg: #16302b; --ok-fg: #6fcb93;
      --warn-bg: #2e2a1b; --warn-fg: #d8c57e;
      --critical-bg: #2e1d1a; --critical-fg: #e0796a;
      --neutral-bg: #1e2624; --neutral-fg: #93a19c;
    }
  }
  * { box-sizing: border-box; }
  body {
    font-family: var(--font-sans); max-width: 720px; margin: 0 auto;
    padding: 48px 24px 96px; background: var(--paper); color: var(--ink);
    -webkit-font-smoothing: antialiased;
  }
  .eyebrow {
    font-family: var(--font-mono); font-size: 12px; letter-spacing: 0.08em;
    text-transform: uppercase; color: var(--accent-ink); margin: 0 0 6px;
  }
  h1 { font-family: var(--font-serif); font-size: clamp(26px, 3.6vw, 34px);
       margin: 0 0 24px; letter-spacing: -0.01em; text-wrap: balance; }
  h2 { font-family: var(--font-mono); font-size: 11px; letter-spacing: 0.06em;
       text-transform: uppercase; color: var(--ink-soft); margin: 28px 0 10px; }
  .card { background: var(--paper-raised); border: 1px solid var(--line);
          border-radius: var(--radius); box-shadow: var(--shadow); padding: 24px 26px; }
  .card + .card { margin-top: 16px; }
  .meta { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 4px; }
  .badge {
    display: inline-flex; align-items: center; gap: 5px; font-family: var(--font-mono);
    font-size: 11px; letter-spacing: 0.02em; padding: 3px 9px; border-radius: 100px;
    white-space: nowrap;
  }
  .badge::before { content: ""; width: 6px; height: 6px; border-radius: 50%;
                    background: currentColor; flex: none; }
  .badge--ok { background: var(--ok-bg); color: var(--ok-fg); }
  .badge--warn { background: var(--warn-bg); color: var(--warn-fg); }
  .badge--critical { background: var(--critical-bg); color: var(--critical-fg); }
  .badge--neutral { background: var(--neutral-bg); color: var(--neutral-fg); }
  .muted { color: var(--ink-soft); font-size: 13px; }
  table { border-collapse: collapse; width: 100%; font-size: 14px; }
  thead th { text-align: left; font-family: var(--font-mono); font-size: 10.5px;
             letter-spacing: 0.06em; text-transform: uppercase; color: var(--ink-soft);
             font-weight: 600; padding: 8px 12px; border-bottom: 1px solid var(--line); }
  tbody td { padding: 10px 12px; border-bottom: 1px solid var(--line); vertical-align: top; }
  tbody tr:last-child td { border-bottom: none; }
  .callout { background: var(--accent-soft); color: var(--accent-ink);
             border-radius: var(--radius-sm); padding: 14px 16px; font-size: 14.5px;
             line-height: 1.6; }
  .rodape { color: var(--ink-soft); font-size: 12px; margin-top: 32px; }
</style>
</head>
<body>
  <p class="eyebrow">Root-Spector</p>
  <h1>Relatório de causa raiz — Lote {{ d.nc.batch_id }}</h1>

  {% set cls = d.nc.classification.value %}
  {% set risco = d.nc.risk_prediction.value %}
  {% set fora_da_faixa = d.nc.parametros_fora_da_faixa | join(", ") or "nenhum" %}
  <div class="card">
    <div class="meta">
      <span class="badge badge--{{ badge(cls) }}">{{ cls }}</span>
      <span class="badge badge--{{ badge(risco) }}">{{ risco }}</span>
      <span class="muted">compliance_score={{ d.nc.compliance_score }}</span>
    </div>
    <p class="muted">Parâmetro(s) fora da faixa: {{ fora_da_faixa }}</p>

    <div class="callout">
      <strong>Causa raiz:</strong> {{ d.causa_raiz }}<br>
      <em>{{ d.narrativa }}</em>
    </div>

    <h2>Mapeamento Ishikawa</h2>
    <p>Categoria principal: <strong>{{ d.categoria_principal.categoria }}</strong>
       — {{ d.categoria_principal.justificativa }}</p>
    <table>
      <thead><tr><th>Categoria</th><th>Pergunta</th><th>Resposta</th></tr></thead>
      <tbody>
      {% for r in d.respostas_ishikawa %}
      <tr><td>{{ r.categoria }}</td><td>{{ r.pergunta }}</td><td>{{ r.resposta }}</td></tr>
      {% endfor %}
      </tbody>
    </table>
    {% if d.categorias_descartadas %}
    <p class="muted">Categorias descartadas:
      {% for c in d.categorias_descartadas %}{{ c.categoria }} ({{ c.motivo }})
      {{- ", " if not loop.last }}{% endfor %}
    </p>
    {% endif %}

    <h2>5 Porquês</h2>
    <table>
      <thead><tr><th>#</th><th>Pergunta</th><th>Resposta</th></tr></thead>
      <tbody>
      {% for p in d.cadeia_de_porques %}
      <tr><td>{{ p.numero }}</td><td>{{ p.pergunta }}</td><td>{{ p.resposta }}</td></tr>
      {% endfor %}
      </tbody>
    </table>

    {% if d.ciclos_anteriores %}
    <h2>Ciclos anteriores ({{ d.ciclos_anteriores | length }})</h2>
    {% for c in d.ciclos_anteriores %}
    <p>Ciclo {{ c.numero_ciclo }} (encerrado em {{ c.encerrado_em }}): {{ c.causa_raiz }}</p>
    {% endfor %}
    {% endif %}
  </div>

  <p class="rodape">Gerado em {{ d.gerado_em }}</p>
</body>
</html>
"""
)
_TEMPLATE_HTML.globals["badge"] = _badge


def salvar_relatorio(diagnostico: Diagnostico) -> tuple[Path, Path]:
    """Serializa o Diagnostico em JSON + HTML em REPORTS_DIR, nomeados
    {batch_id}_{timestamp}.{json,html}. Retorna os dois caminhos."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = diagnostico.gerado_em.strftime("%Y%m%dT%H%M%S")
    base = f"{diagnostico.nc.batch_id}_{ts}"

    json_path = REPORTS_DIR / f"{base}.json"
    json_path.write_text(diagnostico.model_dump_json(indent=2), encoding="utf-8")

    html_path = REPORTS_DIR / f"{base}.html"
    html_path.write_text(_TEMPLATE_HTML.render(d=diagnostico), encoding="utf-8")

    return json_path, html_path
