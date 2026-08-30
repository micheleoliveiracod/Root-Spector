# Medição

Quando o diagrama de Ishikawa identifica Medição como categoria
principal, meu foco de investigação se volta para o próprio instrumento
de leitura, e não para o processo que ele mede: considero a hipótese de
que o sensor associado ao parâmetro fora da faixa esteja com a
calibração vencida, ou apresentando problema de leitura ou de registro de
dados, e não que o processo em si tenha, de fato, saído da faixa
aceitável.

## O que verifico

Verifico, em primeiro lugar, a data da última calibração do sensor
associado ao parâmetro fora da faixa, comparando-a com a periodicidade
definida no plano de calibração daquele instrumento. Um sensor com
calibração vencida no momento do lote é, para mim, um forte candidato a
causa raiz nesta categoria, especialmente quando o desvio observado é
compatível com o tipo de erro sistemático que uma descalibração
costuma introduzir.

Distingo dois padrões de desvio que apontam para hipóteses diferentes
dentro desta mesma categoria. Um valor isolado, muito fora da faixa
esperada, sem repetição no restante da série temporal de leituras
daquele lote, sugere ruído ou falha pontual de leitura, não um desvio
real de processo. Já um desvio gradual, uma tendência lenta e consistente
na mesma direção ao longo de todo o lote, é mais compatível com sensor
descalibrado por deriva progressiva do que com um evento pontual. Para
diferenciar entre essas duas hipóteses, recorro à consulta de leituras
históricas de biosensor do lote sempre que a resposta do operador não for
suficiente para esclarecer o padrão observado.

## Relação com bioprocessos

Sensores de bioprocesso, como sondas de pH e de oxigênio dissolvido,
ficam em contato direto e prolongado com um meio biológico ativo, o que
os torna sujeitos a formas de degradação pouco comuns em instrumentação
de processos químicos convencionais, como o biofouling, acúmulo de
material biológico na superfície da sonda que altera gradualmente sua
resposta sem que o sensor pare de funcionar. Esse tipo de degradação
tende a se manifestar como um desvio gradual e não como uma falha
abrupta, o que reforça, no meu domínio, a importância de diferenciar
entre um valor isolado fora da faixa, mais compatível com ruído pontual
de leitura, e uma tendência lenta e consistente ao longo do lote, mais
compatível com deriva de sensor por degradação biológica acumulada na
própria sonda.

## O que preciso para elaborar a não conformidade

Para formular o documento de não conformidade e a tratativa recomendada,
preciso registrar qual sensor específico está associado ao parâmetro fora
da faixa, a data da sua última calibração em relação à periodicidade
definida, e se o padrão de leitura observado é compatível com valor
isolado ou com tendência gradual ao longo do lote. A partir dessas
informações, formulo a recomendação de tratativa esperando que a equipe
de qualidade recalibre ou substitua o sensor identificado, invalide a
leitura suspeita e reavalie a conformidade do lote a partir dos demais
parâmetros quando o desvio for de leitura e não de processo real, e
revise a periodicidade de calibração daquele sensor específico quando o
padrão de descalibração se mostrar recorrente.

## Como formulo a tratativa

Quando concluo que a causa raiz está num sensor com calibração vencida ou
descalibrado, recomendo, como ação corretiva, a recalibração ou a
substituição do sensor identificado antes da liberação de lotes
subsequentes que dependam dele. Quando concluo, ao contrário, que o
desvio observado é apenas de leitura, um erro pontual de medição, e não
um desvio real do processo biológico em si, entendo que a ação corretiva
correta é invalidar a leitura suspeita e reavaliar a conformidade do lote
a partir dos demais parâmetros disponíveis, em vez de tratar a leitura
isolada como evidência de uma não conformidade real de processo. Em
ambos os casos, considero, seguindo a lógica CAPA descrita no arquivo
`capa_pdca.md` desta base, que a ação preventiva de fundo deveria revisar
a adequação da periodicidade de calibração daquele sensor específico, caso
o padrão de descalibração se repita ao longo de investigações
posteriores.
