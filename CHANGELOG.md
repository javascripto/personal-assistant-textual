# Changelog

Todas as mudanças relevantes do projeto são registradas aqui. As entradas são
organizadas por área de produto, não pela ordem em que foram implementadas.

## Não lançado

### Demonstração da aplicação

- README com thumbnail clicável para a demonstração com música no YouTube.
- Captura real de terminal em Asciinema, com leitura contínua da saída e
  verificações de SQLite, XLSX, backup e encerramento da sessão.
- Roteiro explora a TUI antes dos comandos de desenvolvimento do Makefile.
- Renderização MP4 1080p, 30 fps, com capítulos e indicação dos atalhos.
- Versão opcional com trilha retrô sintetizada localmente, volume discreto e
  fades; preserva a versão silenciosa e copia o vídeo sem recodificação.
- Grupo opcional `demo`, comandos Make e ações de VS Code/Codex para gerar,
  assistir e validar a demonstração.
- Base temporária isolada; o roteiro só substitui a captura final após todas
  as verificações passarem.

### Aplicação e fluxo de tarefas

- Confirmação de criação e edição com `Ctrl+Enter` na descrição multilinha.
- Atualização do relógio tolera a remoção do cabeçalho no encerramento da TUI.
- Criada a TUI **Personal Assistant** com Python, Textual e SQLite.
- Implementados filtros para todas, pendentes e concluídas.
- Adicionada ordenação por data crescente ou decrescente, persistida entre
  execuções.
- Implementados atalhos para criar, editar, excluir, alternar status, ordenar,
  exportar, trocar tema, abrir a palette e sair.
- Incluída confirmação antes da exclusão de uma tarefa.
- Preservada a tarefa selecionada depois de alternar seu status, quando ainda
  estiver visível no filtro atual.
- Corrigida a navegação entre abas: as setas continuam nas abas até o próximo
  `Tab` mover o foco para outro controle.

### Detalhes e edição

- Adicionada descrição longa persistente para cada tarefa.
- A edição agora oferece `TextArea` ampliado, com altura responsiva e botões de
  confirmação e cancelamento sempre visíveis.
- `Enter` abre detalhes em modo leitura, exibindo título, tag, status, criação
  e descrição.
- A tela de detalhes permite abrir a edição por `e` ou pelo botão **Editar**.

### Interface e acessibilidade

- Reproduzido o tema retrô inspirado em Clipper/QBasic/DOS: fundo escuro,
  cabeçalho e seleção azuis, tabela cyan e indicadores de status coloridos.
- O relógio foi posicionado à direita do cabeçalho azul da aplicação.
- A aplicação passou a ocupar toda a largura horizontal disponível do terminal.
- Atalhos exibidos no rodapé têm teclas destacadas e quebram em múltiplas linhas
  em terminais estreitos, sem ocultar comandos.
- Incluído atalho `q` para sair no rodapé.

### Temas

- Registrado `personal-assistant-retro` como tema padrão.
- Integrada a command palette nativa do Textual para seleção de temas.
- Temas passam a ser aplicados a toda a TUI e são persistidos no SQLite.
- Adicionado atalho `t` para alternar para o próximo tema disponível.

### Dados e exportação

- Implementado esquema SQLite para título, tag, descrição, status, criação e
  conclusão.
- Adicionada migração aditiva da coluna `description`, compatível com bancos
  existentes.
- Criada exportação XLSX com status, datas, tag, título e descrição.
- Substituídas tarefas de seed por exemplos genéricos anonimizados.
- Adicionado `make seed`, que inclui somente seeds ausentes e não duplica dados.
- `make seed` cria backup SQLite consistente com timestamp antes de alterar uma
  base existente.

### Qualidade e ferramentas

- Adotados `uv`, Ruff, Black, mypy estrito, BasedPyright estrito e pytest.
- Configurado limite de 80 colunas para Ruff, Black e a régua do VS Code.
- Adicionado `pyrightconfig.json` para rejeitar tipos desconhecidos e
  parcialmente desconhecidos.
- Tipadas explicitamente as fronteiras dinâmicas de `DataTable` do Textual.
- Criado `Makefile` com comandos de instalação, lint, formatação, testes,
  verificação, execução, seed e limpeza de caches.
- Configurados VS Code, Pylance, tarefas de editor e extensões recomendadas.
- Configuradas ações do Codex Desktop para verificar, testar, formatar, lintar,
  executar a TUI, popular o seed e limpar caches.

### Documentação e convenções

- Criado README com arquitetura, requisitos, atalhos, temas, persistência e
  fluxo de desenvolvimento.
- Criado `AGENTS.md` com regras de tipagem explícita, testes, migrações,
  segurança de dados e qualidade obrigatória.
- Adicionado este changelog para apoiar futuros commits por área funcional.
