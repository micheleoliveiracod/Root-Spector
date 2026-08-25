# Diagrama de Ishikawa

Utilizo o diagrama de Ishikawa como estrutura central da primeira fase da
minha investigação de causa raiz. Também chamado de diagrama de causa e
efeito ou diagrama espinha de peixe, pela forma que assume quando
desenhado à mão, foi desenvolvido por Kaoru Ishikawa, engenheiro químico
japonês, ao longo das décadas de 1960 e 1970, período em que liderava
processos de controle de qualidade nos estaleiros da Kawasaki. Ishikawa é
considerado um dos fundadores da gestão da qualidade moderna, e o
diagrama que leva seu nome integra o conjunto das sete ferramentas
básicas da qualidade, ao lado de instrumentos como o histograma, a folha
de verificação e o diagrama de Pareto.

## Como construo e leio o diagrama

Desenho o problema, ou efeito observado, na cabeça do peixe, à direita do
diagrama. A partir da espinha dorsal, traço ramos que representam
categorias amplas de causas possíveis. A formulação original de Ishikawa
usava quatro categorias voltadas à manufatura, conhecidas como 4M: Método,
Máquina, Material e Mão de obra. Ao longo do tempo, a comunidade de
qualidade expandiu esse modelo para 6M, acrescentando Meio ambiente e
Medição, variação que adoto no meu processo de investigação por cobrir
melhor os fatores ambientais e de instrumentação relevantes num
bioprocesso. Existem ainda variações setoriais com sete ou oito
categorias, algumas delas incorporando Gestão ou Manutenção como ramos
próprios, mas considero que, para o escopo da minha investigação, o 6M
oferece cobertura suficiente sem introduzir redundância entre categorias.

Para cada ramo principal, levanto sub-causas específicas, formando
ramificações menores que se conectam ao ramo principal. Esse
desdobramento é o que diferencia o diagrama de uma simples lista de
hipóteses: ele obriga a explicitar a relação hierárquica entre uma causa
mais geral e as causas mais específicas que a compõem, o que facilita
tanto a geração de hipóteses quanto a comunicação do raciocínio para
quem revisa a investigação depois.

## Por que escolho essa ferramenta

Entendo o diagrama de Ishikawa como uma ferramenta de organização e
levantamento estruturado de hipóteses, não como um método estatístico de
comprovação de causalidade. Ele não me diz qual causa é a verdadeira,
apenas me ajuda a mapear sistematicamente onde procurar, reduzindo a
chance de eu deixar de examinar uma frente de investigação inteira por
viés de ancoragem numa hipótese inicial. Rooney e Vanden Heuvel, num dos
artigos mais citados sobre análise de causa raiz para praticantes,
descrevem o diagrama de causa e efeito exatamente nesse papel: uma
ferramenta de brainstorming estruturado que precisa ser complementada por
evidência e, frequentemente, por uma técnica de aprofundamento como os 5
Porquês, para chegar da causa aparente à causa raiz sistêmica.

Ilie e Ciocoiu, em estudo sobre a aplicação do diagrama a eventos com
múltiplas causas concorrentes, chamam atenção para uma limitação real do
método clássico: quando mais de uma causa contribui simultaneamente para
o efeito observado, o diagrama tradicional tende a tratar cada ramo como
independente, o que pode obscurecer interações entre categorias. Levo
essa limitação em conta na minha investigação ao não me contentar em
apontar uma única categoria principal sem registrar também as categorias
descartadas e a justificativa de cada descarte, prática que documento de
forma estruturada em cada diagnóstico gerado, permitindo revisão posterior
caso uma causa secundária se revele relevante.

## Relação com bioprocessos

Escolhi o diagrama de Ishikawa como ponto de partida da minha
investigação justamente porque um bioprocesso é um sistema com múltiplas
frentes de causa plausíveis e interdependentes: um mesmo desvio de
parâmetro pode originar-se de uma mudança de receita, de um equipamento
degradado, de um insumo biológico fora de especificação, de uma execução
humana inadequada, de uma condição ambiental atípica ou de um sensor
descalibrado, e frequentemente mais de uma dessas frentes contribui
simultaneamente para o efeito observado. A natureza viva do processo, que
responde de forma não linear e às vezes retardada a qualquer uma dessas
seis dimensões, é exatamente o motivo pelo qual considero arriscado
investigar um desvio de bioprocesso a partir de uma única hipótese
inicial sem antes percorrer sistematicamente as seis categorias.

## O que preciso para elaborar a não conformidade

Para elaborar o documento de não conformidade, preciso, ao final do
mapeamento Ishikawa, de três elementos estruturados: a categoria
identificada como principal, com a justificativa que a sustenta a partir
das evidências levantadas nas seis respostas; a lista de categorias
descartadas, cada uma com o motivo específico do descarte; e o registro
literal das perguntas e respostas de cada categoria, que compõe a
evidência auditável da investigação. É a partir da categoria principal,
não das descartadas, que sigo para o aprofundamento pelos 5 Porquês, e é
o conjunto das seis respostas, não apenas a categoria vencedora, que
disponibilizo no diagnóstico final, para que a equipe de qualidade possa
revisar todo o raciocínio, e não apenas a conclusão.

## Aplicação na minha investigação

Na prática, percorro as seis categorias do 6M em sequência fixa,
formulando uma pergunta de contexto por categoria, adaptada à
não-conformidade específica do lote sob investigação. Ao final das seis
respostas, comparo as evidências levantadas em cada ramo e identifico a
categoria mais provável de conter a causa raiz, registrando também o
raciocínio que levou ao descarte das demais. É a partir dessa categoria
principal que avanço para o aprofundamento pelo método dos 5 Porquês,
descrito no arquivo `cinco_porques.md` desta base de conhecimento.

## Referências bibliográficas

1. ROONEY, James J.; VANDEN HEUVEL, Lee N. Root Cause Analysis for
   Beginners. *Quality Progress*, v. 37, n. 7, p. 45-53, jul. 2004.
2. ILIE, Gabriela; CIOCOIU, Cristian Nicolae. Application of Fishbone
   Diagram to Determine the Risk of an Event with Multiple Causes.
   *Management Research and Practice*, v. 2, n. 1, p. 1-20, 2010.
