# Gabarito de teste: Lote 6 e Lote 11

Roteiro de respostas prontas pra quem for testar o Root-Spector de ponta a
ponta, sabendo de antemão a causa raiz "oficial" de cada lote (definida em
`data/simulacao_causa_raiz/README.md`, cenários `desvio_01` e `desvio_06`).

A regra de elegibilidade de `GET /api/lotes` (`backend/main.py:listar_lotes`)
passa a considerar `risk_prediction` e `parametros_fora_da_faixa`, não só o
`compliance_score` do BiotecPredict. Antes dessa correção, `desvio_01` e
`desvio_06` (lotes 6 e 11 no dataset de exemplo) eram os únicos dois
elegíveis, os outros 8 lotes com desvio ficavam `ACCEPTABLE` pelo score e
não apareciam como investigáveis. Com a correção, os 10 lotes com desvio
aparecem como elegíveis, porque todos têm `risk_prediction` MEDIUM_RISK ou
HIGH_RISK mesmo quando o `compliance_score` fica ACCEPTABLE:

| Causa raiz simulada | Sensor(es) afetado(s) | Score | Classificação | Risco ML |
|---|---|---|---|---|
| Contaminação microbiana / meio de cultura ruim (`desvio_01`, lote 6) | pH + temperatura + OD | 48.31 | WARNING | HIGH_RISK |
| Falha na bomba dosadora de base (`desvio_02`) | pH | 84.13 | ACCEPTABLE | MEDIUM_RISK |
| Falha na bomba dosadora de ácido (`desvio_03`) | pH | 84.53 | ACCEPTABLE | MEDIUM_RISK |
| Falha no sistema de aquecimento (`desvio_04`) | temperatura | 84.65 | ACCEPTABLE | MEDIUM_RISK |
| Deriva de calibração do sensor de temperatura (`desvio_05`) | temperatura | 83.96 | ACCEPTABLE | MEDIUM_RISK |
| Agitador com RPM muito baixo (`desvio_06`, lote 11) | agitador + OD | 71.32 | WARNING | MEDIUM_RISK |
| Erro de configuração do agitador (`desvio_07`) | agitador | 84.36 | ACCEPTABLE | MEDIUM_RISK |
| Válvula de contrapressão travada (`desvio_08`) | pressão | 84.56 | ACCEPTABLE | MEDIUM_RISK |
| Vazamento na linha/vedação do reator (`desvio_09`) | pressão | 84.56 | ACCEPTABLE | MEDIUM_RISK |
| Falha no suprimento de ar (`desvio_10`) | oxigênio dissolvido | 85.04 | ACCEPTABLE | MEDIUM_RISK |

O `batch_id` real de cada lote depende da ordem de upload no BiotecPredict,
por isso a tabela usa o nome do arquivo CSV, não um número de lote fixo,
exceto pelos lotes 6 e 11 já documentados abaixo. O roteiro completo de
respostas (Ishikawa + 5 Porquês) dos outros 8 cenários ainda não foi
escrito aqui, fica como próximo passo para quem for demonstrar esses
casos especificamente.

**Como usar:** a pergunta que o agente mostra na tela é gerada pelo LLM a
cada rodada, a redação varia, mas a intenção de cada categoria é sempre a
mesma (ver `config/regras_bioprocesso.yaml` § `categorias_ishikawa`).
Adapte a resposta abaixo ao que aparecer na tela, mantendo a mesma
substância. O resultado final (categoria principal e causa raiz) depende
da síntese do LLM em cima das suas respostas, as respostas abaixo foram
desenhadas pra deixar só uma categoria com sinal real (as outras
respondem "está tudo normal"), então o esperado é convergir no cenário
descrito, mas a redação exata da causa raiz gerada pode variar.

---

## Lote 6: Contaminação do meio de cultura

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
do ciclo de esterilização do meio de cultura antes da liberação para uso
, permitiu que um meio parcialmente esterilizado (após interrupção por
queda de energia) fosse utilizado, causando contaminação microbiana que
elevou a temperatura e reduziu o pH e o oxigênio dissolvido do lote.

---

## Lote 11: Agitador com velocidade abaixo do padrão

**Ficha do lote:** `WARNING` / `MEDIUM_RISK` / compliance_score 71.32 ,
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
de lote após a instalação de um novo inversor de frequência no agitador ,
permitiu que um setpoint de velocidade incorreto (deixado de um ajuste
anterior) não fosse detectado antes do início do processo, reduzindo a
velocidade real do agitador e, por consequência, a transferência de
oxigênio (KLa) e a concentração de oxigênio dissolvido no lote.
