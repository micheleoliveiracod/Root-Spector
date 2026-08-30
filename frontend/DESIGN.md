# Design system, Root-Spector (frontend)

Este documento descreve a linguagem visual usada em `src/`, alinhada à
identidade visual da marca (logo, favicon, `README.md`): superfície do
produto clara e neutra, roxo em pontos definidos (botão, foco, rótulo de
fase), nunca como preenchimento de área grande, e o semáforo dos
indicadores como o único elemento colorido de peso.

## Onde vive

- `src/styles/tokens.css` — todas as CSS custom properties (cores,
  tipografia, raio de borda, sombra). Único lugar com valores de cor
  hardcoded; todo o resto do CSS consome `var(--token)`.
- `src/index.css` — estilos globais e classes utilitárias (`.card`,
  `.badge`, `.qa-list`, `.callout`, `.alert`, `.actions`, etc.), importa
  `tokens.css`.
- `src/statusBadge.ts` — mapeia um valor de classificação/risco (ex.
  `"CRITICAL"`, `"LOW_RISK"`) para a classe de badge correspondente
  (`badge--ok` / `badge--warn` / `badge--critical` / `badge--neutral`).

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
| `--shadow` / `--shadow-lg` | sombra sutil dos cards |

### Cores "semáforo"

Nunca vermelho/amarelo/verde saturados, sempre fundo pastel, borda na
mesma família de cor e texto legível, pra não competir com o resto da
interface nem parecer um alerta de sistema operacional. A leitura nunca
depende só da cor, o ponto sólido em `.badge::before` reforça o estado
mesmo pra quem não distingue bem as cores:

| Token (bg/border/fg) | Significado | Usado em |
|---|---|---|
| `--ok-bg` / `--ok-border` / `--ok-fg` | aceitável / baixo risco | `badge--ok` |
| `--warn-bg` / `--warn-border` / `--warn-fg` | atenção / risco médio | `badge--warn` |
| `--critical-bg` / `--critical-border` / `--critical-fg` | crítico / alto risco | `badge--critical`, `.alert--critical` |
| `--neutral-bg` / `--neutral-border` / `--neutral-fg` | classificação não mapeada | `badge--neutral` |

`statusBadge.ts` é o único lugar que decide qual badge usar a partir do
valor vindo da API — se um novo valor de classificação/risco for
adicionado no backend, o mapeamento é ajustado ali, não em cada
componente.

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
- `.alert` / `.alert--critical` — mensagens de erro (ex. LLM
  indisponível).
- `.report-links` — links de relatório como "pills" (`border-radius:
  100px`, fundo `--accent-soft`).

## Botões

- Padrão: contorno em `--accent`, fundo transparente, texto
  `--accent-ink`, fundo `--accent-soft` no hover, ação primária
  (Responder, Voltar à lista de lotes). Nunca preenchimento de área
  grande, mesma regra da paleta como um todo.
- `.secondary`: fundo transparente, borda `--line`, texto `--ink`, ação
  secundária (Pedir ajuste).

## Adicionando um novo componente

1. Envolva o conteúdo em `<div className="card section">` (ou apenas
   `.card` se não precisar do espaçamento em coluna).
2. Use `h2`/`h3` para títulos — nunca defina `font-family` inline.
3. Se o componente exibir um valor de classificação/risco vindo da API,
   use `badgeClass()` de `statusBadge.ts` — não crie uma nova cor.
4. Qualquer cor nova (fundo, texto, borda) deve ser adicionada como token
   em `tokens.css` (com a variante dark correspondente), nunca como valor
   hardcoded no componente ou em `index.css`.
