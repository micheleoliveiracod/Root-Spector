# Observabilidade

Este documento descreve os dois sinais de observabilidade correlacionados
exigidos pelo PDF (§4.6) e o reforço de resiliência que acompanha o mesmo
requisito. O código correspondente está em `root_cause_agent/config.py`
(sinal 1, configuração de logging e o callback de chamadas de LLM),
`root_cause_agent/graph.py` (onde cada nó do grafo é instrumentado) e
`root_cause_agent/tools.py` (timeout/retry); a análise original está em
`specs/fase02/design.md` (seção Observabilidade); a prova automatizada
está em `tests/test_observabilidade.py`, `tests/test_checkpointer.py` e
`tests/test_tools.py`.

## Sinal 1: logging estruturado (JSON)

`config.py:configurar_logging()` configura o logger `root_cause_agent`
para emitir 1 linha de JSON por registro em dois lugares: stdout (leitura
humana em runtime, sem dependência nova, só a `logging` da biblioteca
padrão) e a tabela `eventos_log`, gravada por
`config.py:_HandlerBancoDeDados`. Essa tabela vive em SQLite local
(`data/observabilidade.db`) por padrão, ou na mesma instância de Postgres
do checkpointer do grafo quando `DATABASE_URL` estiver definida (deploy,
ver `specs/deploy-producao/plano.md`). É essa cópia em banco, não o
stdout, que o resumo diário (`root_cause_agent/resumo_diario.py`) relê
depois, e que permite conectar uma ferramenta de BI direto no banco para
análise estatística.

`graph.py:_com_log_estruturado` envolve todo nó do grafo (incluindo
`usar_ferramenta`, o `ToolNode`) e emite, ao final de cada execução, um
registro com:

| Campo | Origem | Exemplo |
|---|---|---|
| `timestamp` | Horário da emissão do log | `2026-08-26T14:32:01.123456+00:00` |
| `nivel` | Nível do log | `INFO` |
| `mensagem` | Descrição fixa do evento | `no_executado` |
| `no` | Nome do nó no `StateGraph` | `formular_porque` |
| `thread_id` | `RunnableConfig["configurable"]["thread_id"]`, injetado pelo LangGraph | `"511"` |
| `batch_id` | `AgentState["batch_id"]` | `511` |
| `duracao_s` | Tempo de execução do nó, em segundos | `1.842` |

Um exemplo real de linha emitida:

```json
{"timestamp": "2026-08-26T14:32:01.123456+00:00", "nivel": "INFO", "mensagem": "no_executado", "thread_id": "511", "batch_id": 511, "no": "gerar_causa_raiz", "duracao_s": 2.157}
```

`perguntar_operador` chama `interrupt()` para pausar o grafo esperando o
operador -- o LangGraph reexecuta esse nó do zero ao retomar de um
checkpoint, então ele aparece 2x por pergunta no log: 1x quando levanta a
pausa, 1x quando o `resume` de fato o atravessa. Isso é esperado, não uma
duplicação indevida (ver comentário em `graph.py:_com_log_estruturado` e
`tests/test_observabilidade.py`).

### Desempenho por provedor de LLM na cadeia de fallback

`config.py:_CallbackObservabilidadeLLM` é um callback do LangChain
anexado à cadeia de fallback inteira (`get_llm()`), não só ao provedor
principal. Callbacks do LangChain disparam para cada tentativa dentro de
`with_fallbacks()`, inclusive as que falham antes do próximo provedor
assumir, então esse callback captura o fallback de verdade acontecendo,
não só o resultado final. Cada tentativa gera um registro na mesma tabela
`eventos_log`, com `mensagem: "chamada_llm"`:

```json
{"timestamp": "2026-08-26T14:32:01.123456+00:00", "nivel": "INFO", "mensagem": "chamada_llm", "provedor": "ChatGoogleGenerativeAI", "modelo": "gemini-2.5-flash", "duracao_s": 8.021, "sucesso": false, "erro": "rate limit"}
```

