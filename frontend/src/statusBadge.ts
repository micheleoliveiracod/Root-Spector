// Mapeia classification/risk_prediction pro tom "semáforo" certo (sempre
// pastel, ver src/styles/tokens.css) -- um único lugar pra essa regra, os
// componentes só chamam badgeClass().
const MAPA: Record<string, string> = {
  ACCEPTABLE: "badge--ok",
  LOW_RISK: "badge--ok",
  WARNING: "badge--warn",
  MEDIUM_RISK: "badge--warn",
  CRITICAL: "badge--critical",
  HIGH_RISK: "badge--critical",
};

export function badgeClass(valor: string): string {
  return MAPA[valor] ?? "badge--neutral";
}
