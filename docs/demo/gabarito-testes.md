# Gabarito de teste: os 10 lotes elegíveis

Roteiro de respostas prontas pra quem for testar o Root-Spector de ponta a
ponta, sabendo de antemão a causa raiz "oficial" de cada lote (definida em
`data/simulacao_causa_raiz/README.md`, cenários `desvio_01` a `desvio_10`).

A regra de elegibilidade de `GET /api/lotes` (`backend/main.py:listar_lotes`)
passa a considerar `risk_prediction` e `parametros_fora_da_faixa`, não só o
`compliance_score` do BiotecPredict. Antes dessa correção, `desvio_01` e
`desvio_06` eram os únicos dois elegíveis, os outros 8 lotes com desvio
ficavam `ACCEPTABLE` pelo score e não apareciam como investigáveis. Com a
correção, os 10 lotes com desvio aparecem como elegíveis, porque todos têm
`risk_prediction` MEDIUM_RISK ou HIGH_RISK mesmo quando o
`compliance_score` fica ACCEPTABLE. `batch_id` real de cada lote,
confirmado direto em `GET /api/lotes` em produção:

| `batch_id` | Causa raiz simulada | Sensor(es) afetado(s) | Score | Classificação | Risco ML |
|---|---|---|---|---|---|
| 606 | Contaminação microbiana / meio de cultura ruim (`desvio_01`) | temperatura + pH + OD | 48.31 | WARNING | HIGH_RISK |
| 607 | Falha na bomba dosadora de base (`desvio_02`) | pH | 84.13 | ACCEPTABLE | MEDIUM_RISK |
| 608 | Falha na bomba dosadora de ácido (`desvio_03`) | pH | 84.53 | ACCEPTABLE | MEDIUM_RISK |
| 609 | Falha no sistema de aquecimento (`desvio_04`) | temperatura | 84.65 | ACCEPTABLE | MEDIUM_RISK |
| 610 | Deriva de calibração do sensor de temperatura (`desvio_05`) | temperatura | 83.96 | ACCEPTABLE | MEDIUM_RISK |
| 611 | Agitador com RPM muito baixo (`desvio_06`) | agitador + OD | 71.32 | WARNING | MEDIUM_RISK |
| 612 | Erro de configuração do agitador (`desvio_07`) | agitador | 84.36 | ACCEPTABLE | MEDIUM_RISK |
| 613 | Válvula de contrapressão travada (`desvio_08`) | pressão | 84.56 | ACCEPTABLE | MEDIUM_RISK |
| 614 | Vazamento na linha/vedação do reator (`desvio_09`) | pressão | 84.56 | ACCEPTABLE | MEDIUM_RISK |
| 615 | Falha no suprimento de ar (`desvio_10`) | oxigênio dissolvido | 85.04 | ACCEPTABLE | MEDIUM_RISK |

**Como usar:** a pergunta que o agente mostra na tela é gerada pelo LLM a
cada rodada, a redação varia, mas a intenção de cada categoria é sempre a
mesma (ver `config/regras_bioprocesso.yaml` § `categorias_ishikawa`).
Adapte a resposta abaixo ao que aparecer na tela, mantendo a mesma
substância. O resultado final (categoria principal e causa raiz) depende
da síntese do LLM em cima das suas respostas, as respostas abaixo foram
desenhadas pra deixar só uma categoria com sinal real (as outras
respondem "está tudo normal"), então o esperado é convergir no cenário
descrito, mas a redação exata da causa raiz gerada pode variar.

Em alguns casos a Camada 2 (`avaliar_informatividade`, julgamento
agêntico) pode julgar a 1ª tentativa de uma resposta pouco específica e
pedir a mesma pergunta de novo, mostrando o aviso explicando o motivo
(ver `nodes.py::avaliar_informatividade`) -- nesse caso, reenvie a mesma
resposta com um pouco mais de detalhe técnico, mantendo a mesma
substância.

---

## Lote 606: Contaminação do meio de cultura

