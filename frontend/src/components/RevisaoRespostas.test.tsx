import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import * as api from "../api";
import type { Revisao } from "../api";
import { RevisaoRespostas } from "./RevisaoRespostas";

vi.mock("../api");

const REVISAO: Revisao = {
  thread_id: "511",
  respostas_ishikawa: [{ categoria: "Maquina", pergunta: "P?", resposta: "R." }],
  categoria_principal: { categoria: "Maquina", justificativa: "Falta de manutenção preventiva." },
  categorias_descartadas: [{ categoria: "Metodo", motivo: "Procedimento padrão confirmado." }],
  cadeia_de_porques: [{ numero: 1, pergunta: "Por quê?", resposta: "Porque sim." }],
  causa_raiz: "Ausência de verificação de manutenção preventiva.",
  narrativa: "O agitador não foi verificado a tempo.",
  relatorio: {
    json: "/api/relatorios/42",
  },
};

describe("RevisaoRespostas", () => {
  it("renderiza a cadeia completa (Ishikawa + 5 Porquês + causa raiz)", () => {
    render(<RevisaoRespostas revisao={REVISAO} onAjustar={() => {}} onReiniciar={() => {}} processando={false} />);

    expect(screen.getAllByText(/Maquina/).length).toBeGreaterThan(0);
    expect(screen.getByText(/Por quê\?/)).toBeInTheDocument();
    expect(screen.getByText(REVISAO.causa_raiz)).toBeInTheDocument();
  });

  it("baixa o JSON ao clicar em Baixar JSON", async () => {
    const blob = new Blob(['{"causa_raiz": "teste"}'], { type: "application/json" });
    vi.mocked(api.baixarRelatorioJson).mockResolvedValue(blob);
    const criarUrl = vi.fn().mockReturnValue("blob:url-de-teste");
    const revogarUrl = vi.fn();
    URL.createObjectURL = criarUrl;
    URL.revokeObjectURL = revogarUrl;
    const cliqueLink = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});

    render(<RevisaoRespostas revisao={REVISAO} onAjustar={() => {}} onReiniciar={() => {}} processando={false} />);

    fireEvent.click(screen.getByRole("button", { name: "Baixar JSON" }));

    await waitFor(() => expect(api.baixarRelatorioJson).toHaveBeenCalledWith(REVISAO.relatorio.json));
    expect(criarUrl).toHaveBeenCalledWith(blob);
    expect(cliqueLink).toHaveBeenCalledTimes(1);
    expect(revogarUrl).toHaveBeenCalledWith("blob:url-de-teste");

    cliqueLink.mockRestore();
  });

  it("gera e baixa o PDF ao clicar em Gerar relatório", async () => {
    const blob = new Blob(["%PDF-1.4"], { type: "application/pdf" });
    vi.mocked(api.gerarRelatorioPdf).mockResolvedValue(blob);
    const criarUrl = vi.fn().mockReturnValue("blob:url-de-teste");
    const revogarUrl = vi.fn();
    URL.createObjectURL = criarUrl;
    URL.revokeObjectURL = revogarUrl;
    // jsdom tenta navegar de verdade ao clicar num <a href>, sem suporte a
    // blob: URLs -- só nos interessa que o clique aconteceu, não a
    // navegação em si (que só existe de fato no navegador).
    const cliqueLink = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});

    render(<RevisaoRespostas revisao={REVISAO} onAjustar={() => {}} onReiniciar={() => {}} processando={false} />);

    fireEvent.click(screen.getByRole("button", { name: "Gerar relatório (PDF)" }));

    await waitFor(() => expect(api.gerarRelatorioPdf).toHaveBeenCalledWith(REVISAO.thread_id));
    expect(criarUrl).toHaveBeenCalledWith(blob);
    expect(cliqueLink).toHaveBeenCalledTimes(1);
    expect(revogarUrl).toHaveBeenCalledWith("blob:url-de-teste");

    cliqueLink.mockRestore();
  });

  it("mostra uma mensagem de erro se a geração do PDF falhar", async () => {
    vi.mocked(api.gerarRelatorioPdf).mockRejectedValue(new Error("Erro 400 ao gerar o relatório em PDF"));

    render(<RevisaoRespostas revisao={REVISAO} onAjustar={() => {}} onReiniciar={() => {}} processando={false} />);

    fireEvent.click(screen.getByRole("button", { name: "Gerar relatório (PDF)" }));

    expect(await screen.findByText("Erro 400 ao gerar o relatório em PDF")).toBeInTheDocument();
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
      screen.getByText("Reabrindo um novo ciclo de investigação, isso pode levar alguns instantes."),
    ).toBeInTheDocument();
  });
});
