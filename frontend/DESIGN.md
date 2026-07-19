# Design system — Root-Spector (frontend)

Este documento descreve a linguagem visual usada em `src/`. A referência
original é a mesma dos artefatos HTML produzidos para a apresentação e o
mapeamento de processo do projeto (`docs/apresentacao.html`,
`docs/mapeamento-processo.html`, `docs/fluxo-tecnico-agente.html`,
`docs/checklist-fluxo.html`): elegante, minimalista, tipografia editorial,
cores de status em tons pastel.

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

Claro/escuro via `@media (prefers-color-scheme: dark)` em
`tokens.css` — nenhum componente decide cor por conta própria, todos leem
os tokens (`--paper`, `--ink`, `--accent`, etc.), então o tema muda sem
tocar em `index.css` ou nos componentes.

| Token | Uso |
|---|---|
| `--paper` / `--paper-raised` | fundo da página / fundo dos cards |
| `--ink` / `--ink-soft` | texto principal / texto secundário |
| `--line` | bordas e divisores |
| `--accent` / `--accent-ink` / `--accent-soft` | cor de marca (botão primário, eyebrow, callout, links de relatório) |
| `--shadow` | sombra sutil dos cards |

### Cores "semáforo"

Nunca vermelho/amarelo/verde saturados — sempre fundo pastel + texto legível
na mesma família de cor, para não competir com o resto da interface nem
parecer um alerta de sistema operacional:

| Token (bg/fg) | Significado | Usado em |
|---|---|---|
| `--ok-bg` / `--ok-fg` | aceitável / baixo risco | `badge--ok` |
| `--warn-bg` / `--warn-fg` | atenção / risco médio | `badge--warn` |
| `--critical-bg` / `--critical-fg` | crítico / alto risco | `badge--critical`, `.alert--critical` |
| `--neutral-bg` / `--neutral-fg` | classificação não mapeada | `badge--neutral` |

`statusBadge.ts` é o único lugar que decide qual badge usar a partir do
valor vindo da API — se um novo valor de classificação/risco for
adicionado no backend, o mapeamento é ajustado ali, não em cada
componente.

## Tipografia

Três famílias, cada uma com um papel fixo (mesmo padrão dos artefatos
HTML da apresentação):

- **Serif** (`--font-serif`, Charter) — títulos (`h1`, `h2`): dá o tom
  editorial/relatório em vez de "dashboard genérico".
- **Mono** (`--font-mono`) — rótulos curtos em caixa alta com
  letter-spacing: `.eyebrow`, `h3`, cabeçalho de tabela, `.categoria` nas
  listas de pergunta/resposta, badges, links de relatório. Sinaliza
  "metadado", não texto de leitura corrida.
- **Sans** (`--font-sans`) — corpo do texto (`body`, parágrafos, textarea,
  botões).

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

- Padrão: fundo `--accent`, texto branco — ação primária (Responder,
  Voltar à lista de lotes).
- `.secondary`: fundo transparente, borda `--line` — ação secundária
  (Pedir ajuste).

## Adicionando um novo componente

1. Envolva o conteúdo em `<div className="card section">` (ou apenas
   `.card` se não precisar do espaçamento em coluna).
2. Use `h2`/`h3` para títulos — nunca defina `font-family` inline.
3. Se o componente exibir um valor de classificação/risco vindo da API,
   use `badgeClass()` de `statusBadge.ts` — não crie uma nova cor.
4. Qualquer cor nova (fundo, texto, borda) deve ser adicionada como token
   em `tokens.css` (com a variante dark correspondente), nunca como valor
   hardcoded no componente ou em `index.css`.