**Ficha do lote:** `WARNING` / `HIGH_RISK` / compliance_score 48.31 ,
parâmetros fora da faixa: temperatura, pH, oxigênio dissolvido (os três
juntos, mesma causa física).

**Causa raiz "oficial" do dataset:** contaminação microbiana / meio de
cultura ruim.

### Fase 1: Mapeamento Ishikawa

| Categoria | Resposta sugerida |
|---|---|
| **Método** | Não houve mudança de procedimento ou receita neste lote, seguimos o protocolo padrão normalmente. |
| **Máquina** | Não houve intervenção nos equipamentos; a manutenção preventiva está em dia. |
| **Material** | Sim, o meio de cultura usado neste lote veio de um novo lote de insumo, e o ciclo de esterilização (autoclave) foi interrompido antes de completar o tempo padrão. A amostra apresentou leve turvação incomum antes da inoculação. |
| **Mão de obra** | Não houve troca de equipe nem pendência de treinamento; a equipe é experiente. |
| **Meio ambiente** | Não houve condição ambiental atípica, sala dentro dos parâmetros esperados. |
| **Medição** | Sensores de temperatura, pH e oxigênio dissolvido calibrados, sem histórico de desvio. |

**Categoria principal esperada:** Material (meio de cultura mal
esterilizado). As outras 5 são descartadas porque cada resposta acima já
nega qualquer sinal de problema.

### Fase 2: 5 Porquês (ancorados em Material)

| # | Por quê | Resposta sugerida |
|---|---|---|
| 1 | Por que o meio de cultura estava contaminado? | Porque o ciclo de esterilização (autoclave) daquele lote de meio foi interrompido antes de completar o tempo padrão. |
| 2 | Por que o ciclo foi interrompido antes do tempo? | Porque houve uma queda de energia breve durante o ciclo de autoclave. |
| 3 | Por que o meio foi liberado mesmo com o ciclo interrompido? | Porque o operador não percebeu a interrupção e liberou o meio para uso mesmo assim. |
| 4 | Por que o operador liberou o meio sem confirmar o ciclo completo? | Porque não existe uma checagem obrigatória de conclusão do ciclo antes de liberar o meio para uso. |
| 5 | Por que não existe essa checagem obrigatória? | Porque o procedimento operacional padrão não prevê uma verificação e registro formal de conclusão do ciclo de autoclave antes da liberação do meio. |

**Causa raiz esperada:** ausência de uma verificação formal de conclusão
do ciclo de esterilização do meio de cultura antes da liberação para uso,
permitiu que um meio parcialmente esterilizado (após interrupção por
queda de energia) fosse utilizado, causando contaminação microbiana que
elevou a temperatura e reduziu o pH e o oxigênio dissolvido do lote.

**Confirmado em produção:** relatório real gerado, `GET /api/relatorios/1`.

---

## Lote 607: Falha na bomba dosadora de base

**Ficha do lote:** `ACCEPTABLE` / `MEDIUM_RISK` / compliance_score 84.13,
parâmetro fora da faixa: pH.

**Causa raiz "oficial" do dataset:** falha na bomba dosadora de base.

### Fase 1: Mapeamento Ishikawa

| Categoria | Resposta sugerida |
|---|---|
| **Método** | Não houve mudança de procedimento ou receita neste lote, seguimos o protocolo padrão normalmente. |
| **Máquina** | Sim, a bomba dosadora de base (usada para corrigir o pH) apresentou uma falha intermitente durante este lote, com vazão irregular de dosagem; a manutenção preventiva dessa bomba especificamente estava atrasada. |
| **Material** | Materiais e insumos habituais, mesmo fornecedor e mesmo lote de sempre, sem alteração de aspecto visível na inspeção de recebimento. |
| **Mão de obra** | Não houve troca de equipe nem pendência de treinamento; a equipe é experiente e seguiu o procedimento operacional padrão normalmente. |
| **Meio ambiente** | Não houve condição ambiental atípica, sala dentro dos parâmetros esperados. |
| **Medição** | O sensor de pH está calibrado, sem histórico de desvio; a leitura reflete o pH real do lote, não erro de medição. |

