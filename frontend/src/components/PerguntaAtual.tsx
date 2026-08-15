import { useState } from "react";

import type { Pergunta } from "../api";
import { nomeParametro } from "../parametroLabel";

interface Props {
  pergunta: Pergunta;
  onResponder: (resposta: string) => void;
  processando: boolean;
}

export function PerguntaAtual({ pergunta, onResponder, processando }: Props) {
  const [resposta, setResposta] = useState("");

  function enviar() {
    if (!resposta.trim()) return;
    onResponder(resposta);
    setResposta("");
  }

  return (
    <div className="card section">
      <div>
        <p className="eyebrow">
          {pergunta.fase === "ishikawa"
            ? `Fase 1 · Pergunta ${pergunta.indice} de ${pergunta.total} · ${pergunta.categoria}`
            : `Fase 2 · Porquê ${pergunta.indice} de ${pergunta.total}`}
        </p>
        <h2>{pergunta.fase === "ishikawa" ? "Mapeamento Ishikawa" : "5 Porquês"}</h2>
      </div>
      {pergunta.erro && <p className="alert alert--critical">{pergunta.erro}</p>}

      <h3>Parâmetros do lote {pergunta.nc.batch_id}</h3>
      <table>
        <thead>
          <tr>
            <th>Parâmetro</th>
            <th>Média</th>
            <th>Mínimo</th>
            <th>Máximo</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {Object.values(pergunta.nc.sensor_metrics).map((m) => (
            <tr key={m.parametro}>
              <td>{nomeParametro(m.parametro)}</td>
              <td>
                {m.media.toFixed(1)} {m.unidade}
              </td>
              <td>
                {m.minimo.toFixed(1)} {m.unidade}
              </td>
              <td>
                {m.maximo.toFixed(1)} {m.unidade}
              </td>
              <td>
                <span className={`badge ${m.dentro_da_faixa ? "badge--ok" : "badge--critical"}`}>
                  {m.dentro_da_faixa ? "dentro da faixa" : "fora da faixa"}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <p>{pergunta.pergunta}</p>
      <textarea
        value={resposta}
        onChange={(e) => setResposta(e.target.value)}
        rows={4}
        aria-label="Resposta"
        disabled={processando}
      />
      <div className="actions">
        <button onClick={enviar} disabled={processando}>
          {processando ? "Enviando..." : "Responder"}
        </button>
      </div>
      {processando && (
        <div className="loading">
          <span className="spinner" aria-hidden="true" />
          <span>O agente está formulando a próxima pergunta — isso pode levar alguns instantes.</span>
        </div>
      )}
    </div>
  );
}
