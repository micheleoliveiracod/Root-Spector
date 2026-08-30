# Governança e guardrails

Este documento descreve os mecanismos de proteção (guardrails) do
Root-Spector: os que já existiam desde a Fase 1, incorporados à
arquitetura do agente, e os quatro novos adicionados na Fase 2 para
limitar o abuso da interação do operador com o agente e o acesso à API.
O código correspondente
está em `root_cause_agent/nodes.py`, `root_cause_agent/tools.py` e
`backend/main.py`; a análise original de resiliência está em
`specs/fase02/design.md` (seção Governança); a prova automatizada está em
`tests/test_seguranca_prompt_injection.py`.

## Guardrails estruturais (Fase 1)

A arquitetura do Root-Spector já nasceu resiliente a entrada não confiável
por decisões de design tomadas na Fase 1, antes de qualquer trabalho
específico de segurança. Nenhum deles é um filtro de conteúdo aplicado
sobre a resposta do operador: são restrições estruturais que tornam certas
classes de ataque estruturalmente impossíveis, independente do texto
recebido.

| Guardrail | Onde | O que limita |
|---|---|---|
| Roteamento determinístico em Python | `nodes.py:rotear_apos_ferramenta`, `nodes.py:rotear_apos_avaliar` | O LLM nunca decide para onde o grafo avança, só o conteúdo de uma pergunta ou o julgamento de informatividade. Uma instrução embutida na resposta do operador não tem como alterar o fluxo da investigação |
| Segredos fora do contexto do LLM | `config.py:get_llm()` | Chaves de API são lidas do `.env` só para configurar o provedor, nunca entram em uma `SystemMessage`/`HumanMessage`. O LLM não pode revelar o que nunca recebeu |
| `batch_id` injetado, não escolhido pelo LLM | `tools.py:consultar_leituras_biosensor`, via `InjectedState` | A tool não pode ser redirecionada para consultar outro lote |
| Tool somente leitura, datas validadas | mesma tool | `SELECT` fixo, sem ação destrutiva no domínio; formato ISO e `data_inicio <= data_fim` validados antes de qualquer consulta ao banco |
| Validação determinística da resposta (Camada 1) | `tools.py:validar_resposta_operador` | Rejeita resposta vazia ou frase evasiva conhecida antes de qualquer julgamento de LLM |
| Máximo de 2 tentativas por pergunta (Camada 2) | `nodes.py:avaliar_informatividade` | Impede que o agente fique preso pedindo a mesma pergunta indefinidamente após uma resposta considerada não informativa |
| Cadeia de fallback de LLM com limite | `config.py:get_llm()` | Se todos os provedores configurados falharem, a exceção vira `FalhaLLMError`, e a API responde HTTP 503 em vez de travar |

`tests/test_seguranca_prompt_injection.py` demonstra três desses
guardrails sob um cenário adversarial concreto: uma resposta do operador
que tenta instruir o agente a revelar uma chave de API e pular etapas da
investigação. O teste confirma que o roteamento não muda, que nenhum
segredo aparece no `Diagnostico` final, e que o `batch_id` da tool
continua restrito ao lote da investigação.

## Guardrails novos (Fase 2)

Os quatro guardrails abaixo foram adicionados nesta fase, motivados pela
mesma pergunta central de governança do PDF (§4.5): em que situação faz
sentido limitar a interação do operador com o agente. Nos dois casos, a
resposta é a mesma: quando a ausência do limite permite manter a
investigação presa ou o contexto do LLM inflado sem nenhum ganho legítimo
de informação, mesmo sem existir uma intenção maliciosa comprovável por
trás disso.

### Limite de tentativas na Camada 1 (`MAX_TENTATIVAS_CAMADA_1`)

**Problema.** A Camada 1 de validação (`validar_resposta_operador`)
rejeita resposta vazia, longa demais ou evasiva e pede a mesma pergunta de
novo, sem nenhum limite de tentativas. Como cada rejeição nessa camada não
chama o LLM, o custo direto de uma tentativa rejeitada é baixo, mas nada
impedia um operador, ou um cliente automatizado enviando requisições
programaticamente, de manter uma investigação presa na mesma pergunta
indefinidamente, sem nunca progredir.

**Guardrail.** `nodes.py:MAX_TENTATIVAS_CAMADA_1` (valor 5). A função
`perguntar_operador` conta as tentativas rejeitadas pela Camada 1 para a
pergunta atual; ao atingir o limite, levanta
`LimiteTentativasExcedidoError` em vez de pedir de novo. O endpoint
`POST /api/investigacoes/{thread_id}/responder` (`backend/main.py`)
captura essa exceção e responde HTTP 429, no mesmo padrão já usado para
`FalhaLLMError` (HTTP 503).