**Categoria principal esperada:** Máquina (bomba dosadora de base com
falha de vazão). As outras 5 são descartadas porque cada resposta acima
já nega qualquer sinal de problema.

### Fase 2: 5 Porquês (ancorados em Máquina)

| # | Por quê | Resposta sugerida |
|---|---|---|
| 1 | Por que a bomba dosadora de base falhou? | Porque o diafragma da bomba estava desgastado e não fazia a dosagem correta de base. |
| 2 | Por que o diafragma estava desgastado? | Porque já tinha ultrapassado a vida útil recomendada pelo fabricante sem ser trocado. |
| 3 | Por que o diafragma não foi trocado a tempo? | Porque não existe um plano de troca preventiva de peças de desgaste para essa bomba. |
| 4 | Por que não existe esse plano de troca preventiva? | Porque a manutenção desse equipamento é feita reativamente, só quando ocorre falha. |
| 5 | Por que a manutenção é reativa e não preventiva? | Porque não há um cronograma formal de manutenção preditiva/preventiva para bombas dosadoras no plano de manutenção da planta. |

**Causa raiz esperada:** ausência de um cronograma formal de manutenção
preventiva/preditiva para bombas dosadoras, permitiu que o diafragma da
bomba de base operasse além da vida útil recomendada sem ser trocado,
causando dosagem irregular de base e reduzindo o pH do lote fora da
faixa aceitável.

---

## Lote 608: Falha na bomba dosadora de ácido

**Ficha do lote:** `ACCEPTABLE` / `MEDIUM_RISK` / compliance_score 84.53,
parâmetro fora da faixa: pH.

**Causa raiz "oficial" do dataset:** falha na bomba dosadora de ácido.

### Fase 1: Mapeamento Ishikawa

| Categoria | Resposta sugerida |
|---|---|
| **Método** | Não houve mudança de procedimento ou receita neste lote, seguimos o protocolo padrão normalmente. |
| **Máquina** | Sim, a bomba dosadora de ácido (usada para corrigir o pH) apresentou uma falha de vazão durante este lote, dosando ácido de forma irregular; a manutenção preventiva dessa bomba estava atrasada. |
| **Material** | Materiais e insumos habituais, mesmo fornecedor e mesmo lote de sempre, sem alteração de aspecto visível na inspeção de recebimento. |
| **Mão de obra** | Não houve troca de equipe nem pendência de treinamento; a equipe é experiente e seguiu o procedimento operacional padrão normalmente. |
| **Meio ambiente** | Não houve condição ambiental atípica, sala dentro dos parâmetros esperados. |
| **Medição** | O sensor de pH está calibrado, sem histórico de desvio; a leitura reflete o pH real do lote, não erro de medição. |

**Categoria principal esperada:** Máquina (bomba dosadora de ácido com
falha de vazão). As outras 5 são descartadas porque cada resposta acima
já nega qualquer sinal de problema.

### Fase 2: 5 Porquês (ancorados em Máquina)

| # | Por quê | Resposta sugerida |
|---|---|---|
| 1 | Por que a bomba dosadora de ácido falhou? | Porque a válvula de retenção da bomba estava com desgaste e permitia refluxo, dosando ácido de forma irregular. |
| 2 | Por que a válvula de retenção estava desgastada? | Porque já tinha ultrapassado a vida útil recomendada pelo fabricante sem ser trocada. |
| 3 | Por que a válvula não foi trocada a tempo? | Porque não existe um plano de troca preventiva de peças de desgaste para essa bomba. |
| 4 | Por que não existe esse plano de troca preventiva? | Porque a manutenção desse equipamento é feita reativamente, só quando ocorre falha. |
| 5 | Por que a manutenção é reativa e não preventiva? | Porque não há um cronograma formal de manutenção preditiva/preventiva para bombas dosadoras no plano de manutenção da planta. |

**Causa raiz esperada:** ausência de um cronograma formal de manutenção
preventiva/preditiva para bombas dosadoras, permitiu que a válvula de
retenção da bomba de ácido operasse desgastada sem ser trocada, causando
dosagem irregular de ácido e elevando o pH do lote fora da faixa
aceitável.

