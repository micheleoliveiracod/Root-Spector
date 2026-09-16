# RAG (Retrieval-Augmented Generation)

Este documento descreve o mecanismo de RAG do Root-Spector: como a base
de conhecimento está organizada, como o chunking é feito, como os
embeddings são gerados, como o índice vetorial é construído e como a
recuperação por similaridade alimenta a recomendação de tratativa. O
código correspondente está em `root_cause_agent/rag.py`; o desenho
original da decisão está em `specs/fase02/design.md` (seção RAG).

## Por que RAG

A recomendação de tratativa não é gerada a partir de conhecimento geral
do modelo de linguagem. Ela é gerada a partir de um conjunto curado de
documentos de referência, recuperados por similaridade semântica de
acordo com a categoria de causa raiz identificada na investigação. Esse
desenho tem dois objetivos: reduzir a chance de o modelo inventar uma
prática de tratativa sem lastro em nenhuma fonte, e tornar a recomendação
rastreável até documentos específicos, exigência que se conecta
diretamente à governança de dados e à legislação de boas práticas de
fabricação descritas em `data/base_conhecimento/compliance_governanca_dados.md`
e `data/base_conhecimento/bpf_anvisa.md`.

## Organização da base de conhecimento

Os documentos curados ficam em `data/base_conhecimento/`, um arquivo
Markdown por tópico. A base contém 11 arquivos, divididos em dois grupos:

**Prática por categoria do diagrama de Ishikawa (6M)**, um arquivo por
categoria, com orientação operacional específica de bioprocesso e
recomendação de tratativa própria de cada categoria:

- `metodo.md`
- `maquina.md`
- `material.md`
- `mao_de_obra.md`
- `meio_ambiente.md`
- `medicao.md`

**Metodologia e legislação**, um arquivo por tema, cada um com seção
dedicada de referências bibliográficas reais no rodapé:

- `ishikawa.md`, o método do diagrama de causa e efeito em si
- `cinco_porques.md`, o método dos 5 Porquês
- `capa_pdca.md`, as metodologias CAPA e PDCA de estruturação de
  tratativa
- `bpf_anvisa.md`, a legislação brasileira de Boas Práticas de
  Fabricação (RDC 658/2022 e IN 36/2019)
- `compliance_governanca_dados.md`, governança e integridade de dados

Nenhum desses documentos é legislação oficial reproduzida na íntegra nem
substitui a leitura do texto legal original. São referências curadas,
escritas para orientar a formulação da recomendação de tratativa dentro
do escopo deste projeto.

## Chunking

O chunking é feito por `RecursiveCharacterTextSplitter`
(`langchain-text-splitters`), com `chunk_size=500` e `chunk_overlap=50`
(`root_cause_agent/rag.py`, constantes `CHUNK_SIZE` e `CHUNK_OVERLAP`).
Cada um dos 11 arquivos é lido por inteiro e dividido nesses blocos de até
500 caracteres, com sobreposição de 50 caracteres entre blocos
consecutivos para reduzir a chance de uma ideia ser cortada exatamente na
fronteira entre dois chunks.

O processo de indexação (`root_cause_agent/rag.py::_vector_store`)
percorre `data/base_conhecimento/*.md` em ordem alfabética, aplica o
splitter a cada arquivo e registra, para cada chunk gerado, o nome do
arquivo de origem como metadado (`fonte`). Esse metadado é o que permite
rastrear, mais tarde, de qual documento específico veio cada candidato
recuperado.

Reprocessando a base de conhecimento completa (11 arquivos), o resultado
observado foi:

| Arquivo | Chunks |
|---|---|
| bpf_anvisa.md | 27 |
| capa_pdca.md | 27 |
| cinco_porques.md | 25 |
| compliance_governanca_dados.md | 21 |
| ishikawa.md | 21 |
| maquina.md | 17 |
| mao_de_obra.md | 14 |
| meio_ambiente.md | 14 |
| metodo.md | 14 |
| material.md | 13 |
| medicao.md | 13 |
| **Total** | **206** |

