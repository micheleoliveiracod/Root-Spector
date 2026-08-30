# Design system, Root-Spector (frontend)

Este documento descreve a linguagem visual usada em `src/`, alinhada à
identidade visual da marca (logo, favicon, `README.md`): superfície do
produto clara e neutra, roxo cheio reservado ao botão de ação, nunca como
preenchimento de área grande, e o semáforo dos indicadores como o único
elemento colorido de peso. A premissa é que quem usa o sistema está no
piso de produção, respondendo perguntas sobre o lote no meio do turno,
muitas vezes sem familiaridade com software: alvos grandes (48 pixels de
altura mínima), cada elemento com uma única forma reconhecível, e nenhuma
informação depende só da cor.

## Onde vive

- `src/styles/tokens.css` — todas as CSS custom properties (cores,
  tipografia, altura de controle, raio de borda, sombra). Único lugar com
  valores de cor hardcoded; todo o resto do CSS consome `var(--token)`.
- `src/index.css` — estilos globais e classes utilitárias (`.card`,
  `.badge`, `.mensagem`, `.estado`, `.progresso`, `.qa-list`, `.callout`,
  `.alert`, `.actions`, etc.), importa `tokens.css`.
- `src/statusBadge.ts` — traduz um valor de classificação/risco vindo da
  API (ex. `"CRITICAL"`, `"LOW_RISK"`) para o que o operador vê:
  `badgeClass()` devolve a classe de badge (`badge--ok` / `badge--warn` /
  `badge--critical` / `badge--neutral`), `estadoLote()` devolve a palavra
  do estado, a ação recomendada e a classe de `.estado` correspondente.

## Paleta e tema

Superfície única, clara e neutra (`color-scheme: light` em `tokens.css`),
não segue o tema do sistema operacional. Nenhum componente decide cor por
conta própria, todos leem os tokens (`--paper`, `--ink`, `--accent`,
etc.), então a paleta muda sem tocar em `index.css` ou nos componentes.
`.on-dark` é uma classe utilitária à parte, reservada à faixa quase preta
da marca (banner, README, documentação), não usada dentro do produto.

| Token | Uso |
|---|---|
| `--paper` / `--paper-raised` / `--paper-sunken` | fundo da página / fundo dos cards / campos e cabeçalho de tabela |
| `--ink` / `--ink-soft` | texto principal / texto secundário |
| `--line` / `--line-soft` | bordas e divisores |
| `--accent` / `--accent-ink` / `--accent-soft` | cor de marca (botão primário, eyebrow, callout, links de relatório) |
| `--accent-deep` / `--accent-border` | texto sobre `--accent-soft` / borda discreta em acento |
| `--accent-art` | reservado à arte da logo e às faixas escuras (`.on-dark`), sem contraste suficiente sobre branco pra uso em texto/borda |
| `--accent-hover` / `--accent-active` | estado de hover / clique do botão primário |
| `--control-height` / `--field-height` | altura mínima de botão (48px) / campo de resposta (52px) |
| `--control-border` / `--control-border-strong` | borda padrão / borda em hover de campos e botão secundário |
| `--disabled-bg` / `--disabled-fg` | fundo e texto de botão desabilitado |
| `--shadow` / `--shadow-lg` | sombra sutil dos cards |

### Cores "semáforo"

Nunca vermelho/amarelo/verde saturados, sempre fundo pastel, borda na
mesma família de cor e texto legível, pra não competir com o resto da
interface nem parecer um alerta de sistema operacional. A leitura nunca
depende só da cor: o ponto sólido em `.badge::before` e o quadrado sólido
em `.estado::before` reforçam o estado mesmo pra quem não distingue bem
as cores:

| Token (bg/border/fg) | Significado | Usado em |
|---|---|---|
| `--ok-bg` / `--ok-border` / `--ok-fg` | aceitável / baixo risco | `badge--ok`, `estado--ok`, `alert--ok` |
| `--warn-bg` / `--warn-border` / `--warn-fg` | atenção / risco médio | `badge--warn`, `estado--warn`, `alert--warn` |
| `--critical-bg` / `--critical-border` / `--critical-fg` | crítico / alto risco | `badge--critical`, `estado--critical`, `alert--critical` |
| `--neutral-bg` / `--neutral-border` / `--neutral-fg` | classificação não mapeada | `badge--neutral`, `estado--neutral` |

