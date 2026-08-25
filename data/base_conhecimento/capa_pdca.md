# CAPA e PDCA

Depois de identificar a causa raiz de uma não conformidade através do
diagrama de Ishikawa e do método dos 5 Porquês, estruturo a recomendação
de tratativa segundo duas metodologias complementares e amplamente
adotadas na indústria farmacêutica e de bioprocessos: CAPA (Corrective
and Preventive Action) e PDCA (Plan-Do-Check-Act).

## CAPA

CAPA é um sistema de gestão de qualidade que trata tanto a correção
imediata de uma não conformidade já ocorrida quanto a eliminação da causa
que a originou, para reduzir a probabilidade de recorrência. O termo foi
formalizado pelo FDA em 2006, como parte da orientação sobre sistemas de
qualidade farmacêutica, e depois incorporado à diretriz ICH Q10, que
trata do sistema de qualidade farmacêutica em escala internacional.
Considero relevante distinguir três elementos que compõem um sistema CAPA
completo, seguindo a estrutura descrita por Arunagiri, Kannaiah e
Vasanthan em revisão publicada em 2024:

**Correção**, ou ação de remediação, é a resposta imediata ao efeito
observado, sem necessariamente atacar a causa. No meu domínio, corresponde,
por exemplo, a isolar um lote, invalidar uma leitura de sensor suspeita ou
reprocessar um lote específico.

**Ação corretiva** é a ação voltada a eliminar a causa raiz de uma não
conformidade já ocorrida, para que o mesmo problema não se repita pela
mesma razão. Diferencia-se da correção por atuar sobre a causa, não
apenas sobre o efeito.

**Ação preventiva** é a ação voltada a eliminar a causa de uma não
conformidade potencial, ainda não ocorrida, mas identificada como risco
a partir da análise de um caso já investigado. É a dimensão prospectiva
do sistema, que impede a ocorrência antes mesmo do primeiro caso real.

Arunagiri, Kannaiah e Vasanthan destacam que a análise de causa raiz é
pré-requisito indispensável para que a ação corretiva e a ação preventiva
sejam eficazes, e que a ausência de uma investigação de causa raiz
estruturada é uma das principais razões pelas quais sistemas CAPA falham
na prática, tratando sintomas em vez de causas sistêmicas. Essa
constatação reforça, na minha investigação, a importância de só formular
a recomendação de tratativa depois de concluída a cadeia completa de
Ishikawa e 5 Porquês, nunca antes.

## PDCA

O ciclo PDCA tem origem no trabalho de Walter A. Shewhart, estatístico
dos Laboratórios Bell, que descreveu em 1939 um ciclo de melhoria
científica em três etapas. William Edwards Deming estendeu essa proposta
para quatro etapas e a apresentou à União Japonesa de Cientistas e
Engenheiros em 1950, ocasião em que a comunidade japonesa de qualidade
reformulou e nomeou o ciclo como Plan-Do-Check-Act, incorporando-o como
eixo operacional do movimento da qualidade no Japão do pós-guerra. Por
essa razão, o ciclo também é chamado de ciclo de Shewhart, e em algumas
variantes de ciclo PDSA, substituindo Check por Study.

As quatro etapas do ciclo, na forma como as aplico à recomendação de
tratativa, são:

**Plan (planejar)**: definição da ação corretiva e preventiva a partir da
causa raiz identificada, incluindo o resultado esperado e o critério que
será usado para avaliar se a ação foi eficaz.

**Do (executar)**: implementação da ação planejada, em escala controlada
quando aplicável, antes de estendê-la a todo o processo produtivo.

**Check (verificar)**: avaliação dos resultados da ação executada, num
horizonte de tempo ou amostra de lotes suficiente para verificar se o
efeito esperado de fato ocorreu, e se a não conformidade original deixou
de se repetir.

**Act (agir)**: incorporação definitiva da ação ao processo, caso a
verificação confirme eficácia, ou reinício do ciclo a partir de uma nova
hipótese, caso a ação não tenha produzido o resultado esperado.

