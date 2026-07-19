# Root-Spector — Agente de Investigação de Causa Raiz de NC

**Desenvolvido por:** [Michele Oliveira](https://github.com/micheleoliveiracod)

**Organização:** Programa SCTEC e SENAI (https://github.com/IA-para-DEVs-SCTEC-T2)

**Curso:** IA para DEVs

**Objetivo:** Desenvolvimento de um mini projeto E2E com IA em todas as etapas, como entrega parcial do módulo 2.

> **Status:** agente, backend, frontend e testes (pytest + Vitest + Playwright)
> implementados e verificados localmente, inclusive via `deploy/` (Docker).
> M2 a M5 já commitados e mergeados em `develop` via PR; `release/v1.0-entrega`
> em andamento — ver `docs/gitflow.md`. Detalhamento técnico em
> `specs/requirements.md` e `specs/design.md`.

## Descrição do problema

Quando um processo produtivo gera uma Não-Conformidade (NC) — um lote fora
da especificação — o passo mais custoso do tratamento costuma ser descobrir
**por que** aconteceu, não só constatar que aconteceu. Essa investigação
normalmente depende de um especialista cruzando manualmente o evento de NC
com dados históricos de processo, e é conduzida por um colaborador da
qualidade investigando um processo operacional realizado por outro
colaborador — o que carrega um viés interpessoal difícil de eliminar. Um
agente de IA traz imparcialidade e impessoalidade a essa investigação, por
não ser parte da equipe operacional, e agilidade no processo de
investigação e tratamento da causa, evitando que o lote se transforme em
um produto e avance no processo produtivo, causando mais desperdícios e a reincidencia do problema.

## Objetivo do agente

Este agente é o **complemento de causa raiz** do
[BiotecPredict](https://github.com/micheleoliveiracod/Projeto-avaliativo-M1-2-BiotecPredict)
(projeto da mesma autora), uma plataforma que avalia lotes de bioprocesso a
partir de dados de biosensores por dois sinais independentes — um
`compliance_score` (0–100, classificável em ACCEPTABLE/WARNING/CRITICAL) e
um `risk_prediction` de ML (LOW_RISK/MEDIUM_RISK/HIGH_RISK) — e persiste o
resultado num **banco SQLite** (`batches` + `sensor_readings`, schema
verificado diretamente no código-fonte do BiotecPredict).

Ao abrir a aplicação, o operador vê a lista de lotes já classificada por
risco e escolhe um lote elegível (risco médio ou alto) para investigar.
O agente identifica deterministicamente qual(is) parâmetro(s) de biosensor
está(ão) fora da faixa (comparando a média das leituras do lote contra
`config/regras_bioprocesso.yaml`) e então **facilita duas ferramentas de
qualidade em sequência com o operador**: primeiro um **diagrama de
Ishikawa** (6 perguntas de contexto — Método, Máquina, Material, Mão de
obra, Meio ambiente, Medição — não perguntas diretas sobre o parâmetro fora
da faixa), identifica a categoria mais provável, e só então aprofunda com o
**método dos 5 Porquês** ancorado nessa categoria — sempre 6 + 5 rodadas —
até sintetizar uma causa raiz sistêmica, gerando o relatório. Ao final, o
operador revisa a cadeia completa e pode **pedir ajuste** (reabre um novo
ciclo, preservando o anterior). Não é um agente que investiga
sozinho; é um agente que conduz a investigação em conjunto com quem opera o
processo.

**Case de referência:** biotecnologia — produção de bioinsumos/bioprocessos.
A solução é desenhada para ser adaptável a outros setores produtivos
trocando apenas os arquivos de configuração/dados — ver "Adaptação a outro
setor" em `specs/design.md`. Este projeto começou desenhado para
agronegócio/grãos e foi re-configurado para bioprocessos trocando só esses
arquivos, na prática validando esse requisito.

## Arquitetura

- **Backend:** Python, LangGraph (motor do agente) + FastAPI (API).
- **Frontend:** React + TypeScript (Vite), uma única tela.
- **Dados de entrada:** `data/biotecpredict.db` — um arquivo SQLite (não
  versionado, ver "Como executar").

## Fluxo com LangGraph

```
Lote escolhido pelo operador na lista da interface web
   ↓
preparar_contexto        [determinístico: consulta batches (COMPLETED, com score), calcula sensor_metrics,
                           identifica parametros_fora_da_faixa, monta a NC]
   ↓
┌── FASE 1: ISHIKAWA (6 categorias, sempre nesta ordem) ───────────────┐
│ formular_pergunta_ishikawa ⇄ usar_ferramenta                         │
│    ↓                                                                  │
│ perguntar_operador  ← PONTO HUMAN-IN-THE-LOOP (via interface web)     │
│    ↓ (repete até as 6 categorias serem respondidas)                   │
└────────────────────────────────────────────────────────────────────┘
   ↓
orquestrar_analise   [nó LLM: identifica categoria_principal + categorias_descartadas]
   ↓
┌── FASE 2: 5 PORQUÊS (ancorado na categoria_principal) ───────────────┐
│ formular_porque ⇄ usar_ferramenta                                    │
│    ↓                                                                  │
│ perguntar_operador  ← PONTO HUMAN-IN-THE-LOOP                        │
│    ↓ (repete 5x)                                                       │
└────────────────────────────────────────────────────────────────────┘
   ↓
gerar_causa_raiz   [Diagnostico: Ishikawa + cadeia de 5 porquês + causa raiz]
   ↓
reports.py          [gera relatório JSON+HTML]
   ↓
Revisão pelo operador → link do relatório já disponível | pedir ajuste (reabre ciclo)
```

Detalhamento completo (estado, mecanismo de interrupção/retomada do
LangGraph, por que é um agente e não só um workflow, estratégia de dados)
em `specs/design.md`.

## Ferramenta utilizada pelo agente

`consultar_leituras_biosensor(batch_id, data_inicio, data_fim)` — `SELECT`
somente leitura na tabela `sensor_readings` de `data/biotecpredict.db`,
restrita a um `batch_id` e a uma janela de datas. Disponível tanto em
`formular_pergunta_ishikawa` quanto em `formular_porque` (no máximo 1x por
pergunta), tipicamente mais usada nas perguntas técnicas (Máquina/Medição,
5 Porquês) do que nas de processo/pessoas (Método/Mão de obra).

## Como executar

```bash
# 1. Backend
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -e ".[dev]"
cp .env.example .env         # preencher a chave de API do provedor de LLM escolhido

# 2. Dados: colocar um arquivo biotecpredict.db (exportado do BiotecPredict,
#    schema em specs/design.md) em data/biotecpredict.db.
#    Os testes automatizados usam tests/fixtures/biotecpredict_teste.db
#    (fixture estática já incluída no repositório) — nunca este arquivo real.

# 3. Subir a API
uvicorn backend.main:app --reload

# 4. Frontend (em outro terminal)
cd frontend
npm install
npm run dev
```

Abrir a URL indicada pelo Vite (padrão `http://localhost:5173`) — a tela
inicial já lista os lotes de `data/biotecpredict.db` com sua classificação.

## Exemplo de entrada (formato)

Linha da tabela `batches` que dispara a investigação (schema real do
BiotecPredict; lote 11 do dataset de demonstração atual — ver "Estratégia
de dados" em `specs/design.md`):

```json
{
  "id": 11,
  "upload_date": "2026-07-05T08:00:00",
  "status": "COMPLETED",
  "compliance_score": 71.32,
  "risk_prediction": "MEDIUM_RISK"
}
```

`compliance_score=71.32` é classificado `WARNING` (entre 45 e 80, regra
real do BiotecPredict replicada em `config/regras_bioprocesso.yaml`) —
`classification` não é uma coluna do banco, o agente calcula na hora. O
`risk_prediction` do modelo de ML concorda (`MEDIUM_RISK`).
`preparar_contexto` calcula `sensor_metrics` a partir de `sensor_readings`
e identifica `parametros_fora_da_faixa: ["dissolved_oxygen",
"agitator_speed"]` (par correlacionado — menos agitação, menos
transferência de oxigênio) — isso já vem pronto quando o agente entra em
ação; ele não descobre qual parâmetro é, ele investiga *por que* esses
parâmetros ficaram fora da faixa — primeiro mapeando o contexto
(Ishikawa), depois aprofundando (5 Porquês).

## Exemplo de interação (Ishikawa + 5 Porquês)

```
[Agente] (Máquina) O agitador deste lote operou dentro da velocidade
         (RPM) padrão do processo?
[Operador] Não — o setpoint do inversor de frequência estava abaixo do
           valor padrão.
[Agente] (Método) Houve alguma mudança de procedimento neste lote?
[Operador] Não, seguimos o procedimento padrão.
... (Material, Mão de obra, Meio ambiente, Medição)
```
(6 perguntas de contexto, depois a orquestração identifica `categoria_principal: "Máquina"`)

```
[Agente] Por que o agitador operou com velocidade abaixo do padrão?
[Operador] Porque o setpoint configurado no inversor de frequência estava
           abaixo do valor padrão do processo.
[Agente] Por que o setpoint estava abaixo do padrão?
[Operador] Porque foi alterado durante o ajuste do lote anterior e não foi
           restaurado.
[Agente] Por que não foi restaurado antes de iniciar este lote?
[Operador] ...
```
(continua até a 5ª pergunta, quando o relatório já é gerado; o operador
revisa e pode pedir ajuste — roteiro completo em
`docs/demo/gabarito-testes.md`)

## Exemplo de saída (formato)

Salvo em `reports/11_20260719T000000.json` e `.html`:

```json
{
  "batch_id": 11,
  "categoria_principal": {
    "categoria": "Máquina",
    "justificativa": "Setpoint do inversor de frequência do agitador abaixo do padrão, coincide com a queda de agitator_speed e dissolved_oxygen"
  },
  "categorias_descartadas": [
    {"categoria": "Método", "motivo": "operador confirma procedimento padrão seguido"}
  ],
  "cadeia_de_porques": [
    {
      "numero": 1,
      "pergunta": "Por que o agitador operou com velocidade abaixo do padrão?",
      "resposta": "Porque o setpoint configurado no inversor de frequência estava abaixo do valor padrão do processo.",
      "evidencia": "agitator_speed e dissolved_oxygen fora da faixa aceitável (par correlacionado)"
    },
    {
      "numero": 2,
      "pergunta": "Por que o setpoint estava abaixo do padrão?",
      "resposta": "Porque foi alterado durante o ajuste do lote anterior e não foi restaurado ao valor padrão.",
      "evidencia": null
    }
  ],
  "causa_raiz": "Ausência de atualização do checklist de início de lote após a instalação de um novo inversor de frequência no agitador, permitindo que um setpoint de velocidade incorreto não fosse detectado antes do início do processo.",
  "narrativa": "...",
  "ciclos_anteriores": [],
  "gerado_em": "2026-07-19T00:00:00"
}
```

O `.html` correspondente apresenta o mesmo conteúdo formatado para leitura.

## Principais decisões

- **LangGraph** com estado (`AgentState`), nós determinísticos + 4 nós
  agênticos (`formular_pergunta_ishikawa`, `orquestrar_analise`,
  `formular_porque`, `gerar_causa_raiz`), um `ToolNode`, e um ponto
  human-in-the-loop (`perguntar_operador`, reusado nas duas fases).
- **Interface web (FastAPI + React), não CLI** — o operador interage pelo
  navegador; o mecanismo de pausa/retomada usa `interrupt()` e um
  checkpointer do LangGraph, não `input()` bloqueante (que não funciona
  atrás de uma API) — ver `specs/design.md`.
- **Ishikawa (6 categorias) antes de 5 Porquês** — 5 Porquês sozinho não
  prioriza entre causas de categorias diferentes (método, máquina,
  material, mão de obra, meio ambiente, medição); mapear o contexto
  primeiro evita ancorar a investigação numa categoria errada. Decisão
  informada por literatura de qualidade (ASQ, KaiNexus) e por um artigo
  acadêmico sobre RCA multiagente — ver `specs/design.md`.
- **"Orquestrador" e "relatório" são nós do mesmo grafo, não agentes
  separados** — decisão deliberada de simplicidade; a literatura de
  referência usa arquitetura multiagente de verdade, mas replicar isso
  aqui adicionaria complexidade de coordenação sem necessidade.
- **Sempre exatamente 6 perguntas de Ishikawa + 5 Porquês, no máximo 1
  consulta à ferramenta por pergunta** — decisão deliberada por
  previsibilidade, mesmo sabendo que a prática real do método às vezes
  para antes (ver `specs/design.md`).
- **Relatório gerado ao final de cada ciclo, revisão sempre disponível** — o
  relatório já é salvo assim que a cadeia é concluída (5º porquê
  respondido) e seu link aparece na tela de revisão; o operador pode pedir
  ajuste a qualquer momento, o que preserva o ciclo anterior (já reportado)
  em `ciclos_anteriores` (auditoria) e reabre um novo ciclo.
- **Relatório em JSON e HTML** — JSON para consumo por outros sistemas,
  HTML para leitura humana.
- **LLM plugável**: provedor/modelo escolhidos via variável de ambiente
  (`LLM_PROVIDER`/`LLM_MODEL`) usando `init_chat_model` do LangChain —
  padrão Google Gemini (gratuito) nesta entrega.
- **Entrada via SQLite, schema real do BiotecPredict** — `data/biotecpredict.db`
  (nunca versionado) é montado a partir de um dataset curado de
  demonstração, versionado em `data/simulacao_causa_raiz/` (15 lotes: 5
  "ideais" + 10 com um desvio de causa física única cada). Os valores de
  sensor são desenhados propositalmente, mas `compliance_score`/
  `classification`/`risk_prediction` não são inventados: vêm de rodar o
  `ComplianceService`/`MLModel` reais e inalterados do BiotecPredict sobre
  esses dados — ver "Estratégia de dados" em `specs/design.md`. Os
  thresholds de classificação (`>=80` ACCEPTABLE, `>=45` WARNING, abaixo
  CRITICAL) foram conferidos linha a linha em
  `ComplianceService._classify_score()` do BiotecPredict, não apenas no
  README dele. Uma fixture sintética estática
  (`tests/fixtures/biotecpredict_teste.db`) existe só para os testes
  automatizados.

## Limitações

- A classificação/detecção da NC não é feita por este agente — ela vem do
  BiotecPredict. O agente lê um arquivo de banco local (exportado
  manualmente), não uma conexão ao vivo com uma instância em execução.
- Cobre um parâmetro fora da faixa por lote; múltiplos parâmetros fora da
  faixa simultaneamente exigiriam ciclos/NCs separadas.
- Os loops sempre completam todas as perguntas (6 Ishikawa + 5 Porquês),
  mesmo que a categoria/causa fique óbvia antes — não implementa parada
  antecipada.
- Lotes com `compliance_score` nulo (processados mas sem score atribuído)
  são excluídos da lista de elegíveis.

## Adaptação a outro setor produtivo

Ver seção correspondente em `specs/design.md`.

## Documentação relacionada

- `docs/PRD.md` — documento de requisitos de produto (problema, público, escopo, critérios de sucesso)
- `docs/cenarios-de-uso.md` — cenários de uso passo a passo (fluxo principal + validação/erro/ajuste)
- `docs/diagrama-fluxo.md` — diagramas Mermaid do grafo LangGraph e da sequência de chamadas HTTP
- `docs/openapi.yaml` — contrato completo da API (gerado a partir do schema real do FastAPI)
- `specs/requirements.md` — requisitos funcionais e não-funcionais
- `specs/design.md` — arquitetura, fluxo do grafo, estratégia de dados
- `docs/prompts.md` — prompts usados para planejar/implementar o agente
- `docs/gitflow.md` — modelo de branches, CI/CD, convenções de commit/PR
- `docs/apresentacao.md` — conteúdo da apresentação de 2 slides
- [BiotecPredict](https://github.com/micheleoliveiracod/Projeto-avaliativo-M1-2-BiotecPredict) — projeto complementar (classificação de risco do lote)

---

## ⭐ Agradecimentos

- **SCTEC e SENAI** - Programa de IA para DEVs
- **Comunidade Open Source** - Ferramentas e bibliotecas utilizadas

---

## 👨‍💻 Desenvolvedor

**Desenvolvido com 💜 por Michele Oliveira**
- GitHub: [@micheleoliveiracod](https://github.com/micheleoliveiracod)
- Email: [data.analystmlso@gmail.com](mailto:data.analystmlso@gmail.com)

**Última atualização:**  19 de Julho de 2026

---

## 🤝 Contribuindo

1. Crie uma branch para sua feature: `git checkout -b feature/sua-feature`
2. Commit suas mudanças: `git commit -m 'feat: descrição da feature'`
3. Push para a branch: `git push origin feature/sua-feature`
4. Abra um Pull Request

Consulte [GitFlow](specs/gitflow.md) para mais detalhes.

---

## 📄 Licença do Projeto

Este projeto está licenciado sob a **Apache License 2.0**.