---

## Lote 609: Falha no sistema de aquecimento

**Ficha do lote:** `ACCEPTABLE` / `MEDIUM_RISK` / compliance_score 84.65,
parâmetro fora da faixa: temperatura.

**Causa raiz "oficial" do dataset:** falha no sistema de aquecimento.

### Fase 1: Mapeamento Ishikawa

| Categoria | Resposta sugerida |
|---|---|
| **Método** | Não houve mudança de procedimento ou receita neste lote, seguimos o protocolo padrão normalmente. |
| **Máquina** | Sim, o sistema de aquecimento do biorreator (resistência/serpentina de aquecimento) apresentou uma falha intermitente durante este lote, com oscilação da temperatura acima do esperado; a manutenção preventiva desse sistema estava atrasada. |
| **Material** | Materiais e insumos habituais, mesmo fornecedor e mesmo lote de sempre, sem alteração de aspecto visível na inspeção de recebimento. |
| **Mão de obra** | Não houve troca de equipe nem pendência de treinamento; a equipe é experiente e seguiu o procedimento operacional padrão normalmente. |
| **Meio ambiente** | Não houve condição ambiental atípica, sala dentro dos parâmetros esperados. |
| **Medição** | O sensor de temperatura está calibrado, sem histórico de desvio; a leitura reflete a temperatura real do lote, não erro de medição. |

**Categoria principal esperada:** Máquina (sistema de aquecimento com
falha intermitente). As outras 5 são descartadas porque cada resposta
acima já nega qualquer sinal de problema.

### Fase 2: 5 Porquês (ancorados em Máquina)

| # | Por quê | Resposta sugerida |
|---|---|---|
| 1 | Por que o sistema de aquecimento falhou? | Porque o controlador de temperatura (termostato/PID) da resistência de aquecimento apresentou oscilação, não mantendo a temperatura estável. |
| 2 | Por que o controlador de temperatura oscilou? | Porque o componente já apresentava sinais de desgaste elétrico, identificados só depois do lote. |
| 3 | Por que esse desgaste não foi identificado antes? | Porque não existe uma rotina de inspeção preventiva periódica desse controlador. |
| 4 | Por que não existe essa rotina de inspeção preventiva? | Porque a manutenção desse equipamento é feita reativamente, só quando ocorre falha visível. |
| 5 | Por que a manutenção é reativa e não preventiva? | Porque não há um cronograma formal de manutenção preditiva/preventiva para os sistemas de aquecimento dos biorreatores. |

**Causa raiz esperada:** ausência de um cronograma formal de manutenção
preventiva/preditiva para os sistemas de aquecimento, permitiu que o
controlador de temperatura operasse desgastado sem ser identificado,
causando oscilação e elevando a temperatura do lote fora da faixa
aceitável.

---

## Lote 610: Deriva de calibração do sensor de temperatura

**Ficha do lote:** `ACCEPTABLE` / `MEDIUM_RISK` / compliance_score 83.96,
parâmetro fora da faixa: temperatura.

**Causa raiz "oficial" do dataset:** deriva de calibração do sensor de
temperatura.

### Fase 1: Mapeamento Ishikawa

| Categoria | Resposta sugerida |
|---|---|
| **Método** | Não houve mudança de procedimento ou receita neste lote, seguimos o protocolo padrão normalmente. |
| **Máquina** | Não houve intervenção extraordinária nos equipamentos, a manutenção preventiva do sistema de aquecimento e do agitador está em dia. |
| **Material** | Materiais e insumos habituais, mesmo fornecedor e mesmo lote de sempre, sem alteração de aspecto visível na inspeção de recebimento. |
| **Mão de obra** | Não houve troca de equipe nem pendência de treinamento; a equipe é experiente e seguiu o procedimento operacional padrão normalmente. |
| **Meio ambiente** | Não houve condição ambiental atípica, sala dentro dos parâmetros esperados. |
| **Medição** | O sensor de temperatura apresentou deriva de calibração durante este lote; a última calibração já estava vencida há algumas semanas, e a leitura mostrou desvio consistente em relação ao valor real esperado do processo. |

