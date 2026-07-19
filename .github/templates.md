# Templates do GitHub

Guia dos templates de Issues (`.github/ISSUE_TEMPLATE/`) e Pull Requests
(`.github/pull_request_template.md`) do projeto.

## 📋 Templates de Issues

### 🚀 Feature Request (`feature.yml`)
Use para propor novas funcionalidades. Label: `feature`.

**Quando usar:**
- Adicionar nova funcionalidade ao agente/backend/frontend
- Implementar novo módulo
- Expandir capacidades existentes

**Campos obrigatórios:**
- Contexto
- Escopo
- Critérios de Aceite
- Categoria
- Milestone

---

### 🐛 Bug Report (`bug_report.yml`)
Use para reportar bugs ou comportamentos incorretos. Label: `bugfix`.

**Quando usar:**
- Sistema não funciona como esperado
- Erro ou crash
- Comportamento incorreto

**Campos obrigatórios:**
- Descrição do Bug
- Passos para Reproduzir
- Comportamento Esperado
- Comportamento Atual
- Severidade
- Componente Afetado

---

### 📚 Documentation (`documentation.yml`)
Use para melhorias ou adições à documentação. Label: `docs`.

**Quando usar:**
- Criar nova documentação
- Atualizar documentação existente
- Melhorar clareza da documentação

**Campos obrigatórios:**
- Contexto
- Escopo
- Tipo de Documentação

---

### 🔧 Chore/Maintenance (`chore.yml`)
Use para tarefas de manutenção, configuração ou refatoração. Label: `chore`.

**Quando usar:**
- Atualizar dependências
- Configurar ferramentas
- Refatorar código
- Melhorar CI/CD
- Tarefas de limpeza

**Campos obrigatórios:**
- Contexto
- Escopo
- Critérios de Aceite
- Tipo de Tarefa

---

### 💬 General Issue (`general.yml`)
Use para issues que não se encaixam nas outras categorias. Sem label fixa.

**Quando usar:**
- Discussões gerais
- Questões que não se encaixam em outras categorias
- Propostas de melhoria geral

---

## 📝 Template de Pull Request

O template de PR (`.github/pull_request_template.md`) é aplicado
automaticamente ao criar uma nova Pull Request — mesmo conteúdo do template
descrito em `specs/gitflow.md` § Convenção de Pull Requests.

**Seções do template:**
- **Contexto**: qual milestone/issue isso resolve
- **O que mudou**: lista curta das mudanças
- **Como testar**: comando(s) pra verificar localmente
- **Checklist**: CI verde, critérios de aceitação conferidos, `docs/prompts.md` atualizado
- **Closes #**: issue(s) fechada(s) por este PR

---

## 🎯 Boas Práticas

### Para Issues

1. **Seja específico**: Descreva claramente o problema ou funcionalidade
2. **Forneça contexto**: Explique por que a issue é necessária
3. **Defina critérios de aceite**: Como validar que está completo
4. **Referencie documentação**: Link para `specs/`/`docs/` relevantes
5. **Use as labels de tipo + etapa** (ver `docs/gitflow.md` § Labels de etapa)

### Para Pull Requests

1. **Título descritivo**: `<tipo>(<escopo>): <descrição>` (Conventional Commits, ver `specs/gitflow.md`)
2. **Descrição completa**: Explique o que mudou e por quê
3. **Passos de teste**: Facilite a revisão
4. **Link issues**: Use "Closes #123" para fechar automaticamente
5. **Checklist completo**: Marque todos os itens antes de solicitar revisão

---

## 📚 Referências

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Convenção de Gitflow do projeto](../specs/gitflow.md)
- [Estrutura do Projeto](../specs/structure.md)
- [Stack Tecnológica](../specs/tech.md)
- [Plano operacional (milestones, branches, issues)](../docs/gitflow.md)

---

## 🔄 Atualizando Templates

Para atualizar os templates:

1. Edite os arquivos `.yml` em `.github/ISSUE_TEMPLATE/`
2. Edite `.github/pull_request_template.md` para o template de PR
3. Teste criando uma nova issue/PR
4. Commit e push das alterações

**Nota**: Mudanças nos templates só afetam novas issues/PRs, não as existentes.
