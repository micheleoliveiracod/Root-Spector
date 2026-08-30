// Mapeia classification/risk_prediction pro tom "semáforo" certo (sempre
// pastel, ver src/styles/tokens.css) -- um único lugar pra essa regra, os
// componentes só chamam badgeClass() ou estadoLote().
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

export interface EstadoLote {
  /** classe do .estado, ex. "estado--critical" */
  classe: string;
  /** a palavra do estado, em português, para quem não conhece o código técnico */
  rotulo: string;
  /** o que o operador deve fazer diante desse estado */
  acao: string;
}

const MAPA_ESTADO: Record<string, EstadoLote> = {
  CRITICAL: { classe: "estado--critical", rotulo: "Crítico", acao: "Investigar agora" },
  HIGH_RISK: { classe: "estado--critical", rotulo: "Crítico", acao: "Investigar agora" },
  WARNING: { classe: "estado--warn", rotulo: "Atenção", acao: "Avaliar antes de liberar" },
  MEDIUM_RISK: { classe: "estado--warn", rotulo: "Atenção", acao: "Avaliar antes de liberar" },
  ACCEPTABLE: { classe: "estado--ok", rotulo: "Aceitável", acao: "Seguir o processo" },
  LOW_RISK: { classe: "estado--ok", rotulo: "Aceitável", acao: "Seguir o processo" },
};

/** Traduz um código técnico (classification ou risk_prediction) para o
 * estado que o operador vê: palavra, ação e classe visual. Valor não
 * mapeado cai em "Sem classificação", à espera do sistema. */
export function estadoLote(valor: string): EstadoLote {
  return (
    MAPA_ESTADO[valor] ?? {
      classe: "estado--neutral",
      rotulo: "Sem classificação",
      acao: "Aguardar o sistema",
    }
  );
}
