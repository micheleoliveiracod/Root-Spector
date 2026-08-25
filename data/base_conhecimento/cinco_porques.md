# Método dos 5 Porquês

Depois de identificar, através do diagrama de Ishikawa, a categoria mais
provável de conter a causa raiz de uma não conformidade, aprofundo essa
categoria com o método dos 5 Porquês. Trata-se de uma técnica de
investigação iterativa, na qual pergunto "por quê" repetidamente a partir
de um sintoma ou desvio observado, usando cada resposta como ponto de
partida para a próxima pergunta, até alcançar uma causa que já não é mais
sintoma de algo anterior, mas sim uma condição sistêmica acionável.

## Origem do método

O método foi desenvolvido por Sakichi Toyoda na década de 1930 e
posteriormente refinado por seu filho Kiichiro Toyoda e pelo engenheiro
Taiichi Ohno, no contexto da formação do que se tornaria o Sistema Toyota
de Produção. Ohno formalizou a prática de ir até o local onde o problema
de fato ocorre, o que no vocabulário da manufatura enxuta se chama gemba,
para observar diretamente as condições antes de perguntar por quê, em vez
de investigar apenas a partir de relatos ou registros indiretos. Esse
princípio de observação direta continuo aplicando na minha investigação
ao consultar, sempre que necessário, os dados brutos de biosensor do lote
através da ferramenta de consulta histórica, em vez de depender apenas da
resposta verbal do operador.

## Por que cinco

O número cinco é convencional, não uma regra rígida. A observação
empírica de Ohno e dos primeiros praticantes do método é que cinco
iterações costumam ser suficientes para sair de um sintoma superficial e
alcançar uma causa sistêmica, mas o número exato de perguntas necessárias
varia de acordo com a complexidade do problema: às vezes três perguntas
já revelam uma causa raiz clara, outras vezes são necessárias mais de
cinco. Na minha investigação, fixo cinco iterações como estrutura padrão
por equilibrar profundidade de análise com tempo de interação com o
operador, mas trato o número como um guia prático, não como garantia de
que a quinta resposta sempre será a causa raiz definitiva.

## Como conduzo cada iteração

Ancoro a primeira pergunta na categoria principal identificada pelo
diagrama de Ishikawa e na justificativa que a acompanha. A cada resposta
subsequente, formulo a próxima pergunta a partir da resposta anterior,
sem repetir literalmente a formulação padrão, para manter a pergunta
adequada ao contexto específico levantado até aquele ponto. Assim como na
fase de mapeamento Ishikawa, posso recorrer a uma consulta de dados
históricos de biosensor quando a evidência agregada disponível não for
suficiente para embasar a pergunta seguinte.

## Limitações que considero

Alan Card, em artigo publicado na revista BMJ Quality & Safety, questiona
o uso indiscriminado dos 5 Porquês em investigações de segurança
assistencial complexas, argumentando que o método tende a simplificar
problemas multicausais ao seguir uma única cadeia linear de causalidade,
e que a resposta a cada "por quê" pode ter mais de uma alternativa
plausível, de modo que, sem evidência que indique qual delas está
correta, a investigação corre o risco de seguir um caminho de causalidade
equivocado. Considero essa crítica pertinente e por isso não trato os 5
Porquês como um substituto do diagnóstico completo: o método aprofunda
uma única categoria já selecionada pelo diagrama de Ishikawa a partir de
evidência levantada nas seis categorias, e cada resposta do operador
passa por uma camada de validação antes de ser aceita como suficientemente
informativa para prosseguir à pergunta seguinte, o que reduz, ainda que
não elimine, o risco de avançar por um caminho de causalidade mal
embasado.

Serrat descreve o método como simples, versátil e acessível a
praticantes sem necessidade de ferramentas estatísticas avançadas,
características que valorizo por permitir que qualquer operador
participe da investigação sem treinamento prévio em métodos formais de
qualidade. Ao mesmo tempo, mantenho em mente a ressalva de Card: o método
funciona melhor como ferramenta de aprofundamento dentro de uma
investigação já estruturada por outra técnica, no meu caso o diagrama de
Ishikawa, do que como método isolado de investigação de causa raiz.

## Relação com bioprocessos

Num bioprocesso, a cadeia de causalidade entre um evento inicial e o
desvio de parâmetro finalmente observado costuma atravessar fronteiras
entre o mundo físico e o mundo biológico, o que torna o aprofundamento
por perguntas sucessivas especialmente útil. Uma primeira resposta pode
apontar para um evento mecânico, como uma falha de agitação, mas a
pergunta seguinte pode revelar que o efeito real sobre o processo foi uma
queda de transferência de oxigênio, e a pergunta seguinte a essa pode
revelar que essa queda alterou a via metabólica do organismo em cultivo
de forma que só se manifestou no parâmetro de pH horas depois. Sem
aprofundar a cadeia além da primeira resposta, a investigação correria o
risco de registrar a causa raiz como o evento mecânico inicial, quando na
verdade a causa raiz sistêmica está na ausência de um mecanismo de
compensação que evitasse que aquele evento mecânico se propagasse até
afetar o metabolismo do processo.

## O que preciso para elaborar a não conformidade

Para elaborar o documento de não conformidade, preciso registrar a cadeia
completa de perguntas e respostas dos 5 Porquês, não apenas a última
resposta obtida, porque é o encadeamento completo que demonstra como se
chegou da categoria principal do diagrama de Ishikawa até a causa raiz
final. A partir dessa cadeia, sintetizo a causa raiz e a narrativa que
explica o raciocínio, e é esse par, causa raiz e narrativa, que alimenta
a formulação da recomendação de tratativa. Espero que a equipe de
qualidade, ao revisar essa cadeia, avalie se a causa raiz apontada é de
fato sistêmica ou se ainda representa um sintoma que mereceria
aprofundamento adicional antes de definir a tratativa final.

## Como a cadeia final é usada

Ao final das cinco iterações, ou menos, caso a informatividade da
resposta assim justifique o encerramento antecipado, sintetizo a causa
raiz sistêmica a partir da categoria principal do diagrama de Ishikawa e
da cadeia completa de perguntas e respostas dos 5 Porquês. Essa síntese
alimenta, junto da base de conhecimento curada, a recomendação de
tratativa descrita no arquivo `capa_pdca.md` desta base.

## Referências bibliográficas

1. SERRAT, Olivier. The Five Whys Technique. In: SERRAT, Olivier.
   *Knowledge Solutions: Tools, Methods, and Approaches to Drive
   Organizational Performance*. Singapura: Springer, 2017. p. 307-310.
2. CARD, Alan J. The problem with '5 whys'. *BMJ Quality & Safety*,
   v. 26, n. 8, p. 671-677, 2017.
