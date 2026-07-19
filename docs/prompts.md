# Prompts utilizados no desenvolvimento

Registro dos principais prompts usados com o assistente de IA (Claude Code)
para planejar, projetar e implementar o Root-Spector. Prompts
editados/resumidos para clareza, mantendo a intenção original — focado no
escopo, na arquitetura, nos processos/ferramentas e nas decisões de
execução que construíram o resultado final entregue.

## Planejamento

1. *"Vamos construir um Agente de IA para um processo de qualidade
   industrial. Quero aprender o método spec-driven development do Claude
   Code para aplicar neste projeto, junto com arquitetura clean code."*
   → Definiu o método de trabalho (explorar → planejar → implementar →
   verificar, com specs versionadas antes do código).

2. *"Quero que este agente seja adaptável para outras áreas de negócio... o
   processo de tratamento de NC é igual para todo tipo de processo
   produtivo."*
   → Definiu o requisito central de adaptabilidade: regras/parâmetros
   externalizados, motor genérico.

3. *"A API que chama o LLM vai ser aberta pro usuário escolher e mudar de
   API e LLM quando ele quiser. Preciso ter tools, workflow, e o agente que
   chama o LLM para decidir na parte que for agêntica, e não for workflow."*
   → Definiu a arquitetura híbrida workflow/agente e a camada de LLM
   plugável.

4. *"Não tenho muito tempo, entrega até 20/07. Preciso cumprir os critérios
   de avaliação, mas de forma simples, mais simples possível."* + colagem
   do enunciado completo do Mini-Projeto (Módulo 2, IA para DEVs).
   → Substituiu o desenho inicial (Clean Architecture + FastAPI) por um
   escopo mínimo que cumpre 100% do rubric: LangGraph obrigatório, ≥1 tool,
   memória no estado, saída estruturada, README, docs/prompts.md, slides.

5. Perguntas de esclarecimento respondidas pelo usuário: modelo de LLM
   padrão = Gemini (gratuito); projeto individual; incluir testes básicos;
   commits feitos pelo próprio usuário, não pelo assistente.

6. *"Crie a arquitetura do sistema, pastas, as specs, documentação inicial
   etc."* (após uma correção explícita de que não era para implementar
   código ainda, só planejar)
   → Gerou a estrutura de pastas, stubs de módulos (sem lógica),
   `specs/requirements.md`, `specs/design.md` e a documentação inicial
   (este arquivo, README, slides).

7. *"Vamos criar branches de desenvolvimento (máximo 5), issues, milestones
   e quadro kanban. Vamos planejar isso localmente primeiro."* + *"Quadro
   kanban: Backlog, Fazendo, Revisando, Concluído — quero poucas etapas e
   confiança de que são boas etapas."*
   → Gerou `docs/gitflow.md` (v1): 5 branches de feature ligadas a 5
   milestones, kanban de 4 colunas, convenção de commit simples.

8. *"Vamos ter branch develop, CI/CD na develop, e só mergear pra main se
   passar. Seguir fielmente as regras do Gitflow, padrões de commit,
   semântica de PR — mesmo o projeto sendo pequeno, porque aprendemos isso
   no curso."*
   → Reescreveu `docs/gitflow.md` (v2) para o modelo Gitflow clássico
   completo: `main`/`develop`/`feature/*`/`release/*`/`hotfix/*`, gate de
   CI antes de merge, Conventional Commits, template de PR, merge `--no-ff`.

9. *"Vamos fazer este agente como complemento do BiotecPredict (minha
   outra plataforma, que classifica qualidade de lote/bioprocesso a partir
   de biosensores). Vamos criar a base de dados simulando situações reais,
   com o BiotecPredict como referência. Os lotes reprovados/não-conformes
   do BiotecPredict seriam a entrada deste agente."* + link do repositório
   do BiotecPredict.
   → Definiu o domínio do agente: complemento de causa raiz do
   BiotecPredict, biotecnologia/bioprocesso. O assistente buscou o schema
   real do BiotecPredict (README do repositório) para alinhar o schema de
   dados simulados (`batch_id`, `timestamp`, `temperature`, `pH`,
   `dissolved_oxygen`, `pressure`, `agitator_speed`) e escreveu
   `specs/requirements.md`, `specs/design.md`, `README.md`,
   `docs/gitflow.md` e `slides/apresentacao.md` de acordo.

10. *"A saída do BiotecPredict é um database em SQLite, ele persiste os
    dados gerados na análise neste banco... precisamos planejar a entrada
    de dados no agente com base nesta saída do BiotecPredict."*
    → O assistente buscou o código-fonte real do BiotecPredict
    (`backend/models/batch.py`, `backend/models/sensor_reading.py`) via
    `git/trees` da API do GitHub e confirmou o schema de `batches`
    (`compliance_score`, `risk_prediction`) e `sensor_readings`. Redesenhou
    a entrada do agente como uma consulta SQL (`SELECT` em `batches`)
    contra um banco SQLite simulado com esse schema exato, em vez de um
    arquivo JSON de exemplo solto. **Erro cometido nesta rodada** (corrigido
    no ponto seguinte): concluiu, com base só nos dois arquivos de modelo,
    que `ACCEPTABLE`/`WARNING`/`CRITICAL` do README "não existiam no
    código" — afirmação incorreta, corrigida pela usuária.