**Categoria principal esperada:** Medição (sensor de temperatura com
calibração vencida, apresentando deriva). As outras 5 são descartadas
porque cada resposta acima já nega qualquer sinal de problema.

### Fase 2: 5 Porquês (ancorados em Medição)

| # | Por quê | Resposta sugerida |
|---|---|---|
| 1 | Por que o sensor de temperatura apresentou deriva de calibração? | Porque a calibração do sensor já estava vencida há algumas semanas quando este lote foi processado. |
| 2 | Por que a calibração estava vencida? | Porque o prazo de recalibração desse sensor específico não foi cumprido dentro do cronograma padrão. |
| 3 | Por que o prazo de recalibração não foi cumprido? | Porque não existe um alerta automático que avise a equipe de metrologia quando um sensor se aproxima do vencimento da calibração. |
| 4 | Por que não existe esse alerta automático? | Porque o controle de prazos de calibração é feito manualmente, em planilha, sem monitoramento sistemático. |
| 5 | Por que o controle de calibração é manual e não sistematizado? | Porque não existe um sistema informatizado de gestão de calibração (metrologia) integrado ao cronograma de produção da planta. |

**Causa raiz esperada:** ausência de um sistema informatizado de gestão
de calibração que alerte automaticamente sobre prazos vencidos, permitiu
que o sensor de temperatura operasse além do prazo de calibração sem
ser identificado, causando leituras com deriva e registrando a
temperatura do lote fora da faixa aceitável.

---

## Lote 611: Agitador com velocidade abaixo do padrão

**Ficha do lote:** `WARNING` / `MEDIUM_RISK` / compliance_score 71.32,
parâmetros fora da faixa: oxigênio dissolvido e velocidade do agitador
(par correlacionado, menos agitação, menos transferência de oxigênio).

**Causa raiz "oficial" do dataset:** agitador configurado com RPM muito
baixo.

### Fase 1: Mapeamento Ishikawa

| Categoria | Resposta sugerida |
|---|---|
| **Método** | Não houve mudança de procedimento ou receita neste lote. |
| **Máquina** | Sim, o inversor de frequência do agitador estava com o setpoint de velocidade abaixo do valor padrão do processo; a manutenção preventiva do agitador está com o cronograma atrasado. |
| **Material** | Materiais e insumos são do fornecedor e lote habituais, sem alteração de aspecto. |
| **Mão de obra** | Não houve troca de equipe, mas o setpoint do inversor não foi conferido antes de iniciar o lote. |
| **Meio ambiente** | Não houve condição ambiental atípica. |
| **Medição** | O sensor de velocidade (tacômetro) está calibrado, a leitura baixa reflete a velocidade real do equipamento, não erro de sensor. |

**Categoria principal esperada:** Máquina (setpoint do agitador
configurado abaixo do padrão). As outras 5 são descartadas pelo mesmo
motivo: cada resposta já nega sinal de problema.

### Fase 2: 5 Porquês (ancorados em Máquina)

| # | Por quê | Resposta sugerida |
|---|---|---|
| 1 | Por que o agitador operou com velocidade abaixo do padrão? | Porque o setpoint configurado no inversor de frequência estava abaixo do valor padrão do processo. |
| 2 | Por que o setpoint estava abaixo do padrão? | Porque foi alterado durante o ajuste do lote anterior e não foi restaurado ao valor padrão. |
| 3 | Por que não foi restaurado antes de iniciar este lote? | Porque não existe uma etapa de conferência do setpoint do agitador no checklist de início de lote. |
| 4 | Por que o checklist não inclui essa conferência? | Porque o checklist foi criado antes da instalação do inversor de frequência atual e nunca foi atualizado. |
| 5 | Por que o checklist não foi atualizado após a troca do inversor? | Porque não existe um processo formal de revisão de documentos quando um equipamento é trocado ou atualizado. |