Sokovic, Pavletic e Kern Pipan descrevem o PDCA como uma metodologia de
melhoria contínua aplicável de forma recorrente, e não como um
procedimento de execução única: cada volta completa do ciclo gera
aprendizado que alimenta o ciclo seguinte, o que é consistente com a
noção de melhoria contínua incorporada à norma ISO 9001. Essa natureza
cíclica é o motivo pelo qual considero especialmente relevante o dado de
recorrência de uma não conformidade: uma tratativa recomendada para um
caso que já se repetiu antes, com a mesma categoria e causa raiz
semelhante, é um indício direto de que o ciclo PDCA de uma tratativa
anterior não foi concluído com sucesso, seja porque a etapa Check nunca
foi de fato executada, seja porque a ação planejada não foi implementada
como previsto. Nesses casos, formulo a recomendação de tratativa
priorizando esse histórico, em vez de repetir a mesma ação que já se
mostrou insuficiente.

## Como aplico as duas metodologias na minha investigação

Trato CAPA como o enquadramento do que a tratativa deve conter, correção
do caso pontual, ação corretiva sobre a causa e ação preventiva sobre a
recorrência, e PDCA como o processo pelo qual a eficácia dessa tratativa
deveria, no fluxo real de qualidade da planta, ser verificada ao longo do
tempo. A recomendação de tratativa que produzo ao final da investigação
não substitui esse ciclo de verificação: ela formula a ação recomendada a
partir da causa raiz e da base de conhecimento curada, e cabe ao processo
de qualidade da planta conduzir as etapas de execução e verificação que
completam o ciclo.

Toda tratativa recomendada deve ser rastreável até a causa raiz que a
originou e até as fontes específicas, categoria de Ishikawa e evidência
levantada, que a embasaram. Sem essa rastreabilidade, considero que a
tratativa não é auditável, o que é um requisito básico tanto do sistema
CAPA quanto da governança documental exigida pela legislação de boas
práticas de fabricação (ver arquivo `bpf_anvisa.md` desta base).

## Relação com bioprocessos

Um bioprocesso é produzido em lotes, e um lote já processado não pode ser
desfeito: se um cultivo terminou fora de especificação, a única correção
possível é decidir o destino daquele lote específico, reprocessar,
descartar ou liberar com desvio documentado, mas o processo em si já
ocorreu e não pode ser reexecutado retroativamente. Essa característica
torna a distinção entre correção, ação corretiva e ação preventiva
particularmente relevante no meu domínio: a correção resolve apenas o
lote que já não existe mais para ser corrigido em processo, enquanto a
ação corretiva e a ação preventiva são o que de fato protege os lotes
futuros, que ainda serão processados. Por essa razão, considero
insuficiente qualquer tratativa que se limite a decidir o destino do lote
atual sem propor também a ação sobre a causa raiz que impeça a repetição
do mesmo desvio no próximo lote.

## O que preciso para elaborar a não conformidade

Para formular a recomendação de tratativa, preciso ter em mãos a causa
raiz e a narrativa produzidas ao final da cadeia de Ishikawa e 5
Porquês, além dos casos semelhantes já registrados em investigações
anteriores, quando existirem, para saber se estou diante de um caso
inédito ou de uma recorrência. A partir desses elementos, formulo a
recomendação de tratativa já estruturada nos termos de CAPA, correção do
lote atual quando aplicável, ação corretiva sobre a causa identificada e
ação preventiva sobre o risco de recorrência, esperando que a equipe de
qualidade planeje a execução dessa ação segundo o ciclo PDCA completo:
definir o resultado esperado e o critério de sucesso antes de agir,
executar a ação, verificar sua eficácia após um período ou amostra de
lotes suficiente, e só então incorporá-la de forma permanente ao
processo. Quando o caso já é recorrente, registro esse histórico
explicitamente na recomendação, para que a equipe de qualidade priorize a
investigação e não repita uma tratativa que já se mostrou ineficaz.

## Referências bibliográficas

1. ARUNAGIRI, Thirumalai; KANNAIAH, Kanaka P.; VASANTHAN, Manimaran.
   Enhancing Pharmaceutical Product Quality With a Comprehensive
   Corrective and Preventive Actions (CAPA) Framework: From Reactive to
   Proactive. *Cureus*, v. 16, n. 7, e64760, 2024.
2. SOKOVIC, Mirko; PAVLETIC, Dubravko; KERN PIPAN, Ksenija. Quality
   Improvement Methodologies: PDCA Cycle, RADAR Matrix, DMAIC and DFSS.
   *Journal of Achievements in Materials and Manufacturing Engineering*,
   v. 43, n. 1, p. 476-483, 2010.
