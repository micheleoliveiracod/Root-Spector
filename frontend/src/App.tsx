import { useState } from "react";

import * as api from "./api";
import type { Lote, Pergunta, Revisao } from "./api";
import { ListaLotes } from "./components/ListaLotes";
import { PerguntaAtual } from "./components/PerguntaAtual";
import { RevisaoRespostas } from "./components/RevisaoRespostas";

type Tela = "lista" | "pergunta" | "revisao";

export default function App() {
  const [tela, setTela] = useState<Tela>("lista");
  const [threadId, setThreadId] = useState<string | null>(null);
  const [pergunta, setPergunta] = useState<Pergunta | null>(null);
  const [revisao, setRevisao] = useState<Revisao | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [processando, setProcessando] = useState(false);

  async function escolherLote(lote: Lote) {
    setErro(null);
    setProcessando(true);
    try {
      const p = await api.iniciarInvestigacao(lote.batch_id);
      setThreadId(p.thread_id);
      setPergunta(p);
      setTela("pergunta");
    } catch (e) {
      setErro((e as Error).message);
    } finally {
      setProcessando(false);
    }
  }

  async function enviarResposta(resposta: string) {
    if (!threadId) return;
    setErro(null);
    setProcessando(true);
    try {
      const resultado = await api.responder(threadId, resposta);
      if ("status" in resultado && resultado.status === "pronto_para_revisao") {
        const r = await api.buscarRevisao(threadId);
        setRevisao(r);
        setTela("revisao");
      } else {
        setPergunta(resultado as Pergunta);
      }
    } catch (e) {
      setErro((e as Error).message);
    } finally {
      setProcessando(false);
    }
  }

  async function pedirAjuste() {
    if (!threadId) return;
    setErro(null);
    setProcessando(true);
    try {
      const p = await api.ajustar(threadId);
      setPergunta(p);
      setRevisao(null);
      setTela("pergunta");
    } catch (e) {
      setErro((e as Error).message);
    } finally {
      setProcessando(false);
    }
  }

  function reiniciar() {
    setTela("lista");
    setThreadId(null);
    setPergunta(null);
    setRevisao(null);
    setErro(null);
  }

  return (
    <main className="page">
      <header className="masthead">
        <p className="eyebrow">Root-Spector</p>
        <h1>Investigação de causa raiz</h1>
        <p className="dek">
          Mapeamento Ishikawa e 5 Porquês, conduzidos em conjunto com o operador.
        </p>
      </header>
      {erro && <p className="alert alert--critical">{erro}</p>}
      {tela === "lista" && <ListaLotes onEscolher={escolherLote} processando={processando} />}
      {tela === "pergunta" && pergunta && (
        <PerguntaAtual pergunta={pergunta} onResponder={enviarResposta} processando={processando} />
      )}
      {tela === "revisao" && revisao && (
        <RevisaoRespostas
          revisao={revisao}
          onAjustar={pedirAjuste}
          onReiniciar={reiniciar}
          processando={processando}
        />
      )}
    </main>
  );
}
