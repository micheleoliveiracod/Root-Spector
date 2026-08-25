# Compliance e governança de dados

Entendo que uma investigação de causa raiz de não conformidade só tem
valor real se os dados em que ela se apoia, e os dados que ela própria
produz, forem confiáveis, rastreáveis e íntegros. Por isso trato
compliance e governança de dados não como um tópico à parte da minha
investigação, mas como um requisito estrutural dela, que atravessa desde
a leitura do biosensor até o diagnóstico final gerado.

## O que entendo por governança de dados

Governança de dados é a disciplina que define quem é responsável pelos
dados de uma organização, quais políticas e processos regem sua coleta,
armazenamento e uso, e quais estruturas técnicas garantem que essas
políticas sejam de fato cumpridas. Alhassan, Sammon e Daly, em revisão
da literatura acadêmica sobre o tema, mapeiam as atividades de governança
de dados em cinco domínios de decisão recorrentes na literatura: princípios
de dados, que definem o papel estratégico dos dados na organização;
qualidade de dados, que trata da precisão, completude e consistência dos
dados produzidos; metadados, que documentam origem, significado e
formato de cada dado; acesso a dados, que define quem pode consultar ou
alterar cada informação; e ciclo de vida dos dados, que trata de como os
dados são criados, mantidos, arquivados e eventualmente descartados. Uso
esses cinco domínios como referência conceitual para avaliar, de forma
crítica, onde a minha própria arquitetura de investigação já atende a
esse tipo de exigência e onde ainda depende de decisões tomadas fora do
escopo deste projeto, como o processo de qualidade real da planta que
consome o diagnóstico gerado.

Tallon, Ramirez e Short propõem, em artigo publicado no Journal of
Management Information Systems, uma distinção que considero especialmente
útil: governança de TI trata da infraestrutura técnica que sustenta os
sistemas de informação, enquanto governança de informação, ou governança
de dados, trata do próprio dado como artefato, independente da tecnologia
que o armazena. Essa distinção explica por que uma organização pode ter
uma infraestrutura de TI robusta e, ainda assim, sofrer com dados
inconsistentes, não rastreáveis ou de origem duvidosa: são duas
disciplinas relacionadas, mas não equivalentes. No meu domínio, aplico
essa distinção ao tratar como governança de dados propriamente dita, e
não como mero detalhe técnico, decisões como: de onde vem cada leitura de
biosensor usada na investigação, quem ou o quê gerou cada resposta que
compõe o diagnóstico, e como cada campo do diagnóstico final pode ser
rastreado até a evidência que o originou.

## Integridade de dados no meu domínio

No contexto regulatório de boas práticas de fabricação, a integridade de
dados costuma ser descrita através do princípio conhecido pela sigla
ALCOA, e em versões mais recentes ALCOA+: um dado íntegro deve ser
atribuível a quem o gerou, legível, contemporâneo ao evento que registra,
original ou cópia fiel do original, e preciso, com as extensões mais
recentes acrescentando que o dado também deve ser completo, consistente,
duradouro e disponível quando necessário. Considero esse princípio a
ponte natural entre governança de dados, como disciplina acadêmica de
sistemas de informação, e boas práticas de fabricação, como exigência
regulatória: ambos exigem, em essência, que seja possível responder, para
qualquer dado, de onde ele veio e se ele pode ser confiado.

Na minha investigação, esse princípio se traduz em decisões concretas de
arquitetura. O identificador do lote sob investigação nunca é escolhido
livremente pelo modelo de linguagem: ele vem do estado da investigação,
injetado de forma determinística, o que impede que uma instrução mal
intencionada embutida numa resposta do operador altere qual lote está
sendo consultado. Cada resposta do operador passa por uma camada de
validação determinística antes de qualquer julgamento de modelo, o que
mantém a decisão de fluxo da investigação fora do controle do modelo de
linguagem e sob controle de regras explícitas e auditáveis. E o
diagnóstico final preserva a cadeia completa de evidência, desde a
categoria principal do diagrama de Ishikawa até as fontes específicas da
base de conhecimento consultadas para formular a recomendação de
tratativa, o que permite reconstruir, a qualquer momento, o raciocínio
completo que levou àquela conclusão.

## Compliance como consequência da governança

Trato compliance, no meu domínio, como a consequência prática de uma
governança de dados bem estruturada, não como uma camada adicional
imposta sobre um sistema já pronto. Um sistema que sabe, para cada dado
que produz, de onde ele veio, quem ou o quê o gerou e como pode ser
verificado, está numa posição estrutural favorável para atender a
exigências regulatórias externas, sejam elas de boas práticas de
fabricação, sejam de qualquer outra natureza. Um sistema que não sabe
responder essas perguntas para seus próprios dados dificilmente
conseguirá demonstrar compliance de forma consistente, por mais completa
que seja a política escrita que o descreve. É essa relação entre
governança de dados como prática técnica e compliance como resultado
demonstrável que procuro manter presente em cada decisão de arquitetura
desta investigação.

## Relação com bioprocessos

Num bioprocesso, o dado bruto de biosensor, temperatura, pH, oxigênio
dissolvido, pressão e velocidade de agitação, é a evidência primária
sobre a qual toda a investigação se apoia, e é também o dado mais
suscetível a ruído e a falha de instrumentação, como discuto no arquivo
`medicao.md` desta base. Se a governança sobre esse dado bruto for frágil,
sem clareza de qual sensor gerou qual leitura, sem calibração
documentada, sem histórico acessível, a investigação de causa raiz herda
essa fragilidade e produz um diagnóstico que parece completo mas não é
verificável. Por isso trato a governança do dado de biosensor como
pré-condição da própria investigação, não como um tema paralelo a ela.

## O que preciso para elaborar a não conformidade

Para que o documento de não conformidade seja auditável, preciso que
cada dado usado na investigação carregue sua própria proveniência: de
qual lote e de qual janela de tempo vem cada leitura de biosensor
consultada, qual resposta do operador fundamentou cada categoria do
diagrama de Ishikawa e cada etapa dos 5 Porquês, e quais documentos
específicos da base de conhecimento curada embasaram a recomendação de
tratativa final. Não formulo a causa raiz nem a tratativa a partir de
conhecimento geral não rastreável, formulo a partir dessas fontes
específicas, e registro essas fontes no próprio diagnóstico. Espero que a
equipe de qualidade trate essa rastreabilidade como parte do critério de
aceitação do diagnóstico: um diagnóstico sem proveniência clara de cada
dado que o sustenta não deveria ser aceito como base para a decisão final
sobre o lote, independentemente da qualidade aparente da narrativa
apresentada.

## Referências bibliográficas

1. ALHASSAN, Ibrahim; SAMMON, David; DALY, Mary. Data Governance
   Activities: An Analysis of the Literature. *Journal of Decision
   Systems*, v. 25, n. 1, p. 64-75, 2016.
2. TALLON, Paul P.; RAMIREZ, Ronald V.; SHORT, James E. The Information
   Artifact in IT Governance: Toward a Theory of Information Governance.
   *Journal of Management Information Systems*, v. 30, n. 3, p. 141-178,
   2013.