**Onde esse limite deveria caber.** Especificamente na Camada 1, porque é
o único ponto do fluxo em que uma resposta pode ser rejeitada
repetidamente sem nunca envolver julgamento do LLM (a Camada 2 já tem seu
próprio limite de 2 tentativas). Não caberia um limite geral de
tentativas somando as duas camadas, porque teriam significados diferentes:
uma resposta rejeitada na Camada 1 nunca chegou a ser avaliada quanto ao
conteúdo, uma resposta rejeitada na Camada 2 já foi julgada e considerada
não informativa.

### Limite de tamanho da resposta (`TAMANHO_MAXIMO_RESPOSTA`)

**Problema.** Nenhuma validação impedia uma resposta de texto livre
arbitrariamente longa. Isso é ao mesmo tempo um vetor de custo (mais
tokens no contexto enviado ao LLM a cada chamada subsequente) e uma
superfície de abuso, já que uma resposta legítima a uma pergunta de
contexto do Ishikawa ou de aprofundamento dos 5 Porquês não precisa de
mais do que alguns parágrafos.

**Guardrail.** `tools.py:TAMANHO_MAXIMO_RESPOSTA` (valor 2000 caracteres).
`validar_resposta_operador` passa a rejeitar qualquer resposta acima
desse limite, na mesma Camada 1 que já rejeita resposta vazia ou evasiva.
`perguntar_operador` diferencia a mensagem de erro mostrada ao operador
conforme o motivo da rejeição (resposta longa demais, ou tipo de resposta
não aceito), para que o retorno visual não seja o mesmo dos dois casos.

**Onde esse limite deveria caber.** Na Camada 1, junto da validação de
vazio/evasivo, porque também não exige julgamento de modelo, decidir se
uma string ultrapassa um número de caracteres é uma checagem puramente
determinística.

### CORS restrito e limite de taxa por IP

**Problema.** A API (`backend/main.py`) respondia com `allow_origins=["*"]`
fixo e sem nenhum limite de requisições por cliente. Qualquer origem podia
chamar a API, e nada impedia um número arbitrário de requisições por
segundo vindas do mesmo IP.

**Guardrail.** `backend/main.py:_origens_cors()` lê `CORS_ALLOWED_ORIGINS`
(env var, lista separada por vírgula; `*` continua sendo o padrão em
desenvolvimento local). `backend/main.py:limitar_taxa` é uma dependency
do FastAPI aplicada a toda a API, contando requisições por IP numa janela
deslizante de `JANELA_LIMITE_TAXA_SEGUNDOS` (60) segundos; ao atingir
`LIMITE_REQUISICOES_POR_JANELA` (20), a próxima requisição do mesmo IP
recebe HTTP 429. O contador é mantido em memória por processo, sem
dependência nova nem infraestrutura externa. Sem efeito quando
`LLM_PROVIDER=fake`, mesmo
sinal já usado para toda a suíte de testes e E2E, que faz várias
requisições em sequência sem intenção de abuso.

**Onde esse limite deveria caber.** Na camada de transporte da API, não no
grafo do agente: CORS e limite de taxa protegem o serviço como um todo
contra abuso de rede, independente de qual investigação está em
andamento, diferente dos dois guardrails anteriores, que protegem uma
investigação específica contra uma resposta de operador mal-intencionada
ou mal formada.

### Chave de API interna (`INTERNAL_API_KEY`)

**Problema.** Nenhuma rota da API exige identificação de quem chama. Em
produção, com o backend num domínio público, qualquer cliente com a URL
consegue listar lotes, iniciar e responder investigações, ou ler o
resumo diário agregado, sem nenhuma credencial.

**Guardrail.** `backend/main.py:exigir_api_key`, uma dependency aplicada
às rotas de lotes, investigações e resumo diário, exige o cabeçalho
`X-API-Key` igual ao valor de `INTERNAL_API_KEY` (env var); sem essa
variável definida, nenhuma chave é exigida, o comportamento de
desenvolvimento local. `relatorio.pdf` e `/reports` ficam de fora dessa
exigência, o link do relatório em PDF precisa continuar clicável direto
do e-mail do workflow n8n, sem cabeçalho customizado.

**Onde esse limite deveria caber.** Também na camada de transporte,
junto do CORS e do limite de taxa, mas resolvendo um problema diferente
dos dois: CORS e limite de taxa não identificam quem faz a chamada, só
de onde ou com que frequência; a chave de API é o único guardrail dos
quatro que efetivamente autentica o cliente.

## Quando novos limites fariam sentido

A pergunta geral, "em que situação cabe limitar a interação do usuário
com o agente", tem uma resposta consistente nos quatro casos analisados
nesta fase: um limite novo se justifica quando a ausência dele permite que
a interação consuma recurso (tempo de investigação, tokens de contexto,
capacidade de um serviço público) sem produzir nenhum avanço real na
investigação, e não quando o objetivo é restringir o conteúdo que o
operador pode responder. Os guardrails do Root-Spector limitam **volume e
persistência** de interação (quantas tentativas, quanto texto, quantas
requisições por minuto), nunca o conteúdo em si, porque o próprio
roteamento determinístico do grafo já torna irrelevante, do ponto de vista
de segurança, o que o texto da resposta diz.
