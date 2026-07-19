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
      cwd: '..',
      port: 8000,
      reuseExistingServer: !process.env.CI,
      env: {
        LLM_PROVIDER: 'fake',
        BIOTECPREDICT_DB_PATH: 'tests/fixtures/biotecpredict_teste.db',
        CHECKPOINT_DB_PATH: 'data/checkpoints_e2e.db',
      },
    },
    {
      command: 'npm run dev -- --port 5173',
      cwd: '../frontend',
      port: 5173,
      reuseExistingServer: !process.env.CI,
    },
  ],
});
