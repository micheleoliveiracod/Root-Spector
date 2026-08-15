import { useEffect, useState } from "react";

import { listarLotes, type Lote } from "../api";
import { nomeParametro } from "../parametroLabel";
import { badgeClass } from "../statusBadge";

interface Props {
  onEscolher: (lote: Lote) => void;
  processando: boolean;
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
            <th>Classificação</th>
            <th>Risco</th>
            <th>Parâmetro(s) fora da faixa</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {lotes.map((lote) => (
            <tr key={lote.batch_id}>
              <td>{lote.batch_id}</td>
              <td>
                <span className={`badge ${badgeClass(lote.classification)}`}>
                  {lote.classification}
                </span>
              </td>
              <td>
                <span className={`badge ${badgeClass(lote.risk_prediction)}`}>
                  {lote.risk_prediction}
                </span>
              </td>
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
          ))}
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
