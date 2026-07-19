# Cenários de uso — Root-Spector

Cenários passo a passo do ponto de vista do operador, cobrindo o fluxo
principal e os desvios previstos pelos requisitos funcionais
(`specs/requirements.md`). Rotas HTTP citadas em `docs/openapi.yaml`;
diagrama do grafo em `docs/diagrama-fluxo.md`. UC1 usa o lote 11 do dataset
de demonstração atual como exemplo concreto — roteiro completo de
respostas em `docs/demo/gabarito-testes.md`.

---

## UC1 — Investigação completa de um lote elegível (fluxo principal)

**Ator:** Operador de processo/qualidade.
**Pré-condições:** `data/biotecpredict.db` presente; ao menos um lote com
`status='COMPLETED'`, `compliance_score` não nulo e classificação
`WARNING`/`CRITICAL`; ao menos um provedor de LLM configurado e acessível.
**Requisitos relacionados:** RF1–RF10, RF12.

1. O operador abre a aplicação (`GET /api/lotes`) e vê a lista de lotes,
   já classificada por risco, com os elegíveis destacados.
2. Escolhe o lote 11 — `WARNING` / `MEDIUM_RISK` / compliance_score 71.32
   — que tem `dissolved_oxygen` e `agitator_speed` fora da faixa aceitável
   (par correlacionado: menos agitação, menos transferência de oxigênio).
3. O sistema (`POST /api/investigacoes/11/iniciar`) roda `preparar_contexto`
   e apresenta a 1ª pergunta de contexto (categoria Máquina).
4. O operador responde às 6 perguntas de Ishikawa (Método, Máquina,
   Material, Mão de obra, Meio ambiente, Medição), uma por vez, cada uma
   via `POST /api/investigacoes/11/responder` — o histórico de parâmetros
   do lote permanece visível na tela durante todo o processo.
5. Após a 6ª resposta, o sistema identifica a `categoria_principal`
   (Máquina — setpoint do inversor de frequência do agitador abaixo do
   padrão) e as categorias descartadas, com justificativa/motivo.
6. O operador responde às 5 perguntas "por quê", cada uma ancorada na
   resposta anterior, aprofundando a partir da categoria Máquina.
7. Após a 5ª resposta, o sistema sintetiza a causa raiz, gera
   `reports/11_{timestamp}.json` e `.html`, e devolve
   `{status: "pronto_para_revisao"}`.
8. O operador consulta `GET /api/investigacoes/11/revisao` e vê a cadeia
   completa (6 respostas Ishikawa + 5 porquês), a causa raiz sintetizada
   e os links do relatório.
9. O operador considera a investigação satisfatória e encerra — nenhuma
   ação adicional é necessária (o relatório já está salvo em `reports/`).

**Pós-condição:** `Diagnostico` válido persistido em JSON e HTML;
checkpoint do `thread_id` no estado final (`diagnostico` preenchido).

---

## UC2 — Resposta vazia ou evasiva (validação Camada 1)

**Ator:** Operador.
**Pré-condições:** investigação em andamento, pergunta atual pendente.
**Requisito relacionado:** RF13(a).

1. O operador envia uma resposta vazia, só espaço, ou uma frase evasiva
   conhecida (ex.: "não sei") via `POST /api/investigacoes/{thread_id}/responder`.
2. `validar_resposta_operador` (determinística, `tools.py`) rejeita a
   resposta antes de qualquer envolvimento do LLM.
3. O sistema devolve a **mesma pergunta**, com
   `erro: "Este tipo de resposta não é aceito."` — a investigação não
   avança e a tentativa **não é contada** (tentativas ilimitadas nesta
   camada).
4. O operador reformula e reenvia — volta ao fluxo principal (UC1, passo
   4 ou 6, conforme a fase).

**Pós-condição:** nenhum estado novo persistido; a mesma pergunta
continua ativa.

---

## UC3 — Resposta não informativa (validação Camada 2, agêntica)

**Ator:** Operador.
**Pré-condições:** resposta passou pela Camada 1 (UC2), pergunta atual
pendente.
**Requisito relacionado:** RF13(b).

1. O operador responde algo não vazio/evasivo, mas que não informa de
   fato a pergunta feita (ex.: fora do assunto, vago, contraditório).
2. `avaliar_informatividade` (nó LLM) julga a resposta como não
   informativa.
