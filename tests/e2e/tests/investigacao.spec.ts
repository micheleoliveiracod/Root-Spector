// Cenário principal: lista de lotes -> escolher um elegível -> responder as
// 11 perguntas (6 Ishikawa + 5 porquês) -> revisão, já com o link do
// relatório gerado automaticamente ao concluir o ciclo.
//
// Cenário de ajuste: revisão -> "pedir ajuste" -> novo ciclo completo (11
// perguntas de novo) -> conferir que o relatório do 2º ciclo lista o ciclo
// anterior em ciclos_anteriores.
//
// Roda contra backend/frontend subidos automaticamente pelo webServer do
// playwright.config.ts, sempre contra tests/fixtures/biotecpredict_teste.db
// e LLM_PROVIDER=fake -- nunca contra data/biotecpredict.db nem um
// provedor real.

import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";

async function escolherLote(page: Page, batchId: number) {
  // cada teste usa um lote diferente (thread_id = batch_id) -- evita que um
  // teste reutilize o thread já concluído pelo outro
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Lotes" })).toBeVisible();
  const linha = page.locator("tr", { hasText: String(batchId) });
  await linha.getByRole("button", { name: "Investigar" }).click();
}

async function responderPerguntas(page: Page, quantidade: number, prefixo = "resposta") {
  for (let i = 0; i < quantidade; i++) {
    await expect(page.getByLabel("Resposta")).toBeVisible();
    await page.getByLabel("Resposta").fill(`${prefixo} ${i}`);
    // espera a resposta de /responder chegar antes de preencher a próxima
    // pergunta -- sem isso, o preenchimento seguinte pode correr contra o
    // mesmo textarea antes do React re-renderizar com a nova pergunta
    await Promise.all([
      page.waitForResponse((resp) => resp.url().includes("/responder") && resp.status() === 200),
      page.getByRole("button", { name: "Responder" }).click(),
    ]);
  }
}

test("investigação completa: escolher lote, responder e revisar com relatório já gerado", async ({
  page,
}) => {
  await escolherLote(page, 511);

  await expect(page.getByRole("heading", { name: "Mapeamento Ishikawa" })).toBeVisible();
  await responderPerguntas(page, 11);

  await expect(page.getByRole("heading", { name: "Revisão da investigação" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Ishikawa" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "5 Porquês" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Ver relatório (HTML)" })).toHaveAttribute(
    "href",
    /http:\/\/localhost:8000\/reports\/.*\.html/,
  );
});

test("pedir ajuste reabre um novo ciclo e preserva o anterior no relatório final", async ({
  page,
}) => {
  await escolherLote(page, 512);

  await responderPerguntas(page, 11);
  await expect(page.getByRole("heading", { name: "Revisão da investigação" })).toBeVisible();

  await page.getByRole("button", { name: "Pedir ajuste" }).click();

  await expect(page.getByRole("heading", { name: "Mapeamento Ishikawa" })).toBeVisible();
  await responderPerguntas(page, 11, "resposta ciclo2");

  await expect(page.getByRole("heading", { name: "Revisão da investigação" })).toBeVisible();
  const href = await page.getByRole("link", { name: "Ver relatório (HTML)" }).getAttribute("href");
  expect(href).toBeTruthy();

  const resposta = await page.request.get(href!);
  const corpo = await resposta.text();
  expect(corpo).toContain("Ciclos anteriores");
});
