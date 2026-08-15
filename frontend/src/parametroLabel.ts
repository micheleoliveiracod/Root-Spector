const NOMES: Record<string, string> = {
  temperature: "Temperatura",
  ph: "pH",
  dissolved_oxygen: "Oxigênio dissolvido",
  pressure: "Pressão",
  agitator_speed: "Velocidade do agitador",
};

export function nomeParametro(chave: string): string {
  return NOMES[chave] ?? chave;
}