O número de chunks por arquivo varia com o tamanho do texto: os arquivos
de metodologia e legislação, mais extensos por trazerem contexto teórico
e referências bibliográficas, geram mais chunks do que os arquivos de
orientação prática por categoria Ishikawa, mais curtos e diretos.

## Embedding

A geração de embeddings é feita por `GoogleGenerativeAIEmbeddings`
(`langchain-google-genai`), reaproveitando a mesma `GOOGLE_API_KEY`
configurada para o LLM principal do projeto. O modelo configurado é
`models/gemini-embedding-001`, que produz vetores de 3072 dimensões.

Esse modelo substitui `models/text-embedding-004`, citado na versão
original do desenho técnico em `specs/fase02/design.md`. Na validação
feita durante a implementação, a chamada ao modelo antigo retornou erro
404 (modelo não encontrado), confirmando que a Google descontinuou esse
identificador. A lista de modelos disponíveis para a API key deste
projeto, consultada via `client.models.list()`, mostrou
`models/gemini-embedding-001` como o único modelo estável com suporte a
`embedContent`, e o código foi ajustado para usá-lo.

Em ambiente de teste (`LLM_PROVIDER=fake`), o embedding real é
substituído por `DeterministicFakeEmbedding`
(`langchain_core.embeddings`), que gera vetores determinísticos sem
chamada de rede, na mesma lógica já aplicada ao LLM fake do projeto
(`root_cause_agent/fake_llm.py`). Isso garante que nenhum teste
automatizado da suíte (`tests/`) consuma quota da API real de embeddings.
Esse componente depende de `numpy` em tempo de execução, adicionado como
dependência de desenvolvimento em `pyproject.toml`.

A API gratuita da Google impõe um limite de 100 requisições de embedding
por minuto. Ao reprocessar os 206 chunks da base completa com o modelo
real em lotes de 80 textos, respeitando esse limite, a indexação dos 206
chunks foi concluída com sucesso, confirmando que o modelo configurado
está correto e operacional para o volume atual da base de conhecimento.

## Armazenamento vetorial

O armazenamento tem dois backends, no mesmo padrão dual já usado pelo
checkpointer do grafo (`graph.py::_criar_checkpointer`) e pelo log
estruturado em banco (`config.py::_HandlerBancoDeDados`): local por
padrão, Postgres quando `DATABASE_URL` estiver definida. A escolha é
feita em `_vector_store()` (`root_cause_agent/rag.py`), decorada com
`functools.lru_cache`, mesmo padrão de cache já usado por
`carregar_regras_setor()` em `root_cause_agent/config.py`: a decisão de
qual backend usar, e a consulta que ela dispara, acontece uma única vez
por processo.

**Sem `DATABASE_URL` (padrão em desenvolvimento):** `InMemoryVectorStore`
(`langchain_core.vectorstores`), mantido inteiramente em memória, sem
persistência em disco. Internamente, mantém um dicionário Python
(atributo `store`) que associa, a cada chunk indexado, um identificador
único, o vetor de embedding, o texto original do chunk e o metadado de
origem (`fonte`). O índice inteiro é reconstruído a cada novo processo, a
partir dos arquivos Markdown em `data/base_conhecimento/`, o que mantém a
base de conhecimento como única fonte de verdade, sem risco de o índice
vetorial divergir dos documentos que o originaram -- aceitável em
desenvolvimento, corpus pequeno.

**Com `DATABASE_URL` (produção):** `PGVector` (`langchain-postgres`),
sobre a mesma instância Postgres do checkpointer e do `eventos_log`, na
coleção `root_spector_base_conhecimento`. `PGVector` usa SQLAlchemy
internamente, que resolve um `postgresql://` puro para o driver
`psycopg2` (não instalado, a dependência real do projeto é `psycopg` v3);
`_url_para_sqlalchemy()` troca o esquema pra `postgresql+psycopg://`
antes de repassar a URL, senão a 1ª chamada falharia com
`ModuleNotFoundError`. Reindexar (chunking e chamadas
reais de embedding) a cada reinício do processo desperdiçaria custo e
latência para um corpus que não muda com frequência, então
`_vector_store_postgres()` compara um hash SHA-256 do conteúdo atual de
`data/base_conhecimento/*.md` contra o último hash persistido na tabela
`rag_indice_hash` (criada automaticamente na primeira execução):