11. *Correção da usuária:* **"A análise está incorreta... são dois campos
    diferentes, e ambos são reais"** — apontou que `risk_prediction`
    (ML, `backend/ml/model.py`/`ml_service.py`) e `classification`
    (`ACCEPTABLE`/`WARNING`/`CRITICAL`, calculada por
    `backend/services/compliance_service.py`, exposta em
    `backend/api/routes/compliance.py`) são sinais **independentes**, e
    citou linhas/thresholds específicos.
    → O assistente buscou `compliance_service.py` e `compliance.py` direto
    no repositório pra verificar antes de corrigir qualquer doc. Confirmou:
    a correção da usuária estava certa em tudo, incluindo um detalhe que
    nem ela tinha certeza (inconsistência real de threshold *dentro* do
    próprio BiotecPredict — uma docstring diz "WARNING 60-79", a que roda
    de fato usa `>=45`). Corrigiu `specs/requirements.md`, `specs/design.md`,
    `README.md`, o artefato publicado do checklist/fluxo, e a memória
    `reference_biotecpredict_repo.md`, deixando explícito que `compliance_score`
    e `risk_prediction` são as duas colunas persistidas, e `classification`
    precisa ser recalculada pelo agente (replicando a regra real:
    `score>=80` ACCEPTABLE, `>=45` WARNING, `<45` CRITICAL) já que não é
    uma coluna do banco.

12. *"A inconsistência no BiotecPredict foi corrigida, o valor correto é
    45, e o frontend vai ser arrumado também."* → Confirmação de que o bug
    encontrado no ponto anterior já foi corrigido na fonte; a memória
    `reference_biotecpredict_repo.md` foi atualizada para não sinalizar mais
    isso como discrepância viva. Nenhuma doc do Root-Spector precisou mudar
    (já usava 45).

13. *"O agente vai receber sim todo o resultado da análise feita pelo
    BiotecPredict, inclusive os parâmetros. O que o agente vai descobrir é
    qual foi a causa raiz do problema, ajudando o operador a entender com
    base no método de 5 porquês... a próxima pergunta sempre depende da
    resposta anterior."*
    → Mudança central de arquitetura: o agente deixa de "descobrir qual
    parâmetro está fora da faixa" (isso vira determinístico, calculado em
    `preparar_contexto` a partir de `sensor_metrics`) e passa a **facilitar
    o método dos 5 Porquês**. O assistente buscou `get_sensor_metrics()`
    (`compliance_service.py`) pra confirmar exatamente que dado já vem
    pronto do BiotecPredict (`average`/`min`/`max`/`ideal_min`/`ideal_max`/
    `acceptable_min`/`acceptable_max` por sensor — mas sem apontar
    explicitamente qual sensor violou a faixa, exigindo comparação
    client-side).

14. Pergunta do assistente sobre se o operador participa interativamente de
    cada porquê (human-in-the-loop) ou se o agente roda os 5 sozinho:
    *"A primeira pergunta será sempre com base no desvio de lote
    identificado... os 5 porquês partem destas evidências... o operador
    vai responder... aí o agente pergunta de novo..."* + confirmação de que
    o loop roda sempre exatamente 5 vezes, no máximo 1 consulta à
    ferramenta por porquê.
    → Confirmou human-in-the-loop de verdade (não um loop autônomo). Levou
    ao redesenho de `models.py` (`PorQue` substitui `HipoteseCausa`),
    `state.py` (`cadeia_porques`, `numero_porque`, `pergunta_atual`
    substituem o estado genérico anterior), `nodes.py`/`graph.py`
    (`agente_investigador` vira `formular_porque` + novo nó
    `perguntar_operador` com `input()` bloqueante), e todas as specs/README/
    gitflow/artefato correspondentes.

15. *"Renomeie X para Y"* (duas rodadas de rename: manter `formular_porque`
    ao invés de reverter pro nome antigo; renomear `gerar_resposta_final`
    para `gerar_causa_raiz`) → ajustes de nomenclatura aplicados em todos os
    módulos/specs/docs/artefato de uma vez, sem mudança de comportamento.

16. *"Em qual arquivo consta o desenho do processo, com o papel do
    operador, como um mapeamento de processo produtivo mesmo?"* + *"Sim,
    pode criar um artefato visual tipo BPMN."*
    → Identificou que nenhum arquivo tinha um mapeamento de processo formal
    (raias por ator) — o que existia era só o fluxo técnico do grafo. Gerou
    um artefato BPMN novo (raias Biorreator/Sensores, BiotecPredict,
    Root-Spector, Operador) mostrando o processo produtivo de ponta a
    ponta, não só os nós do LangGraph.

17. *"O operador responde as perguntas e recebe o relatório para validação
    ou pedir ajuste... a evidência do primeiro ciclo fica guardada... Se de
    primeira estiver tudo certo, quem investiga é o setor da Qualidade,
    com ajuda de outro agente que procura num RAG (documentação, legislação,
    ANVISA, bibliografia)... o relatório final vai pra Garantia da
    Qualidade, não pro operador."*
    → O assistente identificou que essa era uma adição de escopo bem maior
    que as anteriores (um segundo agente com RAG é essencialmente outro
    projeto) e perguntou explicitamente antes de agir. A usuária confirmou:
    documentar as duas coisas (loop de validação + Fase 2 RAG) como
    **roadmap**, sem implementar nenhuma das duas nesta entrega. Levou à
    seção "Roadmap" em `specs/design.md`, aos novos itens em "Fora de
    escopo" de `specs/requirements.md`, e a uma seção "Fase 2" no artefato
    BPMN, visualmente diferenciada (fundo tracejado, faixa "roadmap") do
    que está de fato implementado.

18. *"A Garantia da Qualidade recebe o relatório final da recomendação de
    ação corretiva, Kaizen de melhoria e PDCA estruturado. E a Garantia da
    Qualidade executa este plano e verifica se foi eficaz ou não, com base
    em reincidência do problema."*
    → Extensão do roadmap da Fase 2 (não implementação): fechou o ciclo
    PDCA completo (Plan = recomendação do Agente RAG; Do = execução pela
    Garantia da Qualidade; Check = verificação de eficácia por
    reincidência; Act = novo plano se reincidir) no mapa de processo e em
    `specs/design.md`. Manteve o entendimento já acordado de que essa Fase
    2 inteira é roadmap, não código desta entrega.

