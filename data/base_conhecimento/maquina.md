# Máquina

Quando a categoria principal identificada pelo diagrama de Ishikawa é
Máquina, dirijo minha investigação ao equipamento diretamente envolvido
no parâmetro que saiu da faixa aceitável, seja o agitador, para o
parâmetro de velocidade de agitação, a bomba, para pressão, ou o próprio
sensor do biosensor, quando o desvio parece estar mais relacionado à
medição do que ao processo real. Nesse último caso, considero também a
categoria Medição como hipótese concorrente, e reviso as evidências antes
de decidir qual das duas melhor explica o desvio observado.

## O que verifico

Meu primeiro passo é levantar o histórico de manutenção do equipamento
associado ao parâmetro fora da faixa, cruzando a data da última
intervenção, corretiva ou preventiva, com a data do lote sob
investigação. Uma manutenção corretiva recente é, na minha experiência,
um dos indícios mais diretos de causa raiz nesta categoria: qualquer
reparo altera, ainda que sutilmente, o comportamento do equipamento até
que uma nova qualificação formal seja realizada, processo que na
indústria costuma ser referido pelas etapas de qualificação de instalação,
qualificação de operação e qualificação de desempenho.

Verifico também se a manutenção preventiva programada para aquele
equipamento está em dia ou está atrasada. Um atraso na manutenção
preventiva não costuma produzir um desvio abrupto, mas sim um desvio
gradual, ou drift, que se acumula ao longo do tempo sem ser percebido até
ultrapassar a faixa aceitável, o que reforça a importância de examinar não
apenas o lote atual, mas a tendência de leituras anteriores desse mesmo
equipamento.

## Como uso o histórico de leituras

Quando a evidência levantada na resposta do operador não é suficiente
para confirmar ou descartar a hipótese de causa em Máquina, recorro à
consulta de leituras históricas de biosensor do próprio lote, disponível
como ferramenta durante a investigação. Um padrão de leitura que se
degrada progressivamente ao longo do lote é mais consistente com falha
gradual de equipamento do que um valor isolado fora da faixa, o que ajuda
a diferenciar entre uma causa de Máquina e uma causa pontual de Medição.

## Relação com bioprocessos

O equipamento de bioprocesso interage diretamente com um sistema vivo, e
não apenas com uma solução química inerte, o que torna a categoria
Máquina especialmente sensível neste domínio. O agitador de um
biorreator, por exemplo, precisa manter homogeneidade e transferência de
oxigênio suficiente para o organismo em cultivo, mas uma velocidade de
agitação excessiva pode gerar estresse de cisalhamento e danificar
células ou microrganismos sensíveis, enquanto uma velocidade insuficiente
compromete a oxigenação. Sondas de oxigênio dissolvido e de pH também
respondem de forma gradual à degradação do equipamento, muitas vezes de
forma indistinguível, à primeira vista, de uma alteração real do
metabolismo do organismo em cultivo, o que exige atenção redobrada antes
de atribuir um desvio ao processo biológico em si.

## O que preciso para elaborar a não conformidade

Para formular o documento de não conformidade e a tratativa recomendada,
preciso registrar qual equipamento específico está associado ao
parâmetro fora da faixa, a data da última intervenção de manutenção
sobre ele, corretiva ou preventiva, e se essa intervenção foi seguida de
requalificação formal antes do equipamento voltar a operar. A partir
dessas informações, formulo a recomendação de tratativa esperando que a
equipe de manutenção e qualidade qualifique formalmente o equipamento
antes de liberá-lo para novo uso em produção, revise a periodicidade do
plano de manutenção preventiva quando o atraso for identificado como
causa raiz, e avalie se o desvio observado é compatível com o tipo de
falha mecânica ou de instrumentação identificada, e não apenas com uma
variação normal do processo biológico.

## Como formulo a tratativa

Quando concluo que a causa raiz está numa intervenção de manutenção
recente, recomendo, como ação corretiva, a qualificação formal do
equipamento antes de liberá-lo novamente para uso em produção, garantindo
que o comportamento pós-reparo esteja de fato dentro do especificado.
Quando a causa está num atraso de manutenção preventiva, entendo que a
ação corretiva pontual, executar a manutenção pendente, não é suficiente:
a ação preventiva, seguindo a lógica CAPA descrita no arquivo
`capa_pdca.md` desta base, precisa revisar a periodicidade do próprio
plano de manutenção preventiva daquele equipamento, para que o atraso não
se repita.
