# Análise de incidente de CI, log de pipeline, anomalia e tendência

Este documento cumpre o §4.8 do PDF: explicação de log de pelo menos duas
etapas do pipeline, detecção e explicação de uma anomalia real, e uma
estimativa simples de tendência ou risco de falha. Todos os dados abaixo
vêm do histórico real de execuções do GitHub Actions deste repositório
(`gh api repos/.../actions/runs`), sem nenhum cenário simulado.

## Explicação de log de duas etapas do pipeline

A execução 31977400491 (16 de agosto de 2026, branch `develop`) falhou em
duas etapas do workflow `ci.yml`, `Lint (ruff)` e `E2E (Playwright)`, com
as outras duas etapas, testes do agente e testes do frontend, passando
normalmente.

**Etapa Lint (ruff).** O log mostra 36 erros do tipo `E501`, linha longa
demais, todos em `scripts/setup_github.py`, um script de automação do
GitHub fora do pacote principal do projeto. Um trecho representativo do
log:

```
E501 Line too long (102 > 100)
   --> scripts/setup_github.py:770:101
    |
768 |         ensure_branches()
769 |     else:
770 |         print("\n== Branches ==\n  pulando (rode com --branches pra criar develop + branches vazias)")
    |
Found 36 errors.
##[error]Process completed with exit code 1.
```

O `ruff check` estava configurado para varrer o repositório inteiro,
incluindo um script que nunca tinha passado por lint antes, então os 36
erros já existiam no arquivo havia tempo e só ficaram visíveis quando o
job de lint rodou sobre ele pela primeira vez nessa execução.

**Etapa E2E (Playwright).** O log mostra uma falha diferente, anterior a
qualquer teste rodar de fato:

```
Error: Failed to launch: Error: spawn /bin/sh ENOENT
##[error]Process completed with exit code 1.
```

Essa mensagem indica que o Playwright não conseguiu nem iniciar o
processo do `webServer` configurado (o backend `uvicorn`), muito antes de
qualquer teste de interface começar.

## Anomalia detectada e explicada

A mensagem `spawn /bin/sh ENOENT` é enganosa: parece um problema de
shell ausente no runner, mas a causa raiz era outra. `tests/e2e/playwright.config.ts` define o `webServer` do backend com um
`cwd` relativo (`cwd: '..'`), calculado a partir da pasta onde o próprio
arquivo de configuração vive, `tests/e2e/`. Para chegar na raiz do
repositório a partir dali são necessários dois níveis acima, não um. O
valor `'..'` resolvia para `tests/`, uma pasta que existe, mas é a
errada, e o `webServer` seguinte, do frontend, usava `cwd: '../frontend'`,
que resolvia para `tests/frontend/`, uma pasta que não existe. O Node.js
reporta um `cwd` inexistente com a mesma mensagem genérica de spawn
falho, em vez de um erro claro de "diretório não encontrado", e foi essa
mensagem enganosa que mascarou o problema real durante a primeira
tentativa de correção.

A correção aconteceu em dois commits. O primeiro,
`de2d248` (`fix(ci): corrige spawn ENOENT no webServer do Playwright`),
tratou um sintoma real, mas secundário, o objeto `env` do `webServer` não
espalhava `process.env` antes de definir as variáveis próprias, o que
podia derrubar `PATH` e outras variáveis herdadas em alguns ambientes. O
erro persistiu de forma idêntica depois desse commit, o que apontou para
a causa raiz verdadeira. O segundo commit, `6ceed83`
(`fix(ci): corrige cwd errado no webServer do Playwright, causa raiz
real`), corrigiu os caminhos relativos para `'../..'` e
`'../../frontend'`, resolvendo o problema de fato.

## Estimativa de tendência

Contando todas as execuções do workflow `ci.yml` registradas no
repositório, dividido em três períodos:

| Período | Execuções | Falhas | Taxa de falha |
|---|---|---|---|
| 19 e 20 de julho de 2026 | 37 | 37 | 100% |
| 16 de agosto de 2026, antes da correção real | 2 | 2 | 100% |
| 16 de agosto de 2026 em diante, após o commit `6ceed83` | 20 | 0 | 0% |

O primeiro período, 37 execuções seguidas com `startup_failure`, é um
incidente diferente do analisado acima: todas essas execuções falhavam
antes de qualquer job do `ci.yml` sequer começar a rodar, um sinal de
configuração ou permissão do Actions na conta, não um problema do
próprio workflow, já que o YAML validava normalmente. A configuração
atual de Actions do repositório (`gh api
repos/.../actions/permissions`) está habilitada e sem restrição, então o
incidente não se repete mais, mas a mudança exata que resolveu esse
primeiro incidente não deixou rastro no histórico de commits, por ser
uma configuração de conta ou de repositório, não código versionado.

O segundo e o terceiro período mostram o efeito direto da correção
analisada nesta seção: falha em 100% das execuções antes do commit
`6ceed83`, seguida de sucesso em 100% das 20 execuções posteriores até a
data deste documento. A tendência, olhando os dois incidentes juntos, é
de estabilização, o pipeline vem de duas causas raiz distintas de falha
total, ambas já identificadas e corrigidas, sem nenhuma falha desde
então.