19. *"Como devemos conduzir a pergunta dos 5 porquês [se houver múltiplos
    parâmetros fora da faixa]? Existe alguma referência na literatura ou
    de algum agente que já exista para essa finalidade?"*
    → O assistente pesquisou (WebSearch) literatura de qualidade (ASQ,
    KaiNexus, ITONICS: 5 Porquês não prioriza entre causas múltiplas,
    recomenda-se Ishikawa/Fishbone primeiro) e agentes de IA pra RCA já
    publicados, encontrando um artigo acadêmico (Springer) com arquitetura
    multiagente próxima ao caso, mas paywalled.

20. *"O correto é começar com perguntas para mapear o diagrama de Ishikawa,
    e o agente analisa o resultado, depois disso parte pro 5 Porquês com
    base no resultado do Ishikawa... Essa arquitetura centra-se em um
    Agente Orquestrador que coordena a análise... Um agente de relatório
    sintetiza as descobertas... usando as categorias do diagrama de
    Ishikawa..."* (usuária descreveu o conteúdo do artigo acadêmico
    referenciado no ponto anterior, incluindo o estudo de caso de ruptura
    de mangueira hidráulica e o enquadramento em Indústria 5.0).
    → Mudança metodológica central: o agente deixa de perguntar
    diretamente sobre o parâmetro fora da faixa e passa a mapear o
    contexto (6 categorias Ishikawa) antes de aprofundar com 5 Porquês,
    agora ancorado na categoria identificada. O assistente perguntou
    explicitamente antes de mudar o código: (1) isso entra na
    implementação desta entrega ou fica só documentado? (2) "Orquestrador"
    e "Agente de Relatório" viram agentes/grafos separados (fiel ao
    artigo) ou nós do mesmo grafo (mais simples)? A usuária confirmou:
    entra na implementação agora, e como nós do mesmo grafo — não
    replicar a arquitetura multiagente do artigo, só a metodologia.
    Levou à reescrita de `specs/design.md` (novo método, novos nós
    `formular_pergunta_ishikawa`/`orquestrar_analise`, nova seção "Decisão
    de simplicidade"), `specs/requirements.md` (RF4-RF9 reescritos),
    `README.md`, todos os stubs de `root_cause_agent/`, `docs/gitflow.md`
    (tasks do M3/M4), e os dois artefatos visuais publicados.

21. *"Na Garantia da Qualidade recebe o relatório final, avalia junto com a
    Coordenação da Produção e decide se vai seguir o plano sugerido pelo
    Agente RAG ou mudar alguma coisa. Depois disso vai para etapa de
    execução."*
    → Refinamento do roadmap da Fase 2 (ainda não implementação): inseriu
    um novo passo colaborativo (Garantia da Qualidade + Coordenação da
    Produção avaliam e decidem manter/ajustar o plano) entre "recebe o
    relatório" e "executa (Do)" no PDCA. Atualizou o artefato BPMN e
    `specs/design.md` § Roadmap.

22. *"As saídas de relatórios devem ser todas em JSON e HTML... Vamos fazer
    uma plataforma simples igual o BiotecPredict. Precisamos fazer a
    interface para o operador responder as perguntas, e daí o agente gera
    um link HTML para acessar o resultado após o operador validar e
    aprovar suas respostas... O banco de dados eu preciso pensar como vai
    ser o input, visto que o BiotecPredict tem um output de um arquivo
    SQL... vai ter mais de um lote para ser analisado... o arquivo
    `biotecpredict.db` deve ficar fora do git clone, dentro da pasta
    `data/`... vai abrir a interface do usuário no localhost, com apenas
    uma tela, já mostrando os lotes no banco e quais estão disponíveis."*
    → Mudança de escopo: interface web (antes explicitamente fora de
    escopo por simplicidade) passa a ser real, dado que o resultado
    precisa ser interativo e navegável. O assistente identificou que
    `input()` bloqueante não funciona atrás de uma API web e propôs o
    mecanismo de `interrupt()` + checkpointer do LangGraph antes de
    perguntar detalhes de stack/aprovação/CLI. A usuária escolheu React +
    TypeScript (mesma stack do BiotecPredict) e incluir o fluxo completo
    de "pedir ajuste" já nesta entrega; o assistente recomendou manter o
    frontend deliberadamente mínimo (sem router, sem lib de estado) e
    preservar `main.py` como harness de teste, dado o tempo disponível.
    Levou a um plano detalhado (backend FastAPI + frontend React mínimo +
    reports.py com saída JSON+HTML + banco não versionado) e ao início da
    implementação real (models.py, state.py, config.py, tools.py).

23. *"Remova as informações de contexto interno da entrega; mantenha a
    linguagem formal, direta e objetiva. Atualize todos os arquivos do
    repositório com o novo escopo — temos arquivos desatualizados. O
    agente recebe os resultados dos lotes analisados pelo BiotecPredict e
    classifica quais têm risco alto/médio, para o operador escolher qual
    investigar. O banco de dados eu já coloquei em `data/`, é esse que
    vamos usar."*
    → Correção de linguagem: removida uma menção operacional específica de
    um comentário em `.gitignore`, substituída por linguagem neutra.
    Confirmação de que a classificação de risco já exibida na lista de
    lotes é o que orienta a escolha do operador (não uma mudança de
    design, uma reafirmação). Achado importante ao inspecionar
    `data/biotecpredict.db` naquele momento: era uma exportação real de
    uma instância do BiotecPredict (27 lotes, 1337 leituras, incluindo uma
    tabela `predictions` vazia e 6 lotes com `compliance_score` nulo
    apesar de `status='COMPLETED'`). Isso levou a: renomear o caminho
    padrão em `config.py` para `biotecpredict.db`; documentar em
    `specs/design.md`/`specs/requirements.md` o tratamento de
    `compliance_score` nulo (lote excluído da lista de elegíveis, não
    erro) e a tabela `predictions` (presente no schema, não utilizada);
    reescrita de `README.md`, `specs/design.md`, `specs/requirements.md` e
    `docs/gitflow.md` para refletir a plataforma web como escopo real.

24. *"Pontos em aberto no escopo: em `perguntar_operador`, o campo não deve
    aceitar resposta vazia nem evasiva ('não sei'), sinalizando 'Este tipo
    de resposta não é aceito'. Se a resposta não for inválida mas o agente
    considerar não informativa, isso deve ser registrado junto com a
    resposta, sinalizado ao operador, e ele ganha uma nova chance — só 2
    chances por pergunta. Na 2ª, se ainda não for informativa, o agente
    segue para a próxima pergunta e registra as 2 respostas não
    informativas."*
    → Desenhada a validação da resposta do operador em duas camadas:
    Camada 1, determinística (`tools.py::validar_resposta_operador`, função
    Python simples, não uma `@tool` do LLM — checar vazio/frase evasiva
    fixa não exige julgamento de modelo), tentativas ilimitadas, nunca
    conta como uma resposta real. Camada 2, agêntica (novo nó
    `avaliar_informatividade`), julga se a resposta de fato informa a
    pergunta, no máximo 2 tentativas, registrando ambas quando as duas
    falham. `models.py` (`RespostaIshikawa`/`PorQue`) ganhou `tentativas`/
    `informativa`; `state.py` ganhou `tentativas_pergunta_atual`. Ver
    `specs/design.md` § Validação da resposta do operador.

25. *"Capturar o erro [de chamada ao LLM] em cada nó; a API devolve ao
    frontend 'Serviço de IA indisponível, recarregue a página'; o
    thread_id/checkpoint daquela investigação fica pausado pra tentar de
    novo."*
    → Desenhado `FalhaLLMError` (definida em `nodes.py`), levantada por
    cada nó agêntico ao capturar falha de rede/rate limit/chave inválida na
    chamada ao LLM; a API traduz isso em HTTP 503 com a mensagem definida.
    Como o `SqliteSaver` só grava um novo checkpoint após um nó terminar
    com sucesso, a exceção nunca chega a ser persistida — o `thread_id` já
    fica naturalmente pausado no último ponto bem-sucedido, sem nenhuma
    lógica extra de "salvar progresso". Ver `specs/design.md` §
    Tratamento de falha na chamada ao LLM.

26. *"Vamos fazer fallback para Anthropic e OpenAI [depois do Gemini]. Se o
    fallback não der certo, as mensagens de tela no frontend persistem e o
    operador terá que aguardar o serviço retornar mais tarde."*
    → Implementado em `config.py::get_llm()`: cadeia Gemini (oficial,
    gratuito, testes/prototipagem) → Anthropic → OpenAI via
    `ChatModel.with_fallbacks(...)`, cada camada só ativada se a respectiva
    chave (`ANTHROPIC_API_KEY`/`OPENAI_API_KEY`) estiver no `.env` — rodar
    só com a chave do Gemini continua funcionando sem exigir as outras
    duas. Só se todos os provedores configurados falharem é que
    `FalhaLLMError`/HTTP 503 entram em ação; sem retry automático em loop,
    a mensagem de erro persiste até o operador recarregar mais tarde.
    Adicionadas dependências `langchain-anthropic`/`langchain-openai`
    (`pyproject.toml`) e variáveis correspondentes (`.env.example`). A
    cadeia ganhou depois um 2º provedor gratuito, Groq, entre Gemini e
    Anthropic — mesmo padrão de ativação condicional pela chave.

27. *"Implementa as duas correções [na validação de entrada da tool]."*
    → `consultar_leituras_biosensor` (`tools.py`) deixou de receber
    `batch_id` como argumento do LLM: agora vem injetado do estado
    (`nc_input.batch_id`) via `Annotated[AgentState, InjectedState]`,
    travando a consulta no lote sob investigação em vez de confiar no
    modelo para escolher o `batch_id` certo. `data_inicio`/`data_fim`
    passaram a ser validadas com `datetime.fromisoformat(...)` (formato
    inválido ou janela invertida devolve mensagem de erro ao LLM, não mais
    uma busca silenciosa sem resultado).

28. *"Todas as branches estão sendo chamadas de feature, mas não são. Esta
    etapa de gerador de banco de dados não existe mais, revise o gitflow
    conforme a especificação atual e escopo do projeto. O Gitflow não está
    seguindo as convenções de commit, branches e PR. Ajuste isso."* seguido
    de *"atualiza todos os arquivos dentro de specs/ para o escopo do
    projeto Root-Spector [...] Analise as convenções e especificações do
    gitflow, com base na metodologia oficial, e atualize o gitflow.md."*
    → Correção em duas etapas. Primeiro ajuste (branch-safe, mas não
    fielmente oficial): prefixos por tipo (`docs/`, `chore/`, `feature/`,
    `test/`). Segundo ajuste, depois de consultar o artigo original de
    Vincent Driessen ("A successful Git branching model", nvie.com): o
    Gitflow clássico **não define** categorias de branch por tipo de
    conteúdo — "feature branch" é o termo genérico pra qualquer branch de
    trabalho que não seja `release-*`/`hotfix-*`. Revertido para
    `feature/*` uniforme, com a distinção de tipo (docs/testes/config)
    movida pro **tipo do commit** (Conventional Commits), não pro prefixo
    da branch. `specs/product.md`, `specs/tech.md`, `specs/structure.md` e
    `specs/ci-cd.md` — cópias de referência do BiotecPredict que ainda
    descreviam FastAPI+SQLAlchemy+RandomForest+Docker+TailwindCSS — foram
    reescritas para o escopo real do Root-Spector.
    `specs/gitflow.md` virou a convenção estável (regras, citando a fonte
    oficial), e `docs/gitflow.md` o plano operacional (milestones, branches
    concretas, checklist de issues) que aplica essa convenção — divisão que
    evita duplicar/divergir as regras entre os dois arquivos.

29. *"Eu quero rodar ci/cd apenas nas branches de feature/, bugfix/ e
    hotfix/ e develop/. E os testes do GitHub Actions devem ser disparados
    apenas a partir da abertura do PR."*
    → `specs/ci-cd.md` ajustado: `push` só em `develop`; `pull_request` só
    com destino `develop` (cobre PRs de `feature/*`/`bugfix/*`/`hotfix/*`
    na prática, já que são as únicas branches que abrem PR contra
    `develop`). Push direto nas branches de trabalho não dispara mais nada
    — só a abertura/atualização do PR. `release/*`→`main` deixou de
    disparar o workflow automaticamente nesta entrega (verificação manual,
    já que o PR de origem já passou pelo CI ao entrar em `develop`).
    `bugfix/*` era uma branch nova, não estava no modelo — adicionada em
    `specs/gitflow.md` como extensão explícita (não faz parte do artigo
    original de Driessen, mas é prática comum: corrige bug encontrado
    *durante* o desenvolvimento, a partir de `develop`, distinta de
    `hotfix/*`, que corrige algo já em produção, a partir de `main`).

30. *"Temos um arquivo gitflow.md dentro de docs/ e dentro de specs/,
    unifique os dois eliminando informações redundantes."*
    → `docs/gitflow.md` (plano operacional) tinha voltado a explicar por
    extenso "por que `feature/*` uniforme" — quase um parágrafo repetido
    do que já está em `specs/gitflow.md` (convenção) — e uma seção de
    CI/CD que restatava (e estava desatualizada em relação a) os triggers
    já descritos em `specs/ci-cd.md`. Aparado para uma linha de referência
    em cada caso; `docs/gitflow.md` ficou só com o que é genuinamente
    operacional e não vive em nenhum outro arquivo (branches concretas,
    checklist de issues por milestone); `specs/gitflow.md` não precisou de
    mudança, já era só a convenção.

31. *"Não precisamos explicar o que é o Gitflow, só precisa ficar claro
    como estamos usando o Gitflow no escopo do projeto. Como estamos
    aplicando o método."*
    → `specs/gitflow.md` tinha virado, em parte, uma aula sobre o método
    (citação do artigo original de Driessen, nota de terminologia sobre o
    que "feature branch" significa academicamente, justificativa de que
    `bugfix/*` "não está no artigo original mas é prática comum"). Cortado
    tudo isso — ficou só o que aplica ao projeto: quais branches existem,
    de onde nascem, pra onde vão, e a convenção de commits/PRs/Kanban.
    Removida também a seção "Fonte" (citação acadêmica isolada, sem
    função de aplicação).

32. *"Não precisamos mais do script para gerar banco de dados, o banco já
    está pronto, remova do escopo do projeto esta função."*
    → O script gerador de banco de dados foi removido do escopo naquele
    momento. `tests/fixtures/biotecpredict_teste.db` — já gerado
    anteriormente — passa a ser um arquivo estático versionado (o
    `.gitignore` tinha uma regra `tests/fixtures/*.db` assumindo que o
    arquivo seria regerado por script; removida, senão os testes
    quebrariam em qualquer clone novo do repositório, sem como recriar a
    fixture). Atualizado: `specs/design.md`, `specs/requirements.md`
    (RNF4), `specs/structure.md`, `specs/tech.md`, `specs/product.md`,
    `docs/gitflow.md` (checklist M2), `README.md`.

33. *"No docs/gitflow.md — o plano operacional, todas as branches estão
    como feature, mas elas não são todas features, ajuste isso
    corretamente com o tipo de arquivo que vamos subir em cada branch,
    seguindo as convenções do gitflow."*
    → Retomada do ponto levantado antes (prefixos de branch por tipo,
    depois revertido pra `feature/*` uniforme baseado no artigo de
    Driessen). Desta vez, decisão definitiva na direção oposta: branches
    de trabalho passam a usar `docs/*`, `chore/*`, `feature/*`, `test/*`
    conforme o tipo de arquivo predominante, mesma taxonomia dos tipos de
    commit — `feature/*` reservado só pra M3 (código novo do agente).
    Atualizado `specs/gitflow.md` (tabela + descrição do modelo de
    branches), `specs/ci-cd.md` (triggers/regra de merge/troubleshooting
    citavam só feature/bugfix/hotfix) e `docs/gitflow.md` (tabela de
    branches × milestones): M1→`docs/`, M2→`chore/`, M3→`feature/`,
    M4→`test/`, M5→`docs/`.

34. *"Revise o plano operacional com relação à criação das issues e
    branches, e milestones, garanta que tudo está conectados e
    relacionados."*
    → Revisão de `docs/gitflow.md` encontrou 4 lacunas de conexão: (1) não
    ficava explícito que cada item de checklist não marcado vira 1 issue,
    atribuída ao milestone e rotulada com a label de tipo correspondente —
    itens já marcados não geram issue retroativa; (2) não ficava explícito
    que o PR de cada branch fecha *todas* as issues do seu milestone via
    "Closes #N"; (3) "Release" (branch `release/v1.0-entrega`) não estava
    listada como milestone junto das outras 5, ficava solta; (4) dois
    pré-requisitos identificados numa investigação de viabilidade de
    automação nunca viraram passo no plano: o board GitHub Projects #9 já
    existe mas com a coluna Status nos nomes padrão do template (`Sprint
    In progress`/`Sprint In review`/`Done`, não `Fazendo`/`Revisando`/
    `Concluído`), e as labels de tipo (`docs`/`chore`/`feature`/`test`/
    `bugfix`) ainda não existem no repositório (só as labels padrão do
    GitHub). `docs/gitflow.md` ganhou: "Release" como 6º milestone na
    tabela; nova seção "Como issues, branches e milestones se conectam";
    e "Passo zero" expandido com os 2 pré-requisitos de board/labels.

35. *"Crie no máximo 10 labels, para a gente classificar as issues
    visualmente, por etapa do projeto, para ficar mais fácil de entender
    de qual etapa aquela issue se refere. Adicione no gitflow operacional
    essas labels."*
    → 6 labels de etapa (1 por milestone, dentro do limite de 10),
    complementares às labels de tipo já previstas: `m1: especificação`,
    `m2: dados & config`, `m3: implementação`, `m4: testes`, `m5:
    documentação`, `release` — cada uma com cor própria (azul → verde →
    roxo → amarelo → laranja → vermelho, progressão visual da 1ª etapa até
    a entrega). Toda issue passa a ganhar 2 labels: tipo + etapa. Adicionado
    em `docs/gitflow.md`: nova seção "Labels de etapa" e "Passo zero" item
    5.

36. *"O prompt vai subir por GitHub na documentação final, mude ele para a
    branch de documentação, e para a issue final."*
    → `docs/prompts.md` estava atribuído a M1 (`docs/especificacao-e-
    arquitetura`) como "inicial" — mas é um log vivo, atualizado a cada
    decisão do projeto inteiro, então marcar a conclusão dele em M1 não
    refletia a realidade. Removido de M1 (tabela de branches e checklist);
    mantido só em M5 (`docs/documentacao-final`), como a última issue do
    milestone — só fecha depois de todas as outras, já que o log só está
    completo no fim do projeto.

37. *"Crie um script para automatizar o plano operacional descrito no
    docs/gitflow.md [...] Não é pra fazer nenhum commit [...] pode colocar
    junto do projeto sim, faz parte da execução."*
    → `scripts/setup_github.py`: automatiza labels, milestones, issues
    (conectadas a milestone + label de tipo + etapa na criação) e o board
    do GitHub Projects (renomeia Status, adiciona cada issue em Backlog) —
    idempotente, sem nenhum `git commit`. Branches (vazias, sem conteúdo)
    ficam atrás da flag `--branches`, desligada por padrão. Passou por uma
    correção de rumo: a primeira versão tentava commitar arquivos reais em
    cada branch, mas a usuária confirmou que o script deveria ficar
    restrito só à estrutura do GitHub, não a commits de código. Movido de
    scratchpad temporário pra `scripts/setup_github.py` (dentro do
    repositório) a pedido explícito — "faz parte da execução" — com
    `specs/structure.md` e `docs/gitflow.md` atualizados de acordo.

38. *"O script não cria as issues das etapas M1 e M2, precisa criar, mesmo
    que já tenha feito estas etapas, precisamos executar o projeto no
    github, então tudo tem que ser feito para todas as etapas."*
    → `scripts/setup_github.py` passou a criar issue pra **todo** item do
    checklist (M1 a Release), não só os pendentes — incluindo os 7 itens
    de M1, os 3 de M2, e os 5 já feitos de M3 (`models.py`, `state.py`,
    `config.py`, `tools.py`, `pyproject.toml`), que antes ficavam de fora
    por já estarem `[x]`. Cada issue ganhou uma flag `done`: as feitas são
    criadas e fechadas na hora (`gh issue close --reason completed`,
    corpo explicando que foi "concluída retroativamente"), e vão pro board
    na coluna Concluído em vez de Backlog. `docs/gitflow.md` § Passo zero
    atualizado.

39. *"Crie uma página em HTML com a minha apresentação, conforme os
    critérios da apresentação descritos no arquivo pdf na pasta
    escopo-avaliacao/."*
    → Lido o PDF oficial (§3, §5.1, critério 4 e checklist final) pra
    confirmar os elementos exigidos: problema, proposta do agente,
    entrada, saída, ferramenta utilizada e fluxo geral — em até 2 slides.
    Criado um deck real de 2 slides (não um documento rolável), navegação
    por clique/setas do teclado, scroll-snap, com "ferramenta utilizada"
    destacada como bloco próprio (o PDF cobra isso explicitamente em 3
    lugares diferentes). Paleta e tipografia consistentes com os outros
    artefatos HTML já publicados nesta sessão (teal/verde, serif Charter
    pros títulos, mono pros rótulos/código).

40. *"Adicione mais uma informação, onde é workflow, onde o processo é
    agêntico, onde chama a tool, e o fallback."*
    → Fluxo do slide 2 ganhou legenda de 4 cores (workflow/agêntico/
    ferramenta/operador) aplicada a cada nó do pipeline — `preparar_contexto`
    marcado como workflow, os 4 nós de LLM como agêntico, Ishikawa e 5
    Porquês com a nota "↳ pode chamar a ferramenta" (são os únicos que
    chamam a tool), e os dois pontos de interação como operador. Adicionado
    um card novo, "Fallback de LLM", ao lado da ferramenta.

41. *"Não é pra fechar nenhuma issue, e nem pra alterar o nome das colunas
    no board."*
    → Removido de `scripts/setup_github.py`: o `gh issue close` (issues
    "feitas" continuam abertas, só com o corpo explicando que já foram
    concluídas retroativamente) e a função `ensure_status_columns` inteira
    (nenhuma mutação GraphQL na coluna Status). O board passa a usar os
    nomes originais do template (`Backlog`/`Done`) em vez dos renomeados
    (`Backlog`/`Concluído`) pra decidir onde cada issue entra. `docs/gitflow.md`
    § Passo zero atualizado (item de rename removido, board section ajustada).

42. *"O nome das colunas do board são Backlog, In progress, In review,
    Done, atualiza no escopo do projeto, no plano operacional do gitflow e
    no script."*
    → `specs/gitflow.md` § Kanban tinha uma inconsistência interna: o
    título da sequência ainda dizia `Backlog → Fazendo → Revisando →
    Concluído` (português), mas os bullets logo abaixo já tinham sido
    corrigidos pra `In Progress`/`In Review`/`Done` (inglês) numa edição
    anterior — sobrou só o título desatualizado. Corrigido pra bater com
    o board real. `docs/gitflow.md` também tinha `Fazendo`/`Revisando`/
    `Concluído` na descrição de como as issues se movem pelo board —
    corrigido pros nomes reais. `scripts/setup_github.py` já usava
    `Backlog`/`Done` desde o ponto anterior, não precisou de mudança.

43. *"Não citar que as etapas M1 e M2 já foram concluídas, abre as issues
    como se nada tivesse sido iniciado ainda."*
    → Removida por completo a distinção `done`/pendente introduzida
    antes: `ISSUES` voltou a ser uma lista uniforme (sem a 4ª posição
    booleana), nenhum corpo de issue menciona conclusão prévia, e
    `add_issues_to_board` volta a colocar toda issue em Backlog, sem
    diferenciar destino por status. `docs/gitflow.md` atualizado nos dois
    pontos que ainda descreviam a distinção (Passo zero item 3, e "Como
    issues, branches e milestones se conectam").

44. *"Eu gostaria de diminuir a quantidade de issues [...] tipo 5 issues
    por etapa [...] se for possível compactar mais."* seguido de "*Tem
    como fazer testes local para ver se vai dar erro antes de criar?
    Porque a issues não dá pra corrigir se criar errado.*"
    → `ISSUES` compactada de 34 pra 19, agrupando itens relacionados do
    checklist numa única issue (ex: `models.py`+`state.py`+`config.py`+
    `pyproject.toml` viraram 1 issue de M3 em vez de 4) — máximo 5 por
    milestone (M3), várias com 2-3. Ganhou um 4º campo (`detail`) com a
    lista dos itens agrupados, incluída no corpo da issue. Nova função
    `validate_data()`, 100% local (nenhuma chamada de rede), rodando antes
    de qualquer coisa em `main()`: confere se todo milestone/label
    referenciado existe de verdade, se não há título de issue duplicado, e
    se nenhum milestone passou de 5 issues — pega erro de copiar/colar
    antes de criar qualquer coisa. Complementa o que `--dry-run` já fazia
    (mostrar o comando `gh issue create` completo, sem executar).
    `docs/gitflow.md` atualizado (contagem de issues, menção à validação).

45. *"Atualize a documentação do gitflow.md plano operacional com essa
    nova estratégia."*
    → A seção "Issues por milestone" de `docs/gitflow.md` ainda listava o
    checklist antigo, granular (34 itens soltos), sem refletir o
    agrupamento em 19 issues feito no ponto anterior — ficou desatualizada
    assim que o script mudou. Reestruturada: cada `###` de milestone agora
    lista as issues de verdade (título em negrito, batendo com
    `scripts/setup_github.py::ISSUES`), com os itens de checklist
    originais como sub-bullets dentro de cada uma — preserva o detalhe
    fino pra acompanhamento, mas deixa claro que não é mais 1 item = 1
    issue.

46. *"Garanta que o código scripts/setup_github.py também está atualizado
    com o novo escopo."*
    → Revisão linha a linha do script contra `docs/gitflow.md` e
    `specs/gitflow.md`. A maior parte já batia (ISSUES com 19 itens,
    contagem por milestone 3+2+5+3+3+3, comentário acima de ISSUES já
    mencionava a compactação) — mas o **docstring do módulo**, no topo do
    arquivo, ainda descrevia o comportamento anterior à compactação pra
    19/máximo-5. Corrigido. Sintaxe e dry-run revalidados depois da
    mudança.

47. *"Verifica se a API do GitHub está funcionando e se podemos rodar o
    script"* → depois *"Se os testes passaram e não tem erro no script, e
    ele segue exatamente o plano operacional, pode executar."*
    → Reconfirmada a saúde da API (`gh api repos/.../Root-Spector`, leitura
    real, sem `--dry-run`) e executado `python scripts/setup_github.py`
    (sem `--branches`, sem `--dry-run`) de verdade. Criados no GitHub:
    11 labels, 6 milestones, 19 issues, todas adicionadas ao board do
    projeto (#9) na coluna Backlog. Nenhuma branch criada nesta execução.

48. *"Eu acho que a descrição das issues ficou muito simples, no padrão
    convencional [de Gitflow do projeto], tem mais detalhes do projeto.
    Consegue verificar isso?"* (com exemplo de padrão: Contexto / Escopo /
    Critérios de Aceite / Branch) seguido de *"O release não vai ter
    commit e push direto na main, vai ser na develop, e abrir PR para a
    main"* e *"Continua executando as ações."*
    → `ISSUES` em `scripts/setup_github.py` deixou de ser uma tupla de 4
    campos soltos e virou uma classe `Issue` (milestone, type_label,
    title, contexto, escopo, criterios), com `build_issue_body()` gerando
    o corpo no padrão convencional (`## Contexto` / `## Escopo` /
    `## Critérios de Aceite` / `## Branch`, esta última derivada de um
    novo dict `MILESTONE_BRANCH`). `ensure_issues()` deixou de só criar —
    agora também sincroniza (`gh issue edit`) o corpo de toda issue já
    existente, tornando o texto das issues idempotente junto com o resto.
    Rodado `--dry-run` pra conferir os 19 corpos gerados, depois execução
    real: as 19 issues tiveram o corpo reescrito no GitHub, sem nenhuma
    recriação. Também corrigida a descrição do fluxo de release em
    `specs/gitflow.md` (bullet `release/*`) e `docs/gitflow.md` (tabela
    Branches × Milestones, seção de conexões, checklist da issue de
    merge): `main` nunca recebe commit/push direto — o merge de
    `release/v1.0-entrega` acontece exclusivamente via Pull Request, com
    back-merge também via PR em `develop`.

49. *"Agora, falta um ponto, precisamos criar a pasta backend para abarcar
    os códigos e tudo relacionado ao FastAPI, que vai fazer a parte do
    backend do agente na interface web."*
    → O plano original (specs/design.md, specs/structure.md) colocava
    a API dentro do próprio `root_cause_agent/`. Como nada do FastAPI
    tinha sido implementado ainda, foi uma correção estrutural pura, sem
    código pra mover: criado o pacote `backend/` na raiz do repositório,
    espelhando a separação backend/frontend que o BiotecPredict já usa.
    `root_cause_agent/` continua sendo o motor do agente puro — sem
    nenhuma dependência de FastAPI, importável e executável sozinho via o
    harness `main.py` —; `backend/` importa `root_cause_agent` como
    biblioteca (nunca o contrário) e expõe o grafo por HTTP. `reports.py`
    permanece em `root_cause_agent/` (serialização do `Diagnostico`,
    agnóstica de framework web). Atualizados: `specs/structure.md`,
    `specs/design.md` (árvore de módulos + contrato completo das rotas da
    API), `specs/tech.md`, `docs/gitflow.md`, `pyproject.toml`
    (`packages.find` passou a incluir `backend*`).

50. *"Vamos adicionar testes para o backend, openapi e os testes
    necessários para o agente não quebrar, teste para o frontend e para o
    agente. Testes para o fallback, precisamos colocar testes E2E para
    fazer localmente e no GitHub Actions."*
    → **Achado antes de implementar:** os workflows existentes em
    `.github/workflows/` não eram do Root-Spector — referenciavam um
    `requirements.txt` (pip puro), `flake8`/`black`/`isort`/ESLint (o
    projeto usa `ruff`), uma coleção Postman de outro projeto, deploy via
    `docker-compose`, e um Project board diferente do real. Batiam com o
    que `specs/ci-cd.md` já documentava como decisão própria (1 workflow,
    sem Docker/CD/E2E) — o oposto do que estava nos arquivos. Perguntado à
    usuária o que fazer: escolheu **substituir tudo** e usar **Playwright**
    pro E2E (em vez de Cypress, que o arquivo antigo usava). Os arquivos
    irrelevantes foram apagados; `ci.yml` reescrito do zero com 4 jobs:
    `lint` (ruff), `test` (pytest — agente + backend), `frontend-test`
    (Vitest), `e2e` (Playwright, depende dos dois anteriores passarem).
    Criados: `tests/test_config.py` (fallback de LLM mockado via
    `pytest-mock`), `tests/test_backend.py` (rotas de `backend/main.py`
    via `TestClient` + contrato `GET /openapi.json` via
    `openapi-spec-validator`), e a suíte E2E em Playwright (Node, próprio
    `package.json`/`playwright.config.ts` com `webServer` subindo
    backend+frontend automaticamente, sempre contra a fixture de teste e
    `LLM_PROVIDER=fake` — nunca um provedor real, por custo e
    determinismo). `pyproject.toml` ganhou `pytest-mock` e
    `openapi-spec-validator` como dev deps. Atualizados `specs/ci-cd.md`
    (reverte a decisão anterior de "sem E2E automatizado"), `specs/tech.md`,
    `specs/structure.md`, `specs/requirements.md` (novos critérios de
    aceitação) e `docs/gitflow.md` (M4 passou de 3 para 5 issues).

## Pesquisa

- *WebFetch no README do repositório do BiotecPredict* → confirmou o schema
  real de colunas (`batch_id`, `timestamp`, `temperature`, `pH`,
  `dissolved_oxygen`, `pressure`, `agitator_speed`) e a lógica de
  classificação (compliance score 0–100, três faixas), usados para desenhar
  `NaoConformidade` e o dataset simulado deste agente.

- *WebFetch em `backend/models/batch.py` e `backend/models/sensor_reading.py`
  (via `git/trees` da API do GitHub)* → confirmou o schema SQLAlchemy real:
  `batches` (id, upload_date, status, compliance_score, risk_prediction) e
  `sensor_readings` (id, batch_id, temperature, ph, dissolved_oxygen,
  pressure, agitator_speed, recorded_at). Insuficiente por si só — levou ao
  erro registrado no item 10 do Planejamento, por não checar a camada de
  serviço/API.

- *WebFetch em `backend/services/compliance_service.py` e
  `backend/api/routes/compliance.py`, depois da correção da usuária* →
  confirmou `_classify_score()` (thresholds reais: 80/45) e o endpoint
  `GET /api/v1/compliance/{batch_id}`, resolvendo a divergência do item 11.

- *WebFetch em `get_sensor_metrics()` (mesmo arquivo), depois do pivô pro
  método 5 Porquês* → confirmou o formato exato do que o BiotecPredict já
  entrega por sensor (estatísticas agregadas + faixas ideal/aceitável), e
  que ele **não** aponta explicitamente qual sensor violou a faixa —
  informação que definiu que `preparar_contexto` precisa fazer essa
  comparação ele mesmo antes de montar a `NaoConformidade`.

- *"Coloca este artigo como referência bibliográfica do projeto:
  https://link.springer.com/chapter/10.1007/978-3-032-03538-7_15"* →
  Confirmado, via busca (o link em si é pago), que é o artigo já citado de
  memória em `specs/design.md` desde o pivô pro método Ishikawa+5 Porquês:
  Bocanet, V.I., Muntean, M.H., Fleseriu, C. (2026), *"Multi-agent
  Framework for AI-Supported Collaborative Root Cause Analysis in Quality
  Assurance"*, em Advances in Production Management Systems (APMS 2025),
  IFIP AICT vol. 766, Springer. Citação completa adicionada em
  `specs/design.md` § Referência bibliográfica completa.

## Implementação (a preencher conforme o código for escrito)

- (pendente)

## Correções e melhorias (a preencher)

- (pendente)
