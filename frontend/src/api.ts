// VITE_API_URL/VITE_API_KEY (build-time, ver docs/deploy-producao.md):
// sem elas, cai no backend local de desenvolvimento e em nenhuma chave.
// Em produção, apontam para o domínio do Render e para o mesmo valor de
// INTERNAL_API_KEY configurado lá.
export const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const API_KEY = import.meta.env.VITE_API_KEY ?? "";

export interface Lote {
  batch_id: number;
  upload_date: string;
  compliance_score: number;
  risk_prediction: string;
  classification: string;
  elegivel: boolean;
  parametros_fora_da_faixa: string[];
}

export interface MetricaSensor {
  parametro: string;
  media: number;
  minimo: number;
  maximo: number;
  unidade: string;
  dentro_da_faixa: boolean;
}

export interface NaoConformidade {
  batch_id: number;
  upload_date: string;
  compliance_score: number;
  classification: string;
  risk_prediction: string;
  sensor_metrics: Record<string, MetricaSensor>;
  parametros_fora_da_faixa: string[];
}

export interface Pergunta {
  thread_id: string;
  pergunta: string;
  nc: NaoConformidade;
  fase: string;
  indice: number;
  total: number;
  categoria?: string;
  erro?: string;
}

export interface StatusRevisao {
  thread_id: string;
  status: "pronto_para_revisao";
}

export interface RespostaIshikawa {
  categoria: string;
  pergunta: string;
  resposta: string;
}

export interface PorQue {
  numero: number;
  pergunta: string;
  resposta: string;
}

export interface CategoriaAnalise {
  categoria: string;
  justificativa: string;
}

export interface CategoriaDescartada {
  categoria: string;
  motivo: string;
}

export interface RelatorioLinks {
  json: string;
}

export interface Revisao {
  thread_id: string;
  respostas_ishikawa: RespostaIshikawa[];
  categoria_principal: CategoriaAnalise;
  categorias_descartadas: CategoriaDescartada[];
  cadeia_de_porques: PorQue[];
  causa_raiz: string;
  narrativa: string;
  relatorio: RelatorioLinks;
}

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const headers = {
    ...(options?.headers ?? {}),
    ...(API_KEY ? { "X-API-Key": API_KEY } : {}),
  };
  const resposta = await fetch(`${BASE_URL}${url}`, { ...options, headers });
  if (!resposta.ok) {
    let mensagem = `Erro ${resposta.status}`;
    try {
      const corpo = await resposta.json();
      mensagem = corpo.detail ?? mensagem;
    } catch {
      // corpo não era JSON -- mantém a mensagem genérica
    }
    throw new Error(mensagem);
  }
  return resposta.json() as Promise<T>;
}

export function listarLotes(): Promise<Lote[]> {
  return fetchJson("/api/lotes");
}

export function iniciarInvestigacao(batchId: number): Promise<Pergunta> {
  return fetchJson(`/api/investigacoes/${batchId}/iniciar`, { method: "POST" });
}

export function responder(threadId: string, resposta: string): Promise<Pergunta | StatusRevisao> {
  return fetchJson(`/api/investigacoes/${threadId}/responder`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ resposta }),
  });
}

export function buscarRevisao(threadId: string): Promise<Revisao> {
  return fetchJson(`/api/investigacoes/${threadId}/revisao`);
}

export function ajustar(threadId: string): Promise<Pergunta> {
  return fetchJson(`/api/investigacoes/${threadId}/ajustar`, { method: "POST" });
}

/** Gera o PDF do relatório sob demanda (nunca salvo em disco, ver
 * root_cause_agent/reports.py::gerar_pdf) e devolve os bytes como Blob,
 * pronto para virar um link de download temporário no componente. Sem
 * cabeçalho X-API-Key, essa rota fica de fora de exigir_api_key (o link
 * do e-mail do n8n precisa continuar clicável sem cabeçalho customizado). */
export async function gerarRelatorioPdf(threadId: string): Promise<Blob> {
  const resposta = await fetch(`${BASE_URL}/api/investigacoes/${threadId}/relatorio.pdf`);
  if (!resposta.ok) {
    throw new Error(`Erro ${resposta.status} ao gerar o relatório em PDF`);
  }
  return resposta.blob();
}

/** Baixa o relatório em JSON gravado no banco (`relatorio.json` da
 * revisão), como Blob -- diferente do PDF, essa rota exige X-API-Key
 * quando configurada, por isso usa fetch com cabeçalho em vez de um link
 * `<a href>` direto. */
export async function baixarRelatorioJson(relatorioLink: string): Promise<Blob> {
  const headers: HeadersInit = API_KEY ? { "X-API-Key": API_KEY } : {};
  const resposta = await fetch(`${BASE_URL}${relatorioLink}`, { headers });
  if (!resposta.ok) {
    throw new Error(`Erro ${resposta.status} ao baixar o relatório em JSON`);
  }
  return resposta.blob();
}
