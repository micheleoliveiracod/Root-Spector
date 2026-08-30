# Deploy em Produção, Plano

> **Status: nenhum deploy real executado ainda.** O checkpointer do
> LangGraph e a tabela `eventos_log` usam `SqliteSaver`/SQLite local sem
> `DATABASE_URL` definida, ou `PostgresSaver`/Postgres, na mesma
> instância, quando essa variável estiver definida. Issues 2, 3 e 4
> continuam só planejamento. Branch: `chore/deploy-producao-fase02`.

## Por que isso fica fora de `specs/fase02/`

O PDF da Fase 2 (`specs/fase02/requirements.md`) não exige deploy em
produção, nenhum dos critérios avaliados pede isso. A usuária optou por
fazer mesmo assim, como exercício de aprendizado sobre como se faz a
produção de agentes de inteligência artificial, depois que o agente
estiver cem por cento funcional localmente. Por isso este plano fica
numa pasta separada, `specs/deploy-producao/`, não conta nota, não deve
ser confundido com os critérios avaliados, e não compete em prioridade
com as issues de `specs/fase02/gitflow.md`.

## Stack escolhida, Render, Vercel e Azure

- **Render** (backend, FastAPI e LangGraph): serviço web gratuito, 750
  horas por mês, sem cartão de crédito. Limitação real: dorme depois de
  cerca de 15 minutos sem tráfego, com um tempo de inicialização de
  alguns segundos a cerca de um minuto no próximo pedido. Aceitável para
  um projeto de estudo, não para produção com acordo de nível de
  serviço. Vale documentar essa limitação explicitamente no README e no
  vídeo, sem escondê-la.
- **Vercel** (frontend, React e Vite estático): camada gratuita
  generosa, sem o problema de suspensão do Render, por ser uma rede de
  distribuição de conteúdo estática, não um processo de servidor.
- **Azure Database for PostgreSQL, Flexible Server**: resolve o mesmo
  problema de persistência, o disco local do Render não sobrevive ao
  ciclo de dormir e acordar do serviço gratuito, então tudo que hoje é
  gravado em arquivo local (checkpoints do LangGraph, `eventos_log`,
  relatório de cada investigação) passa a viver no banco. A conta
  gratuita da Azure inclui 12 meses de uma instância Burstable B1MS com
  32 gigabytes de armazenamento, sem custo; depois disso, o uso passa a
  ser cobrado normalmente. O relatório em PDF continua gerado sob
  demanda e nunca salvo, sem nenhum serviço de armazenamento de arquivo
  envolvido.

**Alternativas descartadas.** Railway deixou de ter camada gratuita
indefinida em 2023, hoje é só um crédito de teste que acaba, não serve
para o objetivo de aprendizado gratuito desta branch. Supabase foi a
escolha original deste plano, e continua sendo uma opção sólida, com uma
camada gratuita permanente e sem exigir cartão de crédito, mas a decisão
desta sessão foi migrar para a Azure, para o exercício de aprendizado
incluir também a experiência de configurar um serviço de nuvem
tradicional, não só um serviço especializado em backend como serviço.
Vale registrar a diferença honestamente: a Azure exige cadastro de
cartão de crédito mesmo para a camada gratuita, e essa camada dura 12
meses, não indefinidamente como a do Supabase. Não há alternativa
claramente melhor para o mesmo perfil de aplicação, um processo Python
de longa duração com FastAPI e LangGraph, com estado, mais um frontend
estático, que seja cem por cento gratuita sem cartão: Fly.io também
exige cartão cadastrado mesmo na camada gratuita, ainda que sem cobrança,
Cloudflare Workers não roda um processo ASGI padrão sem reescrever a
aplicação para o próprio ambiente de execução deles, e Hugging Face
Spaces é mais voltado a demonstrações do que a uma API com estado
persistente. Único serviço de nuvem gerenciado usado neste plano, sem
nenhum serviço de armazenamento de arquivo (Blob Storage ou
equivalente).

## O que muda no código, mínimo, o requisito de simplicidade continua valendo

| Peça | Hoje, local | Produção |
|---|---|---|
| `data/biotecpredict.db` | versionado no repositório, leitura só | sem mudança, embarca no deploy normalmente |
| Checkpointer LangGraph | `SqliteSaver`, `data/checkpoints.db` | `PostgresSaver`, Azure Database for PostgreSQL, quando `DATABASE_URL` estiver definida, com `sslmode=require` na string de conexão; `SqliteSaver` continua sendo o padrão sem essa variável de ambiente, o ambiente de desenvolvimento não ganha infraestrutura extra |
| Relatório (o PDF é gerado sob demanda e nunca salvo) | tabela `relatorios`, SQLite local | mesma tabela, Postgres, na mesma instância do checkpointer, quando `DATABASE_URL` estiver definida |
| CORS | `CORS_ALLOWED_ORIGINS`, variável de ambiente, padrão `localhost:5173` | já implementado, só falta apontar para o domínio real do Vercel |
| Limite de taxa | `limitar_taxa`, 20 requisições por minuto por IP, em memória | já implementado, suficiente para o escopo deste exercício, sem Redis |
| Chave de API interna | `exigir_api_key`, cabeçalho `X-API-Key`, opcional via `INTERNAL_API_KEY` | já implementado; o frontend lê a chave de `VITE_API_KEY` e o workflow n8n envia o mesmo valor num cabeçalho no nó HTTP Request |

