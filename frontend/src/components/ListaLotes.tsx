import { useEffect, useState } from "react";

import { listarLotes, type Lote } from "../api";
import { nomeParametro } from "../parametroLabel";
import { estadoLote } from "../statusBadge";

interface Props {
  onEscolher: (lote: Lote) => void;
  processando: boolean;
}

// classificação e predição de risco às vezes divergem em severidade; a
// situação mostrada ao operador usa a pior das duas, mas os dois códigos
// técnicos originais continuam visíveis em .estado-codigo.
const SEVERIDADE: Record<string, number> = {
  "estado--critical": 3,
  "estado--warn": 2,
  "estado--ok": 1,
  "estado--neutral": 0,
};

function situacaoLote(lote: Lote) {
  const porClassificacao = estadoLote(lote.classification);
  const porRisco = estadoLote(lote.risk_prediction);
  const pior =
    SEVERIDADE[porRisco.classe] > SEVERIDADE[porClassificacao.classe] ? porRisco : porClassificacao;
  return { ...pior, codigo: `${lote.classification} / ${lote.risk_prediction}` };
}

export function ListaLotes({ onEscolher, processando }: Props) {
  const [lotes, setLotes] = useState<Lote[]>([]);
  const [carregando, setCarregando] = useState(true);

  useEffect(() => {
    listarLotes().then((dados) => {
      setLotes(dados);
      setCarregando(false);
    });
  }, []);

  if (carregando) {
    return (
      <div className="card">
        <p className="muted">Carregando lotes...</p>
      </div>
    );
  }

  return (
    <div className="card section">
      <h2>Lotes</h2>
      <table>
        <thead>
          <tr>
            <th>Lote</th>
            <th>Situação</th>
            <th>O que fazer</th>
            <th>Parâmetro(s) fora da faixa</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {lotes.map((lote) => {
            const situacao = situacaoLote(lote);
            return (
              <tr key={lote.batch_id}>
                <td>{lote.batch_id}</td>
                <td>
                  <span className={`estado ${situacao.classe}`}>{situacao.rotulo}</span>
                  <span className="estado-codigo">{situacao.codigo}</span>
                </td>
                <td>{situacao.acao}</td>
                <td>
                  {lote.parametros_fora_da_faixa.length > 0 ? (
                    lote.parametros_fora_da_faixa.map(nomeParametro).join(", ")
                  ) : (
                    <span className="muted">—</span>
                  )}
                </td>
                <td>
                  {lote.elegivel ? (
                    <button onClick={() => onEscolher(lote)} disabled={processando}>
                      Investigar
                    </button>
                  ) : (
                    <span className="muted">não elegível</span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      {processando && (
        <div className="loading">
          <span className="spinner" aria-hidden="true" />
          <span>Iniciando a investigação com o agente — isso pode levar alguns instantes.</span>
        </div>
      )}
    </div>
  );
}