3. **Se for a 1ª tentativa:** o sistema pede a mesma pergunta de novo
   (mais uma chance, sem sinalizar erro explícito de conteúdo — apenas
   repete a pergunta), contando como 1 tentativa registrada.
4. **Se for a 2ª tentativa** (ainda não informativa): o sistema registra
   as duas tentativas, sinaliza a não-informatividade no diagnóstico, e
   avança para a próxima pergunta mesmo assim — sem travar a investigação
   indefinidamente.

**Pós-condição:** a `RespostaIshikawa`/`PorQue` correspondente é
persistida com `tentativas` (lista com até 2 itens) e
`informativa: false`.

---

## UC4 — Pedido de ajuste (reabre um novo ciclo)

**Ator:** Operador.
**Pré-condições:** investigação concluída (UC1, passo 8) — diagnóstico já
disponível para revisão.
**Requisito relacionado:** RF9.

1. Na tela de revisão, o operador considera a causa raiz insuficiente ou
   quer refazer a investigação e escolhe "pedir ajuste".
2. `POST /api/investigacoes/{thread_id}/ajustar` arquiva o diagnóstico
   atual como um `CicloAnterior` (preservado para auditoria, nunca
   sobrescrito) e reinicia o grafo para o mesmo `batch_id`.
3. O sistema devolve a 1ª pergunta de um novo ciclo Ishikawa — mesmo
   formato de resposta de `iniciar` (UC1, passo 3).
4. O operador conduz o novo ciclo do zero (UC1, passos 4–8).
5. Ao concluir, o relatório do novo ciclo lista `ciclos_anteriores` com
   pelo menos 1 entrada (o ciclo arquivado no passo 2).

**Pós-condição:** dois (ou mais) ciclos completos associados ao mesmo
lote, todos auditáveis via `ciclos_anteriores`.

---

## UC5 — Falha de todos os provedores de LLM configurados

**Ator:** Operador; sistema (fallback de LLM).
**Pré-condições:** investigação em andamento (`iniciar`, `responder` ou
`ajustar` em curso).
**Requisito relacionado:** RNF6.

1. O operador aciona qualquer ação que exija um nó agêntico (iniciar,
   responder, ajustar).
2. `get_llm()` tenta a cadeia completa — Gemini → Groq → Anthropic →
   OpenAI (cada camada só ativa se a respectiva chave estiver
   configurada) — e todas falham (rede, rate limit, chave inválida).
3. O nó agêntico relança `FalhaLLMError`; a API captura e devolve
   `HTTP 503` com `"Serviço de IA indisponível, recarregue a página."`,
   sem deixar a exceção crua vazar para o frontend.
4. Como o checkpointer só grava um novo checkpoint após um nó terminar
   com sucesso, o `thread_id` permanece pausado no último ponto
   bem-sucedido — nenhum progresso é perdido.
5. O operador recarrega a página mais tarde (quando o serviço de LLM
   estiver disponível de novo) e retoma exatamente de onde parou, sem
   repetir perguntas já respondidas.

**Pós-condição:** nenhuma mudança de estado persistida além do que já
existia antes da tentativa que falhou.

---

## UC6 — Lote sem `compliance_score` classificado

**Ator:** Operador; sistema.
**Pré-condições:** existe pelo menos um lote com `status='COMPLETED'` mas
`compliance_score IS NULL` (estado real observado na exportação do
BiotecPredict — processado, mas ainda sem score atribuído).
**Requisito relacionado:** entrada, `specs/requirements.md`.

1. O operador abre a lista de lotes (`GET /api/lotes`).
2. O sistema consulta `batches` filtrando `status='COMPLETED' AND
   compliance_score IS NOT NULL` — o lote sem score **não aparece** na
   lista, silenciosamente (não é tratado como erro).
3. Se **nenhum** lote da base atender ao filtro, `GET /api/lotes` devolve
   uma lista vazia e a tabela (`ListaLotes.tsx`) renderiza só o cabeçalho,
   sem linhas — não há uma mensagem explícita de "nenhum lote disponível"
   implementada nesta entrega. Se houver lotes mas nenhum `elegivel: true`,
   cada um aparece na tabela com "não elegível" no lugar do botão
   "Investigar".

**Pós-condição:** nenhuma investigação é iniciada; nenhum erro é exposto
ao operador por causa de dados incompletos.