O acesso ao Postgres usa a mesma biblioteca (`langgraph-checkpoint-postgres`)
e a mesma variável de ambiente (`DATABASE_URL`) independentemente do
provedor, então essa parte do código não muda por causa da troca de
Supabase para Azure, só o valor da variável de ambiente aponta para outro
host.

## Versionamento de `data/biotecpredict.db`

A Fase 1 definiu como requisito não funcional (RNF4, `specs/requirements.md`)
nunca versionar `data/biotecpredict.db`, mantendo-o fora do histórico de
commits. Esse requisito segue valendo para a Fase 1 e não é alterado
retroativamente. Para o deploy da Fase 2, o arquivo precisa estar
disponível no ambiente do Render, que não tem acesso a nenhum passo
manual de cópia de arquivo na camada gratuita. A partir desta branch,
`data/biotecpredict.db` passa a ser versionado, gerado a partir do
dataset curado em `data/simulacao_causa_raiz/` (15 lotes, scores e
classificações já validados contra o `ComplianceService`/`MLModel` reais
do BiotecPredict, ver o README daquela pasta), para embarcar
automaticamente em todo deploy.

## Issues, todas dentro de `chore/deploy-producao-fase02`

O guardrail de CORS restrito e limite de taxa por IP, que era a issue 1
deste plano, já foi implementado e faz parte de `feature/governanca-fase02`
(PR #63, mergeado), porque é um requisito de governança da Fase 2, não
algo exclusivo de produção. As quatro issues abaixo são as que restam,
correspondendo às issues #58, #59, #60 e #61 no GitHub.

### Issue 1, Checkpointer condicional, SqliteSaver local ou PostgresSaver em produção
- **Contexto:** o disco local do Render não sobrevive ao ciclo de dormir
  e acordar da camada gratuita, os checkpoints do grafo, o estado do
  humano no ciclo entre perguntas, se perderiam a cada ciclo. A mesma
  fragilidade vale para a tabela `eventos_log` (observabilidade, log
  estruturado em banco), incluída aqui pelo mesmo motivo.
- **Escopo:** `graph.py::_criar_checkpointer` escolhe o `PostgresSaver`
  quando `DATABASE_URL` estiver definida, apontando para a instância do
  Azure Database for PostgreSQL, senão mantém o `SqliteSaver`, sem
  nenhuma mudança no ambiente de desenvolvimento sem essa variável.
  `config.py::_HandlerBancoDeDados` segue a mesma regra para
  `eventos_log`, na mesma instância de Postgres.
- **Critérios de aceite:** teste automatizado cobre os dois caminhos, com
  `DATABASE_URL` apontando para um Postgres simulado e sem ela; rodar
  localmente sem nenhuma variável de ambiente nova continua funcionando
  exatamente como antes. Testar contra uma instância real do Azure
  Database for PostgreSQL fica para o deploy de verdade (issue 3).

### Issue 2, Relatório persistido em banco de dados, não em disco
- **Contexto:** mesmo problema de persistência da issue anterior, agora
  para os dados do relatório de cada investigação (o PDF é gerado sob
  demanda a partir do checkpoint, nunca salvo em disco, não faz parte
  deste problema).
- **Escopo:** `salvar_relatorio()` grava o `Diagnostico` numa tabela
  `relatorios`, na mesma instância SQLite local (padrão) ou Postgres
  (quando `DATABASE_URL` estiver definida) do checkpointer e do
  `eventos_log`. `resumo_diario.py` e a tool `consultar_recorrencia`
  passam a consultar essa tabela. A rota `GET /reports/{arquivo}` é
  substituída por uma rota que monta a resposta a partir do banco.
- **Critérios de aceite:** teste cobre os dois caminhos; um relatório de
  uma investigação concluída continua consultável depois de simular um
  reinício do processo.

### Issue 3, Deploy real, Render, Vercel e Azure
- **Contexto:** subir a aplicação de verdade, uma vez, depois que as
  issues anteriores estiverem prontas e testadas localmente.
- **Escopo:** configuração do serviço web no Render, comando de build e
  de início, variáveis de ambiente, incluindo `INTERNAL_API_KEY` e
  `DEEPSEEK_API_KEY`; configuração de build no Vercel, `VITE_API_URL`
  apontando para o domínio do Render e `VITE_API_KEY` com o mesmo valor
  de `INTERNAL_API_KEY`; criação da instância do Azure Database for
  PostgreSQL, com a string de conexão em `DATABASE_URL`.
- **Critérios de aceite:** uma investigação completa, Ishikawa e cinco
  porquês, rodada de ponta a ponta contra a URL de produção, o frontend
  do Vercel conversando com o backend do Render; relatório final
  consultável mesmo depois de o backend dormir e acordar de novo.

### Issue 4, Documentação do deploy
- **Contexto:** registrar o processo para conseguir reproduzir e
  reaprender depois, sem depender só da memória desta sessão.
- **Escopo:** `docs/deploy-producao.md`, passo a passo, contas
  necessárias, variáveis de ambiente, comandos, URLs finais, limitações
  conhecidas documentadas explicitamente, o tempo de inicialização do
  Render na camada gratuita e a validade de 12 meses da camada gratuita
  da Azure.
- **Critérios de aceite:** alguém consegue reproduzir o deploy do zero só
  seguindo o documento, sem precisar perguntar nada a mais.

## Ordem sugerida

1, checkpointer, depois 2, relatórios, depois 3, deploy real, depois 4,
documentação.

Só começa depois que a Fase 2 estiver rodando cem por cento local,
nenhuma destas issues compete em prazo com as issues de
`specs/fase02/gitflow.md`.
