# Code review de IA sobre um PR real

Este documento cumpre o §4.7 do PDF: uso de IA para analisar um diff ou PR
real e identificar problemas ou melhorias, mais a seleção e justificativa
de um teste priorizado por risco. O PR revisado é o #63,
`feat(governanca): guardrails de segurança e teste de prompt injection`,
já mergeado em `develop`. O diff completo tem 907 linhas e toca sete
arquivos: `backend/main.py`, `root_cause_agent/nodes.py`,
`root_cause_agent/tools.py`, `docs/GOVERNANCA.md` (novo),
`tests/test_seguranca_prompt_injection.py` (novo), `tests/test_backend.py`
e `tests/test_tools.py`.

## Escopo do PR revisado

O PR implementa três guardrails de governança para a Fase 2 do
Root-Spector:

- `MAX_TENTATIVAS_CAMADA_1` (`nodes.py`), limite de respostas rejeitadas
  pela Camada 1 de validação para uma mesma pergunta. Ao exceder, o nó
  levanta `LimiteTentativasExcedidoError`, e a API responde HTTP 429.
- `TAMANHO_MAXIMO_RESPOSTA` (`tools.py`), limite de 2000 caracteres na
  resposta do operador, rejeitado na mesma Camada 1.
- `CORS_ALLOWED_ORIGINS` e `limitar_taxa` (`backend/main.py`), restrição
  de CORS por variável de ambiente e limite de 20 requisições por minuto
  por IP, aplicado a toda a API.

## Achados

### 1. Contagem de requisições por IP nunca é liberada

`backend/main.py`, função `limitar_taxa`. O contador
`_requisicoes_por_ip` é um `defaultdict(deque)` que cria uma entrada nova
para cada IP visto pela primeira vez. O código já remove, a cada
chamada, os registros de tempo mais antigos que
`JANELA_LIMITE_TAXA_SEGUNDOS`, mas nunca remove a própria entrada do
dicionário quando a fila correspondente fica vazia. Em um processo de
longa duração, o número de entradas cresce com o número de IPs distintos
já vistos, não com o tráfego atual, e nunca diminui. Não é um problema
grave no escopo local deste projeto, mas é um vazamento de memória real
em um deploy contínuo com tráfego variado, especialmente diante de IPs
que mudam com frequência atrás de uma rede móvel ou de um provedor de
nuvem. Uma limpeza simples, removendo a entrada do dicionário quando a
fila fica vazia após o corte da janela, resolveria sem custo adicional
relevante.

### 2. `limitar_taxa` confia em `request.client.host` sem considerar proxy reverso

`backend/main.py`, mesma função. O plano de deploy do projeto usa Render
para o backend, que normalmente coloca a aplicação atrás de um proxy
reverso. Nesse cenário, `request.client.host` tende a devolver o IP do
proxy, não o IP real do cliente, então o limite por IP passaria a
funcionar, na prática, como um limite único compartilhado por todos os
usuários simultâneos, não um limite por usuário. A correção usual é ler
o cabeçalho `X-Forwarded-For` quando presente, com cuidado para não
confiar cegamente nele fora de um ambiente onde o proxy é conhecido e
controlado. Como o guardrail já existe e está testado, esse ajuste pode
esperar o momento do deploy real, mas vale registrar agora para não ser
esquecido.

### 3. O guardrail de limite de taxa está testado como função isolada, não como parte da aplicação

`tests/test_backend.py`, `test_limitar_taxa_bloqueia_apos_o_limite` e
`test_limitar_taxa_sem_efeito_com_llm_fake`. Os dois testes chamam
`backend_main.limitar_taxa(_FakeRequest())` diretamente, sem passar pela
fixture `client` (`TestClient`), então nunca exercitam a aplicação real
com o `Depends(limitar_taxa)` de fato instalado na rota. Além disso, a
fixture `client` sempre roda com `LLM_PROVIDER=fake` (dependência de
`fake_llm`), e o guardrail é desativado exatamente nesse caso, então
nenhum teste do projeto confirma, de ponta a ponta, que uma sequência de
requisições HTTP reais contra a aplicação de fato recebe HTTP 429 a
partir da vigésima primeira. Um bug de wiring, por exemplo a remoção
acidental de `dependencies=[Depends(limitar_taxa)]` na criação do
`FastAPI`, não seria pego por nenhum teste existente. Recomendo um teste
de integração adicional, com uma instância de `TestClient` separada e
`LLM_PROVIDER` desativado, fazendo requisições reais contra uma rota
simples até confirmar o HTTP 429.

### Nenhum achado crítico de segurança

Os três guardrails cumprem o que se propõem a fazer. A validação de
tamanho de resposta e o limite de tentativas da Camada 1 continuam
puramente determinísticos, sem chamada de LLM, consistente com o
restante da arquitetura do projeto. `CORS_ALLOWED_ORIGINS` tem um
default seguro para desenvolvimento e permite restrição explícita em
produção. Não encontrei nenhuma forma de contornar os limites nem
nenhum vazamento de segredo introduzido por este PR.

## Teste priorizado por risco

O teste priorizado por risco desta fase é
`tests/test_seguranca_prompt_injection.py`, que cobre o cenário
adversarial em que a resposta do operador tenta instruir o agente a
revelar uma chave de API e pular etapas da investigação.

A justificativa da prioridade é direta: entre todos os riscos possíveis
no projeto, o de segurança é o único capaz de comprometer a aplicação
inteira de uma só vez, seja por vazamento de credencial, seja por perda
de controle do fluxo da investigação para uma entrada não confiável. Um
teste de causa raiz incorreta produz um relatório errado, um problema
sério, mas contido a uma investigação. Um teste de governança falho,
como um vazamento de chave de API, comprometeria toda a conta do
provedor de LLM e potencialmente outros serviços que compartilham a
mesma credencial. Por isso este teste é o candidato natural a teste
priorizado por risco, e não qualquer um dos testes de fluxo funcional já
existentes na suíte.

O teste confirma, de forma automatizada, que o roteamento entre nós não
muda diante da instrução maliciosa, que nenhum segredo aparece em
nenhum campo do `Diagnostico` final, que a resposta maliciosa é tratada
como qualquer outra resposta do operador, sem ramo especial de detecção,
e que o `batch_id` usado pela tool de biosensor continua restrito ao
lote da investigação em andamento.
