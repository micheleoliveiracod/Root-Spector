import { useState } from "react";
import { baixarRelatorioJson, gerarRelatorioPdf, type Revisao } from "../api";

interface Props {
  revisao: Revisao;
  onAjustar: () => void;
  onReiniciar: () => void;
  processando: boolean;
}

export function RevisaoRespostas({ revisao, onAjustar, onReiniciar, processando }: Props) {
  const [gerandoPdf, setGerandoPdf] = useState(false);
  const [erroPdf, setErroPdf] = useState<string | null>(null);
  const [baixandoJson, setBaixandoJson] = useState(false);
  const [erroJson, setErroJson] = useState<string | null>(null);

  async function baixarPdf() {
    setGerandoPdf(true);
    setErroPdf(null);
    try {
      const blob = await gerarRelatorioPdf(revisao.thread_id);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${revisao.thread_id}_relatorio.pdf`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (erro) {
      setErroPdf(erro instanceof Error ? erro.message : "Falha ao gerar o relatório.");
    } finally {
      setGerandoPdf(false);
    }
  }

  async function baixarJson() {
    setBaixandoJson(true);
    setErroJson(null);
    try {
      const blob = await baixarRelatorioJson(revisao.relatorio.json);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${revisao.thread_id}_relatorio.json`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (erro) {
      setErroJson(erro instanceof Error ? erro.message : "Falha ao baixar o relatório.");
    } finally {
      setBaixandoJson(false);
    }
  }

  return (
    <div className="card section">
      <h2>Revisão da investigação</h2>

      <div className="callout">
        <strong>{revisao.categoria_principal.categoria}</strong>:{" "}
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
        <button onClick={baixarPdf} disabled={gerandoPdf}>
          {gerandoPdf ? "Gerando PDF..." : "Gerar relatório (PDF)"}
        </button>
        <button onClick={baixarJson} disabled={baixandoJson}>
          {baixandoJson ? "Baixando JSON..." : "Baixar JSON"}
        </button>
      </div>
      {erroPdf && <p className="alert alert--critical">{erroPdf}</p>}
      {erroJson && <p className="alert alert--critical">{erroJson}</p>}

      <div className="actions">
        <button onClick={onReiniciar}>Voltar à lista de lotes</button>
        <button className="secondary" onClick={onAjustar} disabled={processando}>
          {processando ? "Reabrindo ciclo..." : "Pedir ajuste"}
        </button>
      </div>
      {processando && (
        <div className="loading">
          <span className="spinner" aria-hidden="true" />
          <span>Reabrindo um novo ciclo de investigação, isso pode levar alguns instantes.</span>
        </div>
      )}
    </div>
  );
}