Isso permite comparar desempenho e confiabilidade entre provedores (por
exemplo, quantas vezes o Gemini falhou por limite de taxa antes do Groq
assumir, e qual dos dois respondeu mais rápido), não só contar quantas
vezes o fallback foi acionado no total.

## Sinal 2: trace do LangSmith

Ativado via a variável de ambiente opcional `LANGSMITH_TRACING` (junto de
`LANGSMITH_API_KEY` e `LANGSMITH_PROJECT`, ver `.env.example`). Nenhum
código próprio: o `langsmith`/`langchain-core` já lê essas variáveis do
ambiente diretamente (carregadas pelo `load_dotenv()` de `config.py`) e
instrumenta automaticamente toda chamada de LLM feita através do
LangChain, sem precisar tocar em `nodes.py`/`graph.py`.

Ativar essa variável é uma decisão consciente, não um default silencioso:
com ela ligada, a conversa completa de cada investigação (prompts,
respostas do LLM, chamadas de tool) passa a ser enviada para o LangSmith.
Por isso o padrão em `.env.example` é `LANGSMITH_TRACING=false`.

## Correlação dos 2 sinais

Rodando 1 investigação real com os 2 sinais ativos, cada linha do log
estruturado (sinal 1) e o trace correspondente no LangSmith (sinal 2)
descrevem a mesma execução de nó a partir de ângulos diferentes: o log diz
quanto tempo o nó levou e com qual `thread_id`/`batch_id`, o trace mostra o
prompt exato enviado ao LLM e a resposta recebida. Cruzar os dois permite
investigar uma execução real de ponta a ponta -- por exemplo, um
`duracao_s` alto em `gerar_causa_raiz` no log aponta para qual trace do
LangSmith abrir pra ver se o tempo foi gasto esperando o provedor de LLM
responder ou processando um prompt anormalmente longo.

> **Pendente**: este documento ainda não contém um exemplo real
> correlacionado (log JSON + link do trace do LangSmith lado a lado), por
> exigir uma chave de API do LangSmith e uma execução com um provedor de
> LLM de verdade (não `LLM_PROVIDER=fake`), que só quem tem acesso às
> credenciais consegue gerar. Para completar: definir `LANGSMITH_TRACING=true`,
> `LANGSMITH_API_KEY` e `LANGSMITH_PROJECT` no `.env`, rodar 1 investigação
> completa pela interface, copiar aqui 1 linha do log JSON emitido no
> terminal do backend e o link do trace correspondente em
> https://smith.langchain.com.

## Timeout e retry na tool de biosensor

**Problema.** `consultar_leituras_biosensor` (`tools.py`) abria a conexão
SQLite sem timeout explícito e sem nenhuma tentativa de recuperação --
um banco travado por outro processo, ou um arquivo corrompido, bloquearia
a chamada indefinidamente ou propagaria uma exceção crua para o nó
agêntico que chamou a tool.

**Guardrail.** `tools.py:TIMEOUT_CONSULTA_SQL` (5 segundos) é passado
explicitamente a `sqlite3.connect()`, o tempo que o SQLite espera por um
lock antes de desistir. `tools.py:MAX_TENTATIVAS_CONSULTA_SQL` (2) tenta a
conexão mais de uma vez antes de desistir, com um intervalo de
`INTERVALO_ENTRE_TENTATIVAS` (0,5s) entre tentativas -- cobre uma falha
transitória (ex. outro processo segurando o arquivo por um instante) sem
tentar indefinidamente. Se todas as tentativas falharem com
`sqlite3.OperationalError`, a tool retorna uma mensagem de erro tratável
pro LLM (nunca lança a exceção pra cima), no mesmo espírito de
`FalhaLLMError` em `nodes.py`: o agente sabe que a consulta falhou e pode
seguir a investigação sem esse dado, em vez de travar.