**Causa raiz esperada:** ausência de atualização do checklist de início
de lote após a instalação de um novo inversor de frequência no agitador,
permitiu que um setpoint de velocidade incorreto (deixado de um ajuste
anterior) não fosse detectado antes do início do processo, reduzindo a
velocidade real do agitador e, por consequência, a transferência de
oxigênio (KLa) e a concentração de oxigênio dissolvido no lote.

**Confirmado em produção:** relatório real gerado, `GET /api/relatorios/2`.

---

## Lote 612: Erro de configuração do agitador

**Ficha do lote:** `ACCEPTABLE` / `MEDIUM_RISK` / compliance_score 84.36,
parâmetro fora da faixa: velocidade do agitador.

**Causa raiz "oficial" do dataset:** erro de configuração do agitador.

### Fase 1: Mapeamento Ishikawa

| Categoria | Resposta sugerida |
|---|---|
| **Método** | Não houve mudança no protocolo do processo em si, mas o parâmetro de velocidade do agitador informado ao operador para configuração estava incorreto na ordem de produção deste lote. |
| **Máquina** | Não houve falha mecânica no agitador nem no inversor de frequência; o equipamento respondeu exatamente ao valor que foi configurado nele. |
| **Material** | Materiais e insumos habituais, mesmo fornecedor e mesmo lote de sempre, sem alteração de aspecto visível na inspeção de recebimento. |
| **Mão de obra** | Não houve troca de equipe nem pendência de treinamento; o operador configurou o agitador exatamente com o valor que constava na ordem de produção deste lote. |
| **Meio ambiente** | Não houve condição ambiental atípica, sala dentro dos parâmetros esperados. |
| **Medição** | O sensor de velocidade (tacômetro) está calibrado, sem histórico de desvio; a leitura reflete a velocidade real configurada, não erro de sensor. |

**Categoria principal esperada:** Método (parâmetro de velocidade
incorreto na ordem de produção, causa raiz de configuração e não de
equipamento ou operador). As outras 5 são descartadas porque cada
resposta acima já nega qualquer sinal de problema nelas.

### Fase 2: 5 Porquês (ancorados em Método)

| # | Por quê | Resposta sugerida |
|---|---|---|
| 1 | Por que o agitador foi configurado com uma velocidade incorreta? | Porque a ordem de produção deste lote trazia um valor de setpoint de velocidade diferente do padrão definido na receita do processo. |
| 2 | Por que a ordem de produção trazia um valor incorreto? | Porque o valor foi digitado manualmente a partir de uma versão desatualizada da receita, sem conferência cruzada. |
| 3 | Por que foi usada uma versão desatualizada da receita? | Porque não existe um controle central único de versão de receitas, e cópias antigas continuam acessíveis à equipe de produção. |
| 4 | Por que não existe esse controle central de versão? | Porque as receitas de processo ainda são geridas em arquivos compartilhados, sem um sistema de gestão de documentos com controle de versão. |
| 5 | Por que a gestão de receitas não usa um sistema com controle de versão? | Porque a planta ainda não implementou um sistema eletrônico de gestão de documentos (EDMS) para receitas e ordens de produção. |

**Causa raiz esperada:** ausência de um sistema eletrônico de gestão de
documentos com controle de versão para receitas de processo, permitiu
que uma versão desatualizada da receita fosse usada na ordem de
produção deste lote, levando à configuração de uma velocidade de
agitação incorreta e registrando o parâmetro fora da faixa aceitável.

---

## Lote 613: Válvula de contrapressão travada

**Ficha do lote:** `ACCEPTABLE` / `MEDIUM_RISK` / compliance_score 84.56,
parâmetro fora da faixa: pressão.

**Causa raiz "oficial" do dataset:** válvula de contrapressão travada.

### Fase 1: Mapeamento Ishikawa

