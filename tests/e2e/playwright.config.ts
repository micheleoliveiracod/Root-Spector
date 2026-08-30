import { defineConfig } from '@playwright/test';

// Sobe backend (uvicorn) + frontend (vite) automaticamente antes da suíte,
// sempre contra tests/fixtures/biotecpredict_teste.db e um LLM fake --
// nunca contra data/biotecpredict.db nem um provedor real (ver
// specs/ci-cd.md e .github/workflows/ci.yml, job `e2e`).
export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  retries: process.env.CI ? 1 : 0,
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },
  webServer: [
    {
      command: 'uvicorn backend.main:app --port 8000',
      // Relativo à pasta deste arquivo (tests/e2e/) -- precisa subir 2
      // níveis pra chegar na raiz do repo, não 1. "cwd: '..'" resolvia
      // pra tests/ (existe, mas é o diretório errado: os caminhos
      // relativos de BIOTECPREDICT_DB_PATH/CHECKPOINT_DB_PATH abaixo
      // ficavam quebrados) -- e o mesmo erro no webServer seguinte
      // (frontend) apontava pra um diretório que nem existe
      // (tests/frontend/), o que faz o Node falhar com a mensagem
      // enganosa "spawn /bin/sh ENOENT" em vez de um erro claro de
      // "diretório não encontrado".
      cwd: '../..',
      port: 8000,
      reuseExistingServer: !process.env.CI,
      env: {
        // Espalha process.env primeiro (boa prática documentada do
        // Playwright pra webServer em array, ver playwright.dev/docs/test-webserver) --
        // preserva PATH e outras variáveis herdadas do processo pai.
        ...process.env,
        LLM_PROVIDER: 'fake',
        BIOTECPREDICT_DB_PATH: 'tests/fixtures/biotecpredict_teste.db',
        CHECKPOINT_DB_PATH: 'data/checkpoints_e2e.db',
      },
    },
    {
      command: 'npm run dev -- --port 5173',
      cwd: '../../frontend',
      port: 5173,
      reuseExistingServer: !process.env.CI,
      env: { ...process.env },
    },
  ],
});