`statusBadge.ts` é o único lugar que decide qual badge ou estado usar a
partir do valor vindo da API — se um novo valor de classificação/risco
for adicionado no backend, o mapeamento é ajustado ali, não em cada
componente. Onde a leitura importa mais que o dado técnico (ex. a lista
de lotes), o componente usa `estadoLote()` e mostra a palavra do estado
em `.estado`, com o código técnico original (`classification` e
`risk_prediction`) abaixo em `.estado-codigo`, pra quem confere com o
backend sem perder a leitura rápida.

## Tipografia

Duas famílias, carregadas via Google Fonts em `index.html`, cada uma com
um papel fixo:

- **Sans** (`--font-sans`, Inter) — corpo do texto (`body`, parágrafos,
  textarea, botões) e títulos (`h1`, `h2`, peso 500). `--font-serif`
  aponta pra `--font-sans`, mantido só por compatibilidade com o restante
  do CSS que já referenciava esse token.
- **Mono** (`--font-mono`, JetBrains Mono) — rótulos curtos em caixa alta
  com letter-spacing: `.eyebrow`, `h3`, cabeçalho de tabela, `.categoria`
  nas listas de pergunta/resposta, badges, links de relatório, dado
  (identificador de lote, parâmetro, unidade). Sinaliza "metadado", não
  texto de leitura corrida.

## Padrões de layout

- `.page` — largura máxima 720px, centralizado; a interface é uma coluna
  única, sem sidebar/grid.
- `.card` + `.section` — todo bloco de conteúdo (lista de lotes, pergunta
  atual, revisão, relatório) é um `.card` com `.section` para o
  espaçamento vertical interno (`gap: 14px`); cards empilhados usam
  `.card + .card` para o espaçamento entre eles.
- `.masthead` — cabeçalho fixo da página (`eyebrow` + `h1` + `.dek`),
  presente em toda tela via `App.tsx`.
- `.actions` — container de botões ao fim de um card (`gap: 10px`).
- `.qa-list` — lista de pergunta/resposta (Ishikawa e 5 Porquês), cada
  item com um rótulo `.categoria` em mono acima do texto.
- `.callout` — destaque de fundo `--accent-soft` para a categoria
  principal identificada na revisão.
- `.alert` / `.alert--critical` / `.alert--warn` / `.alert--ok` —
  mensagens de erro ou aviso (ex. LLM indisponível, resposta rejeitada).
- `.mensagem` — caixa de mensagem do sistema, faixa de título
  (`.faixa`) dizendo de quem é a fala e corpo (`.corpo`) com o texto em
  tamanho maior (`--text-question`). Nunca tem fundo roxo cheio, pra não
  ser confundida com botão. Usada em `PerguntaAtual.tsx` para a pergunta
  do agente.
- `.progresso` — barra fina mostrando quantas perguntas faltam
  (`indice`/`total`), acima da mensagem do sistema em `PerguntaAtual.tsx`.
- `.estado` / `.estado-codigo` — ver seção "Cores semáforo" acima.
- `.report-links` — links de relatório como "pills" (`border-radius:
  100px`, fundo `--accent-soft`).

## Botões

- **Padrão**: retângulo cheio de `--accent` com texto branco, altura
  mínima `--control-height` (48px). É o único elemento com fundo roxo
  cheio na tela, por isso não há dúvida sobre onde clicar — uma ação
  primária por tela (Responder, Investigar). `--accent-hover` /
  `--accent-active` marcam hover e clique.
- `.secondary`: fundo branco, borda de 2 pixels em `--control-border`,
  texto `--ink`, ação secundária.
- `.link`: texto sublinhado em `--accent-ink`, sem caixa, pra ações de
  saída (ex. baixar relatório).
- `:disabled`: fundo e texto em `--disabled-bg`/`--disabled-fg`, sem cor
  de ação, pra não parecer clicável.

## Adicionando um novo componente

1. Envolva o conteúdo em `<div className="card section">` (ou apenas
   `.card` se não precisar do espaçamento em coluna).
2. Use `h2`/`h3` para títulos — nunca defina `font-family` inline.
3. Se o componente exibir um valor de classificação/risco vindo da API,
   use `badgeClass()` (dado técnico) ou `estadoLote()` (leitura para o
   operador) de `statusBadge.ts` — não crie uma nova cor.
4. Qualquer cor nova (fundo, texto, borda) deve ser adicionada como token
   em `tokens.css`, nunca como valor hardcoded no componente ou em
   `index.css`.
5. Nenhum controle interativo (botão, campo, link de ação) deve ter menos
   de 48 pixels de altura, ver `--control-height` / `--field-height`.
