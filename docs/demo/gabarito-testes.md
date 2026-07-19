# Gabarito de teste — Lote 6 e Lote 11

Roteiro de respostas prontas pra quem for testar o Root-Spector de ponta a
ponta, sabendo de antemão a causa raiz "oficial" de cada lote (definida em
`data/simulacao_causa_raiz/README.md`, cenários `desvio_01` e `desvio_06`).
São os **únicos dois lotes elegíveis** (`WARNING`) do dataset atual — os
outros 8 lotes com desvio ficam `ACCEPTABLE` pelo score real do
BiotecPredict e por isso não aparecem como investigáveis na tela.

**Como usar:** a pergunta que o agente mostra na tela é gerada pelo LLM a
cada rodada — a redação varia, mas a intenção de cada categoria é sempre a
mesma (ver `config/regras_bioprocesso.yaml` § `categorias_ishikawa`).
Adapte a resposta abaixo ao que aparecer na tela, mantendo a mesma
substância. O resultado final (categoria principal e causa raiz) depende
da síntese do LLM em cima das suas respostas — as respostas abaixo foram
desenhadas pra deixar só uma categoria com sinal real (as outras
respondem "está tudo normal"), então o esperado é convergir no cenário
descrito, mas a redação exata da causa raiz gerada pode variar.

---

## Lote 6 — Contaminação do meio de cultura

**Ficha do lote:** `WARNING` / `HIGH_RISK` / compliance_score 48.31 —
parâmetros fora da faixa: temperatura, pH, oxigênio dissolvido (os três
juntos, mesma causa física).

**Causa raiz "oficial" do dataset:** contaminação microbiana / meio de
cultura ruim.

### Fase 1 — Mapeamento Ishikawa

| Categoria | Resposta sugerida |
|---|---|
| **Método** | Não houve mudança de procedimento ou receita neste lote — seguimos o protocolo padrão normalmente. |
| **Máquina** | Não houve intervenção nos equipamentos; a manutenção preventiva está em dia. |
| **Material** | Sim — o meio de cultura usado neste lote veio de um novo lote de insumo, e o ciclo de esterilização (autoclave) foi interrompido antes de completar o tempo padrão. A amostra apresentou leve turvação incomum antes da inoculação. |
| **Mão de obra** | Não houve troca de equipe nem pendência de treinamento; a equipe é experiente. |
| **Meio ambiente** | Não houve condição ambiental atípica — sala dentro dos parâmetros esperados. |
| **Medição** | Sensores de temperatura, pH e oxigênio dissolvido calibrados, sem histórico de desvio. |

**Categoria principal esperada:** Material (meio de cultura mal
esterilizado). As outras 5 são descartadas porque cada resposta acima já
nega qualquer sinal de problema.

### Fase 2 — 5 Porquês (ancorados em Material)

| # | Por quê | Resposta sugerida |
|---|---|---|
| 1 | Por que o meio de cultura estava contaminado? | Porque o ciclo de esterilização (autoclave) daquele lote de meio foi interrompido antes de completar o tempo padrão. |
| 2 | Por que o ciclo foi interrompido antes do tempo? | Porque houve uma queda de energia breve durante o ciclo de autoclave. |
| 3 | Por que o meio foi liberado mesmo com o ciclo interrompido? | Porque o operador não percebeu a interrupção e liberou o meio para uso mesmo assim. |
| 4 | Por que o operador liberou o meio sem confirmar o ciclo completo? | Porque não existe uma checagem obrigatória de conclusão do ciclo antes de liberar o meio para uso. |
| 5 | Por que não existe essa checagem obrigatória? | Porque o procedimento operacional padrão não prevê uma verificação e registro formal de conclusão do ciclo de autoclave antes da liberação do meio. |

**Causa raiz esperada:** ausência de uma verificação formal de conclusão
do ciclo de esterilização do meio de cultura antes da liberação para uso
— permitiu que um meio parcialmente esterilizado (após interrupção por
queda de energia) fosse utilizado, causando contaminação microbiana que
elevou a temperatura e reduziu o pH e o oxigênio dissolvido do lote.

---

## Lote 11 — Agitador com velocidade abaixo do padrão

**Ficha do lote:** `WARNING` / `MEDIUM_RISK` / compliance_score 71.32 —
parâmetros fora da faixa: oxigênio dissolvido e velocidade do agitador
(par correlacionado — menos agitação, menos transferência de oxigênio).

**Causa raiz "oficial" do dataset:** agitador configurado com RPM muito
baixo.

### Fase 1 — Mapeamento Ishikawa

| Categoria | Resposta sugerida |
|---|---|
| **Método** | Não houve mudança de procedimento ou receita neste lote. |
| **Máquina** | Sim — o inversor de frequência do agitador estava com o setpoint de velocidade abaixo do valor padrão do processo; a manutenção preventiva do agitador está com o cronograma atrasado. |
| **Material** | Materiais e insumos são do fornecedor e lote habituais, sem alteração de aspecto. |
| **Mão de obra** | Não houve troca de equipe, mas o setpoint do inversor não foi conferido antes de iniciar o lote. |
| **Meio ambiente** | Não houve condição ambiental atípica. |
| **Medição** | O sensor de velocidade (tacômetro) está calibrado — a leitura baixa reflete a velocidade real do equipamento, não erro de sensor. |

**Categoria principal esperada:** Máquina (setpoint do agitador
configurado abaixo do padrão). As outras 5 são descartadas pelo mesmo
motivo: cada resposta já nega sinal de problema.

### Fase 2 — 5 Porquês (ancorados em Máquina)

| # | Por quê | Resposta sugerida |
|---|---|---|
| 1 | Por que o agitador operou com velocidade abaixo do padrão? | Porque o setpoint configurado no inversor de frequência estava abaixo do valor padrão do processo. |
| 2 | Por que o setpoint estava abaixo do padrão? | Porque foi alterado durante o ajuste do lote anterior e não foi restaurado ao valor padrão. |
| 3 | Por que não foi restaurado antes de iniciar este lote? | Porque não existe uma etapa de conferência do setpoint do agitador no checklist de início de lote. |
| 4 | Por que o checklist não inclui essa conferência? | Porque o checklist foi criado antes da instalação do inversor de frequência atual e nunca foi atualizado. |
| 5 | Por que o checklist não foi atualizado após a troca do inversor? | Porque não existe um processo formal de revisão de documentos quando um equipamento é trocado ou atualizado. |

**Causa raiz esperada:** ausência de atualização do checklist de início
de lote após a instalação de um novo inversor de frequência no agitador —
permitiu que um setpoint de velocidade incorreto (deixado de um ajuste
anterior) não fosse detectado antes do início do processo, reduzindo a
velocidade real do agitador e, por consequência, a transferência de
oxigênio (KLa) e a concentração de oxigênio dissolvido no lote.