- Hash igual (caso comum, corpus não mudou): a coleção já persistida é
  reaproveitada como está, nenhum embedding novo é gerado.
- Hash diferente (1ª execução contra esse banco, ou algum `.md` foi
  editado/adicionado/removido): a coleção é apagada e reconstruída do
  zero (`pre_delete_collection=True`), e o hash novo é gravado em
  `rag_indice_hash`.

Esse hash cobre a base inteira, não arquivo por arquivo -- qualquer
mudança em qualquer `.md` da base reindexa tudo, não só o arquivo
alterado, decisão deliberada por simplicidade: o corpus inteiro já é
pequeno o suficiente para uma reindexação completa caber dentro do limite
de requisições por minuto da API de embeddings (ver seção anterior).

A função `limpar_cache()` descarta o backend selecionado (o dicionário em
memória, ou a referência ao `PGVector` já aberto), forçando a escolha e a
consulta de novo na próxima chamada -- usada nos testes automatizados
para evitar que embeddings gerados por um provedor sejam reaproveitados
indevidamente numa consulta feita sob outra configuração de provedor.

## Recuperação

A recuperação é feita por `buscar_candidatos(categoria, resumo_nc, k=3)`,
que monta uma consulta textual combinando a categoria principal
identificada na investigação (Ishikawa) e um resumo da não conformidade,
e executa `similarity_search` sobre o índice vetorial. O resultado é uma
lista de `CandidatoRAG`, cada um com o texto do chunk recuperado e o nome
do arquivo de origem. Trata-se de busca por similaridade semântica real,
não correspondência textual exata: a consulta e os chunks são comparados
pela distância entre seus vetores de embedding, não por palavras-chave em
comum.

## Integração no grafo do agente

A recuperação ocorre no nó `pre_busca_rag`
(`root_cause_agent/nodes.py`), executado em paralelo ao loop dos 5
Porquês, a partir do momento em que a categoria principal já foi
identificada por `orquestrar_analise`. Por depender apenas da categoria
principal, e não da cadeia de 5 Porquês, esse nó não precisa aguardar a
conclusão da interação com o operador para levantar candidatos.

Os candidatos recuperados alimentam o nó `recomendar_tratativa`, que
combina a causa raiz e a narrativa produzidas ao final da investigação
com os trechos recuperados da base de conhecimento, e gera a
recomendação de tratativa final. As fontes usadas (nomes dos arquivos de
origem dos chunks recuperados) são registradas no campo
`Diagnostico.fontes_rag`, preservando a rastreabilidade entre a
recomendação e os documentos que a embasaram.

## Validação realizada

Além dos testes automatizados (`tests/test_rag.py`), que cobrem
recuperação nas 6 categorias Ishikawa usando embeddings determinísticos,
a base de conhecimento completa foi reprocessada manualmente com o
modelo de embedding real, e a recuperação por categoria foi conferida
contra o arquivo de origem esperado:

| Categoria | Fontes recuperadas (k=4) |
|---|---|
| Método | metodo.md, medicao.md |
| Máquina | maquina.md (4/4) |
| Material | material.md, medicao.md |
| Mão de obra | mao_de_obra.md, medicao.md |
| Meio ambiente | meio_ambiente.md (4/4) |
| Medição | medicao.md (4/4) |

A mistura pontual com `medicao.md` em algumas categorias é esperada: os
documentos de Método, Material e Mão de obra também mencionam parâmetros
de biosensor ao descrever como diferenciar causa raiz de erro de
medição, o que aproxima esses chunks, em termos de similaridade
semântica, dos chunks do próprio documento de Medição.
