import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { NaoConformidade, Pergunta } from "../api";
import { PerguntaAtual } from "./PerguntaAtual";

const NC: NaoConformidade = {
  batch_id: 511,
  upload_date: "2026-07-10T08:00:00+00:00",
  compliance_score: 38,
  classification: "CRITICAL",
  risk_prediction: "HIGH_RISK",
  sensor_metrics: {
    agitator_speed: {
      parametro: "agitator_speed",
      media: 74.4,
      minimo: 40.9,
      maximo: 99.8,
      unidade: "RPM",
      dentro_da_faixa: false,
    },
    temperature: {
      parametro: "temperature",
      media: 37.1,
      minimo: 36.5,
      maximo: 37.5,
      unidade: "C",
      dentro_da_faixa: true,
    },
  },
  parametros_fora_da_faixa: ["agitator_speed"],
};

const PERGUNTA: Pergunta = {
  thread_id: "511",
  pergunta: "O agitador recebeu manutenção preventiva?",
  nc: NC,
  fase: "ishikawa",
  indice: 2,
  total: 6,
  categoria: "Maquina",
};

describe("PerguntaAtual", () => {
  it("renderiza a pergunta e envia a resposta digitada", () => {
    const onResponder = vi.fn();
    render(<PerguntaAtual pergunta={PERGUNTA} onResponder={onResponder} processando={false} />);

    expect(screen.getByText(PERGUNTA.pergunta)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Resposta"), {
      target: { value: "Não, estava atrasada." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Responder" }));

    expect(onResponder).toHaveBeenCalledWith("Não, estava atrasada.");
  });

  it("não envia resposta vazia", () => {
    const onResponder = vi.fn();
    render(<PerguntaAtual pergunta={PERGUNTA} onResponder={onResponder} processando={false} />);

    fireEvent.click(screen.getByRole("button", { name: "Responder" }));

    expect(onResponder).not.toHaveBeenCalled();
  });

  it("mostra a mensagem de erro quando a Camada 1 rejeita a resposta anterior", () => {
    const comErro: Pergunta = { ...PERGUNTA, erro: "Este tipo de resposta não é aceito." };
    render(<PerguntaAtual pergunta={comErro} onResponder={() => {}} processando={false} />);

    expect(screen.getByText("Este tipo de resposta não é aceito.")).toBeInTheDocument();
  });

  it("mostra em qual categoria do Ishikawa o operador está", () => {
    render(<PerguntaAtual pergunta={PERGUNTA} onResponder={() => {}} processando={false} />);

    expect(screen.getByText("Fase 1 · Pergunta 2 de 6 · Maquina")).toBeInTheDocument();
  });

  it("mostra em qual dos 5 Porquês o operador está", () => {
    const porque: Pergunta = {
      ...PERGUNTA,
      fase: "porques",
      indice: 3,
      total: 5,
      categoria: undefined,
    };
    render(<PerguntaAtual pergunta={porque} onResponder={() => {}} processando={false} />);

    expect(screen.getByText("Fase 2 · Porquê 3 de 5")).toBeInTheDocument();
  });

  it("mostra o histórico dos parâmetros do lote, destacando o que está fora da faixa", () => {
    render(<PerguntaAtual pergunta={PERGUNTA} onResponder={() => {}} processando={false} />);

    expect(screen.getByText("Parâmetros do lote 511")).toBeInTheDocument();
    expect(screen.getByText("Velocidade do agitador")).toBeInTheDocument();
    expect(screen.getByText("Temperatura")).toBeInTheDocument();
    expect(screen.getByText("fora da faixa")).toBeInTheDocument();
    expect(screen.getByText("dentro da faixa")).toBeInTheDocument();
  });

  it("mostra indicador de carregamento e desabilita o formulário enquanto processa", () => {
    render(<PerguntaAtual pergunta={PERGUNTA} onResponder={() => {}} processando={true} />);

    expect(
      screen.getByText("O agente está formulando a próxima pergunta — isso pode levar alguns instantes."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Enviando..." })).toBeDisabled();
    expect(screen.getByLabelText("Resposta")).toBeDisabled();
  });
});
