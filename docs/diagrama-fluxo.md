# Diagrama de fluxo — Root-Spector

Duas visões complementares do mesmo sistema: a topologia interna do grafo
LangGraph (`root_cause_agent/graph.py`) e a sequência de chamadas HTTP
entre operador, frontend e backend (`backend/main.py`). Ambas renderizam
nativamente no GitHub (Mermaid). Ver `docs/openapi.yaml` para o contrato
completo das rotas e `specs/design.md` para o detalhamento textual.

## 1. Grafo do agente (LangGraph)

Espelha exatamente os nós/arestas de `graph.py` — cores indicam o tipo de
cada nó (a mesma legenda usada em `docs/apresentacao.html`).

```mermaid
flowchart TD
    Inicio(["Operador escolhe o lote\n(interface web)"]) --> PC

    PC["preparar_contexto"] --> FPI

    subgraph Fase1["Fase 1 — Ishikawa (6 categorias, sempre nesta ordem)"]
        FPI["formular_pergunta_ishikawa"]
        PO["perguntar_operador"]
        AI["avaliar_informatividade"]
    end

    subgraph Fase2["Fase 2 — 5 Porquês (ancorado na categoria_principal)"]
        FP["formular_porque"]
    end

    UF["usar_ferramenta\n(consultar_leituras_biosensor)"]

    FPI -- "chamou a tool" --> UF
    FPI -- "pergunta pronta" --> PO
    FP -- "chamou a tool" --> UF
    FP -- "pergunta pronta" --> PO
    UF -- "fase Ishikawa" --> FPI
    UF -- "fase 5 Porquês" --> FP

    PO --> AI

    AI -- "resposta não informativa\n(1ª tentativa)" --> PO
    AI -- "categoria respondida,\nainda há próxima" --> FPI
    AI -- "6ª categoria respondida" --> OA
    AI -- "porquê respondido,\nnúmero <= 5" --> FP
    AI -- "5º porquê respondido" --> GCR

    OA["orquestrar_analise\n(identifica categoria_principal)"] --> FP

    GCR["gerar_causa_raiz"] --> Fim(["reports/{batch_id}_{ts}.json + .html"])

    classDef workflow fill:#cfe8ff,stroke:#2f6fb3,color:#1a1a1a
    classDef agentic fill:#e3d4fa,stroke:#7c4dbd,color:#1a1a1a
    classDef tool fill:#ffe8b3,stroke:#c98a1f,color:#1a1a1a
    classDef human fill:#d3f2d6,stroke:#3f9142,color:#1a1a1a

    class PC workflow
    class FPI,AI,OA,FP,GCR agentic
    class UF tool
    class PO human
```

**Legenda:** azul = determinístico/workflow · roxo = agêntico (chama o
LLM) · amarelo = ferramenta · verde = human-in-the-loop (`interrupt()`).
`usar_ferramenta` é compartilhado pelas duas fases — `rotear_apos_ferramenta`
decide para onde voltar (`categoria_principal is None` → ainda em
Ishikawa). `avaliar_informatividade` é quem decide se a cadeia avança: se a
resposta não for informativa e ainda for a 1ª tentativa, volta para
`perguntar_operador` (2ª e última chance); caso contrário, registra a
resposta final e o roteamento (`rotear_apos_avaliar`) segue para a próxima
categoria, para `orquestrar_analise` (Ishikawa completo), para o próximo
porquê, ou para `gerar_causa_raiz` (5º porquê concluído).

## 2. Sequência operador ↔ frontend ↔ backend ↔ agente

```mermaid
sequenceDiagram
    actor Operador
    participant FE as Frontend (React)
    participant API as backend/main.py
    participant G as Grafo (checkpointer SqliteSaver)

    Operador->>FE: escolhe um lote elegível (WARNING/CRITICAL)
    FE->>API: POST /api/investigacoes/{batch_id}/iniciar
    API->>G: invoke({batch_id}, thread_id=batch_id)
    G-->>API: interrupt() — 1ª pergunta (Ishikawa, categoria 1/6)
    API-->>FE: {thread_id, fase, categoria, pergunta, nc}
    FE-->>Operador: pergunta + histórico de parâmetros do lote

    loop até 11 perguntas (6 Ishikawa + 5 Porquês)
        Operador->>FE: responde
        FE->>API: POST /api/investigacoes/{thread_id}/responder
        API->>G: invoke(Command(resume=resposta))
        alt resposta vazia ou evasiva (Camada 1)
            G-->>API: interrupt() de novo, mesma pergunta
            API-->>FE: {..., erro: "Este tipo de resposta não é aceito."}
        else próxima pergunta
            G-->>API: interrupt() — próxima pergunta
            API-->>FE: {thread_id, fase, pergunta, ...}
        else 5º porquê concluído
            G-->>API: diagnóstico pronto
            API->>API: salvar_relatorio() → reports/*.json + *.html
            API-->>FE: {status: "pronto_para_revisao"}
        end
    end

    FE->>API: GET /api/investigacoes/{thread_id}/revisao
    API-->>FE: cadeia completa + categoria_principal + causa_raiz + links
    FE-->>Operador: tela de revisão com o relatório já disponível

    opt operador pede ajuste
        Operador->>FE: "pedir ajuste"
        FE->>API: POST /api/investigacoes/{thread_id}/ajustar
        API->>API: arquiva o diagnóstico em ciclos_anteriores
        API->>G: reinicia o grafo (mesmo batch_id)
        G-->>API: interrupt() — 1ª pergunta do novo ciclo
        API-->>FE: {thread_id, fase: "ishikawa", ...}
    end
```

**Nota — falha de LLM:** se todos os provedores configurados (Gemini →
Groq → Anthropic → OpenAI) falharem, `iniciar`/`responder`/`ajustar`
capturam `FalhaLLMError` e devolvem `HTTP 503` com "Serviço de IA
indisponível, recarregue a página." — o checkpoint do `thread_id`
permanece pausado no último ponto bem-sucedido (nenhum progresso é
perdido; ver `specs/design.md` § Tratamento de falha na chamada ao LLM).
