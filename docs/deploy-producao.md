# Deploy em produção: Render, Vercel e n8n

Passo a passo de configuração do backend (Render), do frontend (Vercel) e
do workflow de resumo diário (n8n Cloud), mais o que cada guardrail de
segurança já implementado protege de fato e o que fica fora do escopo
deste projeto. Contexto e decisões de arquitetura completas em
`specs/deploy-producao/plano.md`.

## 1. Backend no Render

**Serviço:** Web Service, plano gratuito, apontando para este repositório.

- **Build command:** `pip install -e .`
- **Start command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

**Variáveis de ambiente**, no painel do Render (Environment):

| Variável | Valor |
|---|---|
| `LLM_PROVIDER` | `google_genai` (ou o provedor principal escolhido) |
| `LLM_MODEL` | `gemini-2.5-flash` |
| `GOOGLE_API_KEY` | chave real |
| `GROQ_API_KEY`, `DEEPSEEK_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` | chaves reais dos fallbacks configurados, em branco os que não forem usados |
| `DATABASE_URL` | string de conexão do Azure Database for PostgreSQL, com `sslmode=require` |
| `CORS_ALLOWED_ORIGINS` | domínio real do Vercel, por exemplo `https://root-spector.vercel.app` |
| `INTERNAL_API_KEY` | um valor aleatório longo, gerado uma vez (por exemplo `openssl rand -hex 32`) |
| `LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT` | opcionais, se o rastreamento do LangSmith for usado em produção |

`BIOTECPREDICT_DB_PATH` não precisa ser definida à parte: o arquivo
`data/biotecpredict.db` é somente leitura e embarca junto com o deploy.

## 2. Frontend no Vercel

**Build:** framework Vite detectado automaticamente, diretório raiz
`frontend/`.

**Variáveis de ambiente**, no painel do Vercel (Settings → Environment
Variables):

| Variável | Valor |
|---|---|
| `VITE_API_URL` | domínio público do backend no Render, por exemplo `https://root-spector.onrender.com` |
| `VITE_API_KEY` | o mesmo valor de `INTERNAL_API_KEY` definido no Render |

Sem essas duas variáveis, o frontend aponta para `http://localhost:8000`
e não envia nenhuma chave, o comportamento de desenvolvimento local
(`frontend/src/api.ts`).

## 3. Workflow no n8n Cloud

Seguir `docs/fase02/low-code/construcao-workflow-n8n.md` para a
construção completa. Dois ajustes específicos de produção, no nó HTTP
Request:

- **URL:** o domínio público do backend no Render, por exemplo
  `https://root-spector.onrender.com/api/relatorios/resumo-diario`.
- **Headers:** adicionar um cabeçalho `X-API-Key` com o mesmo valor de
  `INTERNAL_API_KEY` definido no Render, na seção "Headers" do nó HTTP
  Request (aba "Send Headers" → "Add Header").

## 4. O que cada guardrail protege

| Guardrail | Onde | Protege contra |
|---|---|---|
| `CORS_ALLOWED_ORIGINS` restrito ao domínio do Vercel | `backend/main.py` | Um site em outro domínio fazendo requisições à API pelo navegador de alguém que tenha a aba aberta. Não afeta chamadas feitas fora de um navegador (n8n, curl, scripts), CORS é uma regra aplicada pelo navegador, não pelo servidor. |
| `INTERNAL_API_KEY` (`X-API-Key`) | `backend/main.py::exigir_api_key` | Acesso não autenticado às rotas de lotes, investigações e resumo diário. Sem a chave correta, a requisição recebe HTTP 401 antes de tocar em qualquer lógica do agente. `relatorio.pdf` e `/reports` ficam de fora, propositalmente, para o link do e-mail continuar clicável. |
| Limite de taxa (20 requisições por minuto por IP) | `backend/main.py::limitar_taxa` | Um único IP (por engano ou abuso) fazendo uso muito acima do esperado para até 2 operadores simultâneos. Acima do limite, a requisição recebe HTTP 429 sem chegar a chamar o LLM, protegendo o consumo de créditos dos provedores. |
| Checkpointer e `eventos_log` em Postgres quando `DATABASE_URL` estiver definida | `graph.py`, `config.py` | Perda de estado (investigações em andamento, log estruturado) no ciclo de dormir e acordar do Render free tier. Sem isso, uma investigação em andamento se perderia toda vez que o serviço dormisse. |

## 5. O que esses guardrails não cobrem

Nenhuma configuração acima é proteção contra um ataque de negação de
serviço distribuído (DDoS) de verdade, com muitos endereços de IP
diferentes. O limite de taxa é contado por IP: um atacante com muitos IPs
consegue somar bem mais que 20 requisições por minuto no total, mesmo
respeitando o limite em cada IP individualmente. Proteção real contra
DDoS exige uma camada de rede dedicada (CDN/WAF, por exemplo Cloudflare
na frente do domínio), fora do escopo gratuito deste projeto de estudo.

O contador de limite de taxa também vive em memória, dentro do processo
do backend. Isso é suficiente porque o plano gratuito do Render roda uma
única instância; um deploy com múltiplas instâncias em paralelo
precisaria de um contador compartilhado (por exemplo Redis) para o limite
valer de verdade entre todas elas.

Dentro desse escopo, o que as configurações acima cobrem de fato é:
acesso não autenticado à API, uso indevido ou excessivo por um cliente
específico (inclusive um erro de configuração no próprio n8n ou
frontend, chamando a API em loop), e perda de estado no ciclo de sono do
Render, os riscos reais para um projeto de estudo hospedado em camadas
gratuitas, não um ataque coordenado de larga escala.

## 6. Limitações conhecidas

- **Render, camada gratuita:** o serviço dorme depois de cerca de 15
  minutos sem tráfego; o primeiro pedido depois disso leva de alguns
  segundos a cerca de um minuto para responder.
- **Azure Database for PostgreSQL, camada gratuita:** válida por 12
  meses a partir da criação da conta, depois passa a ser cobrada
  normalmente.
