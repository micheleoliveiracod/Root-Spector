# Construção do workflow no n8n

Este documento contém apenas as instruções de construção do workflow no
n8n, passo a passo, para quem está aprendendo a plataforma pela primeira
vez. Informações sobre o que a automação faz, os dados que ela expõe e as
decisões de escopo estão em `specs/fase02/design.md`, seção Low-code, e
no README principal do projeto, não neste documento.

## Antes de começar

É necessário ter uma conta no n8n Cloud, criada gratuitamente em
https://n8n.io, com qualquer e-mail. Essa conta administra o workflow na
nuvem deles, sem depender de nenhuma máquina local ligada.

O nó de requisição HTTP (passo 3) precisa do domínio público do backend
do Root-Spector, já publicado (`specs/deploy-producao/plano.md`), para o
n8n Cloud conseguir chamá-lo.

## Passo 1, criar um workflow novo

Na tela inicial do n8n, clicar em "Add workflow" (ou no símbolo de "+").
Um canvas em branco é aberto, pronto para receber os nós.

## Passo 2, nó de gatilho (Schedule Trigger)

1. Clicar no símbolo de "+" no canvas para adicionar o primeiro nó.
2. Buscar por "Schedule Trigger" e selecioná-lo.
3. Em "Trigger Rules", escolher o tipo "Days" (dias).
4. Definir o horário de disparo, por exemplo 7 da manhã. Esse é o
   horário em que o workflow vai rodar automaticamente, uma vez por dia.

## Passo 3, nó de requisição HTTP (HTTP Request)

1. Clicar no símbolo de "+" na saída do nó Schedule Trigger, para
   conectar o próximo nó a ele.
2. Buscar por "HTTP Request" e selecioná-lo.
3. Em "Method", escolher GET.
4. Em "URL", informar o endereço do endpoint do resumo diário, por
   exemplo `https://root-spector.onrender.com/api/relatorios/resumo-diario`,
   o domínio público do backend. Sem nenhum parâmetro adicional na URL,
   o endpoint devolve o resumo do dia anterior automaticamente.
5. Em "Send Headers" (ou "Headers"), adicionar um cabeçalho chamado
   `X-API-Key`, com o mesmo valor de `INTERNAL_API_KEY` configurado no
   backend (`docs/deploy-producao.md`). Sem esse cabeçalho, a rota
   responde HTTP 401.

Ao testar esse nó isoladamente (botão "Execute step" ou "Test step"), o
n8n mostra o JSON de resposta do endpoint, com os campos
`total_investigacoes`, `investigacoes` e `eficiencia_operacional`. Vale
conferir esse retorno antes de seguir para os próximos nós, para saber
exatamente quais campos estarão disponíveis nas expressões seguintes.

## Passo 4, nó de condição (IF)

1. Conectar um novo nó à saída do HTTP Request.
2. Buscar por "IF" e selecioná-lo.
3. Adicionar uma condição do tipo número:
   - Campo da esquerda: `{{ $json.total_investigacoes }}`.
   - Operador: "greater than" (maior que).
   - Campo da direita: `0`.

O nó IF passa a ter duas saídas, "true" (verdadeiro, o dia teve
investigações) e "false" (falso, o dia não teve). O restante do
workflow deve ser conectado à saída "true"; a saída "false" fica sem
nenhuma conexão, o que faz o workflow simplesmente parar quando não há
nada para relatar naquele dia.

## Passo 5, nó de formatação (Edit Fields)

1. Conectar um novo nó à saída "true" do nó IF.
2. Buscar por "Edit Fields (Set)" e selecioná-lo.
3. Adicionar os campos que vão compor o e-mail. Para cada campo, usar o
   tipo "String" e uma expressão (clicar no símbolo de expressão, o
   pequeno "fx", ao lado do campo de valor):
   - Campo `assunto`, com uma expressão como
     `Relatório Diário Root-Spector, {{ $json.data }}`.
   - Campo `corpo_investigacoes`, percorrendo a lista de investigações
     com uma expressão JavaScript, por exemplo:
     ```
     {{ $json.investigacoes.map(inv =>
       `Lote ${inv.batch_id}, ${inv.classification}/${inv.risk_prediction}, categoria ${inv.categoria_principal}.
       Causa raiz: ${inv.causa_raiz}.
       Recorrencia: ${inv.recorrencia}.
       Recomendacao: ${inv.recomendacao_tratativa}.
       Relatorio em PDF: ${inv.link_relatorio_pdf}`
     ).join('\n\n') }}
     ```
   - Campo `corpo_eficiencia`, com um resumo da eficiência operacional,
     por exemplo:
     `Tempo medio por investigacao: {{ $json.eficiencia_operacional.tempo_medio_investigacao_s }}s. Respostas com 2 tentativas: {{ $json.eficiencia_operacional.respostas_com_2_tentativas }}. Fallback de LLM acionado: {{ $json.eficiencia_operacional.fallback_llm_acionado }} vez(es).`

Esses três campos ficam disponíveis para o próximo nó como
`$json.assunto`, `$json.corpo_investigacoes` e `$json.corpo_eficiencia`.

## Passo 6, nó de envio de e-mail (Gmail)

1. Conectar um novo nó à saída do nó Edit Fields.
2. Buscar por "Gmail" e selecioná-lo (não "Send Email"/SMTP).
3. Em "Credential to connect with", clicar em "Create new credential" e
   escolher "Gmail OAuth2 API". O n8n abre o fluxo padrão de login do
   Google, pedindo autorização para enviar e-mail pela conta escolhida;
   não exige senha de aplicativo nem servidor SMTP configurado à mão.
   Se a conta não permitir gerar senha de aplicativo (verificação em
   duas etapas desligada, conta Google Workspace com a opção bloqueada,
   ou Advanced Protection Program ativado), esse caminho via OAuth2
   continua funcionando normalmente.
4. Em "Resource", manter "Message"; em "Operation", escolher "Send".
5. Preencher "To" com o endereço de destino.
6. Em "Subject", usar a expressão `{{ $json.assunto }}`.
7. Em "Email Type", escolher "Text" ou "HTML", conforme preferir. Em
   "Message", montar o corpo do e-mail combinando os campos criados no
   passo 5, por exemplo `{{ $json.corpo_investigacoes }}` seguido de
   `{{ $json.corpo_eficiencia }}`.

## Passo 7, testar o workflow completo

Com um dia que já tenha investigações reais concluídas (gravadas na
tabela `relatorios`), clicar
no botão "Execute Workflow", no topo do canvas. O n8n executa cada nó em
sequência, mostrando o resultado de cada um. Confirmar que o e-mail
chegou na caixa de entrada configurada no passo 6.

## Passo 8, ativar o workflow

Depois de confirmar que o teste manual funcionou, salvar o workflow e
ligar o botão "Active", no canto superior direito do canvas. A partir
daí, o workflow roda sozinho, todos os dias, no horário configurado no
Schedule Trigger, sem precisar de nenhuma execução manual.
