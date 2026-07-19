import type { Revisao } from "../api";

interface Props {
  revisao: Revisao;
  onAjustar: () => void;
  onReiniciar: () => void;
  processando: boolean;
}

export function RevisaoRespostas({ revisao, onAjustar, onReiniciar, processando }: Props) {
  return (
    <div className="card section">
      <h2>Revisão da investigação</h2>

      <div className="callout">
        <strong>{revisao.categoria_principal.categoria}</strong> —{" "}
        {revisao.categoria_principal.justificativa}
      </div>

      <h3>Ishikawa</h3>
      <ul className="qa-list">
        {revisao.respostas_ishikawa.map((r) => (
          <li key={r.categoria}>
            <span className="categoria">{r.categoria}</span>
            {r.pergunta} → {r.resposta}
          </li>
        ))}
      </ul>
      {revisao.categorias_descartadas.length > 0 && (
        <p className="muted">
          Categorias descartadas:{" "}
          {revisao.categorias_descartadas.map((c, i) => (
            <span key={c.categoria}>
              {i > 0 && ", "}
              {c.categoria} ({c.motivo})
            </span>
          ))}
        </p>
      )}

      <h3>5 Porquês</h3>
      <ul className="qa-list">
        {revisao.cadeia_de_porques.map((p) => (
          <li key={p.numero}>
            <span className="categoria">Porquê {p.numero}</span>
            {p.pergunta} → {p.resposta}
          </li>
        ))}
      </ul>

      <h3>Causa raiz</h3>
      <p>{revisao.causa_raiz}</p>
      <p className="muted">{revisao.narrativa}</p>

      <h3>Relatório</h3>
      <div className="report-links">
        <a href={`http://localhost:8000${revisao.relatorio.html}`} target="_blank" rel="noreferrer">
          Ver relatório (HTML)
        </a>
        <a href={`http://localhost:8000${revisao.relatorio.json}`} target="_blank" rel="noreferrer">
          Baixar JSON
        </a>
      </div>

      <div className="actions">
        <button onClick={onReiniciar}>Voltar à lista de lotes</button>
        <button className="secondary" onClick={onAjustar} disabled={processando}>
          {processando ? "Reabrindo ciclo..." : "Pedir ajuste"}
        </button>
      </div>
      {processando && (
        <div className="loading">
          <span className="spinner" aria-hidden="true" />
          <span>Reabrindo um novo ciclo de investigação — isso pode levar alguns instantes.</span>
        </div>
      )}
    </div>
  );
}