| Categoria | Resposta sugerida |
|---|---|
| **Método** | Não houve mudança de procedimento ou receita neste lote, seguimos o protocolo padrão normalmente. |
| **Máquina** | Sim, a válvula de contrapressão do biorreator ficou parcialmente travada durante este lote, impedindo o ajuste correto da pressão interna; a manutenção preventiva dessa válvula estava atrasada. |
| **Material** | Materiais e insumos habituais, mesmo fornecedor e mesmo lote de sempre, sem alteração de aspecto visível na inspeção de recebimento. |
| **Mão de obra** | Não houve troca de equipe nem pendência de treinamento; a equipe é experiente e seguiu o procedimento operacional padrão normalmente. |
| **Meio ambiente** | Não houve condição ambiental atípica, sala dentro dos parâmetros esperados. |
| **Medição** | O sensor de pressão está calibrado, sem histórico de desvio; a leitura reflete a pressão real do lote, não erro de medição. |

**Categoria principal esperada:** Máquina (válvula de contrapressão
travada). As outras 5 são descartadas porque cada resposta acima já
nega qualquer sinal de problema.

### Fase 2: 5 Porquês (ancorados em Máquina)

| # | Por quê | Resposta sugerida |
|---|---|---|
| 1 | Por que a válvula de contrapressão travou? | Porque houve acúmulo de resíduo/incrustação no mecanismo interno da válvula, impedindo seu movimento livre. |
| 2 | Por que houve esse acúmulo de resíduo na válvula? | Porque a válvula não passou pela limpeza/inspeção interna programada no intervalo recomendado pelo fabricante. |
| 3 | Por que a limpeza/inspeção interna não foi feita no prazo? | Porque não existe uma ordem de serviço automática gerada quando o intervalo de limpeza dessa válvula se aproxima. |
| 4 | Por que não existe essa geração automática de ordem de serviço? | Porque o plano de manutenção preventiva de válvulas críticas ainda é controlado manualmente. |
| 5 | Por que o plano de manutenção de válvulas críticas é manual e não automatizado? | Porque não existe um sistema informatizado de manutenção (CMMS) que dispare alertas automáticos por componente crítico. |

**Causa raiz esperada:** ausência de um sistema informatizado de
manutenção (CMMS) que gere alertas automáticos de limpeza/inspeção para
válvulas críticas, permitiu que a válvula de contrapressão acumulasse
resíduo além do intervalo recomendado e travasse parcialmente, impedindo
o controle correto da pressão do lote.

---

## Lote 614: Vazamento na linha/vedação do reator

**Ficha do lote:** `ACCEPTABLE` / `MEDIUM_RISK` / compliance_score 84.56,
parâmetro fora da faixa: pressão.

**Causa raiz "oficial" do dataset:** vazamento na linha/vedação do
reator.

### Fase 1: Mapeamento Ishikawa

| Categoria | Resposta sugerida |
|---|---|
| **Método** | Não houve mudança de procedimento ou receita neste lote, seguimos o protocolo padrão normalmente. |
| **Máquina** | Sim, foi identificado um pequeno vazamento na vedação de uma conexão da linha de pressão do reator durante este lote; essa vedação já estava com a troca preventiva atrasada. |
| **Material** | Materiais e insumos habituais, mesmo fornecedor e mesmo lote de sempre, sem alteração de aspecto visível na inspeção de recebimento. |
| **Mão de obra** | Não houve troca de equipe nem pendência de treinamento; a equipe é experiente e seguiu o procedimento operacional padrão normalmente. |
| **Meio ambiente** | Não houve condição ambiental atípica, sala dentro dos parâmetros esperados. |
| **Medição** | O sensor de pressão está calibrado, sem histórico de desvio; a leitura reflete a pressão real do lote, não erro de medição. |

**Categoria principal esperada:** Máquina (vazamento na vedação da linha
de pressão). As outras 5 são descartadas porque cada resposta acima já
nega qualquer sinal de problema.

### Fase 2: 5 Porquês (ancorados em Máquina)

