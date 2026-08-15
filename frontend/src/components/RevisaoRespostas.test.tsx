import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { Revisao } from "../api";
import { RevisaoRespostas } from "./RevisaoRespostas";

const REVISAO: Revisao = {
  thread_id: "511",
  respostas_ishikawa: [{ categoria: "Maquina", pergunta: "P?", resposta: "R." }],
  categoria_principal: { categoria: "Maquina", justificativa: "Falta de manutenção preventiva." },
  categorias_descartadas: [{ categoria: "Metodo", motivo: "Procedimento padrão confirmado." }],
  cadeia_de_porques: [{ numero: 1, pergunta: "Por quê?", resposta: "Porque sim." }],
  causa_raiz: "Ausência de verificação de manutenção preventiva.",
  narrativa: "O agitador não foi verificado a tempo.",
  relatorio: {
    json: "/reports/511_20260718T000000.json",
    html: "/reports/511_20260718T000000.html",
  },
};

describe("RevisaoRespostas", () => {
  it("renderiza a cadeia completa (Ishikawa + 5 Porquês + causa raiz)", () => {
    render(<RevisaoRespostas revisao={REVISAO} onAjustar={() => {}} onReiniciar={() => {}} processando={false} />);

    expect(screen.getAllByText(/Maquina/).length).toBeGreaterThan(0);
    expect(screen.getByText(/Por quê\?/)).toBeInTheDocument();
    expect(screen.getByText(REVISAO.causa_raiz)).toBeInTheDocument();
  });

  it("renderiza os links do relatório apontando pro backend", () => {
    render(<RevisaoRespostas revisao={REVISAO} onAjustar={() => {}} onReiniciar={() => {}} processando={false} />);

    const linkHtml = screen.getByRole("link", { name: "Ver relatório (HTML)" });
    const linkJson = screen.getByRole("link", { name: "Baixar JSON" });

    expect(linkHtml).toHaveAttribute("href", `http://localhost:8000${REVISAO.relatorio.html}`);
    expect(linkJson).toHaveAttribute("href", `http://localhost:8000${REVISAO.relatorio.json}`);
  });

  it("chama onReiniciar e onAjustar nos respectivos botões", () => {
    const onReiniciar = vi.fn();
    const onAjustar = vi.fn();
    render(
      <RevisaoRespostas
        revisao={REVISAO}
        onAjustar={onAjustar}
        onReiniciar={onReiniciar}
        processando={false}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Voltar à lista de lotes" }));
    fireEvent.click(screen.getByRole("button", { name: "Pedir ajuste" }));

    expect(onReiniciar).toHaveBeenCalledTimes(1);
    expect(onAjustar).toHaveBeenCalledTimes(1);
  });

  it("mostra indicador de carregamento e desabilita Pedir ajuste enquanto processa", () => {
    render(
      <RevisaoRespostas
        revisao={REVISAO}
        onAjustar={() => {}}
        onReiniciar={() => {}}
        processando={true}
      />,
    );

    expect(screen.getByRole("button", { name: "Reabrindo ciclo..." })).toBeDisabled();
    expect(
      screen.getByText("Reabrindo um novo ciclo de investigação — isso pode levar alguns instantes."),
    ).toBeInTheDocument();
  });
});
