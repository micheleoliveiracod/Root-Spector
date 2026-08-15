import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { Lote } from "../api";
import * as api from "../api";
import { ListaLotes } from "./ListaLotes";

vi.mock("../api");

const LOTES: Lote[] = [
  {
    batch_id: 501,
    upload_date: "2026-07-10T08:00:00+00:00",
    compliance_score: 92,
    risk_prediction: "LOW_RISK",
    classification: "ACCEPTABLE",
    elegivel: false,
    parametros_fora_da_faixa: [],
  },
  {
    batch_id: 511,
    upload_date: "2026-07-10T08:00:00+00:00",
    compliance_score: 38,
    risk_prediction: "HIGH_RISK",
    classification: "CRITICAL",
    elegivel: true,
    parametros_fora_da_faixa: ["agitator_speed"],
  },
];

describe("ListaLotes", () => {
  it("renderiza os lotes e destaca os elegíveis", async () => {
    vi.mocked(api.listarLotes).mockResolvedValue(LOTES);
    render(<ListaLotes onEscolher={() => {}} processando={false} />);

    await waitFor(() => expect(screen.getByText("511")).toBeInTheDocument());
    expect(screen.getByText("não elegível")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Investigar" })).toBeInTheDocument();
    expect(screen.getByText("Velocidade do agitador")).toBeInTheDocument();
  });

  it("chama onEscolher com o lote certo ao clicar em Investigar", async () => {
    vi.mocked(api.listarLotes).mockResolvedValue(LOTES);
    const onEscolher = vi.fn();
    render(<ListaLotes onEscolher={onEscolher} processando={false} />);

    await waitFor(() => screen.getByRole("button", { name: "Investigar" }));
    fireEvent.click(screen.getByRole("button", { name: "Investigar" }));

    expect(onEscolher).toHaveBeenCalledWith(LOTES[1]);
  });

  it("mostra indicador de carregamento e desabilita Investigar enquanto processa", async () => {
    vi.mocked(api.listarLotes).mockResolvedValue(LOTES);
    render(<ListaLotes onEscolher={() => {}} processando={true} />);

    await waitFor(() => screen.getByRole("button", { name: "Investigar" }));

    expect(screen.getByRole("button", { name: "Investigar" })).toBeDisabled();
    expect(
      screen.getByText("Iniciando a investigação com o agente — isso pode levar alguns instantes."),
    ).toBeInTheDocument();
  });
});