| # | Por quê | Resposta sugerida |
|---|---|---|
| 1 | Por que houve vazamento na linha de pressão do reator? | Porque a vedação (o-ring/gaxeta) de uma das conexões da linha estava ressecada e perdeu a estanqueidade. |
| 2 | Por que a vedação estava ressecada? | Porque já tinha ultrapassado a vida útil recomendada pelo fabricante sem ser trocada preventivamente. |
| 3 | Por que a vedação não foi trocada preventivamente a tempo? | Porque não existe um plano de troca preventiva por tempo de uso para vedações críticas dessa linha. |
| 4 | Por que não existe esse plano de troca preventiva por tempo de uso? | Porque a substituição de vedações é feita reativamente, só quando um vazamento já é percebido. |
| 5 | Por que a substituição de vedações é reativa e não preventiva? | Porque não há um cronograma formal de manutenção preditiva/preventiva para vedações críticas no plano de manutenção da planta. |

**Causa raiz esperada:** ausência de um cronograma formal de manutenção
preventiva/preditiva para vedações críticas da linha de pressão,
permitiu que uma vedação ressecada operasse além da vida útil
recomendada sem ser trocada, causando vazamento e registrando a
pressão do lote fora da faixa aceitável.

---

## Lote 615: Falha no suprimento de ar

**Ficha do lote:** `ACCEPTABLE` / `MEDIUM_RISK` / compliance_score 85.04,
parâmetro fora da faixa: oxigênio dissolvido.

**Causa raiz "oficial" do dataset:** falha no suprimento de ar.

### Fase 1: Mapeamento Ishikawa

| Categoria | Resposta sugerida |
|---|---|
| **Método** | Não houve mudança de procedimento ou receita neste lote, seguimos o protocolo padrão normalmente. |
| **Máquina** | Não houve falha nos equipamentos do próprio biorreator (agitador, sensores); a queda de aeração veio de fora do equipamento, do suprimento de ar da planta. |
| **Material** | Materiais e insumos habituais, mesmo fornecedor e mesmo lote de sempre, sem alteração de aspecto visível na inspeção de recebimento. |
| **Mão de obra** | Não houve troca de equipe nem pendência de treinamento; a equipe é experiente e seguiu o procedimento operacional padrão normalmente. |
| **Meio ambiente** | Sim, houve uma interrupção intermitente no suprimento de ar comprimido da planta durante este lote, reduzindo a aeração/oxigenação do biorreator; o compressor central da utilidade de ar apresentou instabilidade nesse período. |
| **Medição** | O sensor de oxigênio dissolvido está calibrado, sem histórico de desvio; a leitura reflete a concentração real de oxigênio no lote, não erro de medição. |

**Categoria principal esperada:** Meio ambiente (interrupção do
suprimento de ar comprimido da planta, utilidade externa ao biorreator).
As outras 5 são descartadas porque cada resposta acima já nega qualquer
sinal de problema.

### Fase 2: 5 Porquês (ancorados em Meio ambiente)

| # | Por quê | Resposta sugerida |
|---|---|---|
| 1 | Por que houve interrupção no suprimento de ar comprimido? | Porque o compressor central da utilidade de ar da planta apresentou instabilidade de pressão durante o período deste lote. |
| 2 | Por que o compressor apresentou essa instabilidade? | Porque o filtro de entrada do compressor estava saturado, reduzindo o fluxo de ar admitido. |
| 3 | Por que o filtro estava saturado? | Porque a troca periódica desse filtro não foi feita no intervalo recomendado pelo fabricante. |
| 4 | Por que a troca periódica do filtro não foi feita no prazo? | Porque a manutenção da central de ar comprimido não está no mesmo cronograma de manutenção preventiva dos equipamentos de produção. |
| 5 | Por que a central de ar comprimido não está nesse cronograma? | Porque não existe um plano de manutenção preventiva unificado que cubra também as utilidades (ar, vapor, água) que atendem os biorreatores. |

**Causa raiz esperada:** ausência de um plano de manutenção preventiva
unificado que cubra as utilidades da planta (ar comprimido, entre
outras), permitiu que o filtro do compressor central operasse saturado
sem ser trocado no prazo, causando instabilidade no suprimento de ar e
reduzindo a concentração de oxigênio dissolvido do lote abaixo da faixa
aceitável.
