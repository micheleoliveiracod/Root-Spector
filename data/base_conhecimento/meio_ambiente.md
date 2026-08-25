# Meio ambiente

Quando o diagrama de Ishikawa identifica Meio ambiente como categoria
principal, dirijo minha investigação às condições da sala e das
utilidades em que o lote foi processado: temperatura ambiente, umidade,
iluminação, ventilação e climatização, além de eventos de energia ou de
água que possam ter ocorrido durante o processamento.

## O que verifico

Cruzo o intervalo de tempo em que o desvio de parâmetro foi observado com
o registro de monitoramento ambiental da sala, quando disponível,
incluindo temperatura, umidade e, em salas classificadas, pressão
diferencial entre ambientes. Verifico também se há registro de queda de
energia, falha de climatização ou outra manutenção de utilidade que
tenha ocorrido no mesmo período do lote sob investigação.

Considero relevante que uma condição ambiental atípica pode afetar o
bioprocesso de forma indireta, e não apenas por contato direto: uma
temperatura de sala elevada, por exemplo, pode dificultar o controle de
temperatura do biorreator mesmo quando o próprio equipamento de controle
de temperatura está funcionando corretamente, o que exige distinguir essa
hipótese da hipótese de causa em Máquina antes de concluir a
investigação.

Um padrão que uso para diferenciar causa ambiental de outras causas é a
recorrência entre lotes distintos: um evento pontual, como uma queda de
energia isolada ou um pico de temperatura externa atípico, tende a se
correlacionar com um único lote processado naquele momento específico. Um
padrão que se repete entre lotes diferentes, processados em momentos
distintos mas na mesma sala ou com a mesma utilidade, é mais consistente
com uma qualificação ambiental desatualizada do que com um evento
pontual.

## Relação com bioprocessos

Instalações de bioprocesso costumam operar sob classificação de sala
limpa, com controle de temperatura, umidade, pressão diferencial entre
ambientes e monitoramento microbiológico do ar, exatamente porque o
material em processamento é biológico e vivo, portanto vulnerável tanto a
contaminação externa quanto a variações ambientais que um processo
puramente químico toleraria sem consequência. Uma falha de climatização,
por exemplo, pode não contaminar o lote, mas ainda assim alterar a
temperatura do biorreator o suficiente para desviar o metabolismo do
organismo em cultivo, produzindo um desvio de parâmetro sem que exista
qualquer falha de equipamento ou de execução envolvida. Por isso, nesta
categoria, procuro sempre correlacionar o desvio observado com o
registro ambiental da sala, e não apenas com o funcionamento do
equipamento de processo em si.

## O que preciso para elaborar a não conformidade

Para formular o documento de não conformidade e a tratativa recomendada,
preciso registrar qual condição ambiental atípica, se houver, ocorreu
durante o processamento do lote, se ela está documentada no
monitoramento ambiental da sala, e se esse mesmo padrão já ocorreu em
lotes anteriores processados na mesma sala ou dependentes da mesma
utilidade. A partir dessas informações, formulo a recomendação de
tratativa esperando que a equipe de qualidade e de infraestrutura avalie
a causa do evento ambiental identificado, implemente resposta
proporcional quando o evento for pontual, e inicie revisão da
qualificação ambiental da sala ou utilidade quando o padrão se mostrar
recorrente entre lotes distintos.

## Como formulo a tratativa

Quando concluo que a causa raiz é um evento ambiental pontual, recomendo,
como ação corretiva, uma resposta proporcional a esse evento específico,
como reforço temporário de climatização durante o período de maior
sensibilidade do processo. Quando o padrão de desvio ambiental se repete
entre diferentes lotes na mesma sala, entendo que a ação preventiva
correta, seguindo a lógica CAPA descrita no arquivo `capa_pdca.md` desta
base, é investigar e atualizar a qualificação ambiental daquela sala ou
utilidade, em vez de tratar cada ocorrência como um evento isolado e
desconectado das anteriores.
