# Personal Assistant TUI

Gerenciador de tarefas para terminal, implementado em Python, SQLite e
[Textual](https://textual.textualize.io/). O projeto reproduz a linguagem visual
retrô de uma referência Clipper/QBasic/DOS: fundo escuro, bordas e cabeçalho
azuis, tabela em cyan, seleção azul, status colorido e operação prioritária por
teclado.

Consulte o [CHANGELOG.md](CHANGELOG.md) para as entregas agrupadas por área.

O escopo foi consolidado a partir do chat de implementação fornecido no início do
trabalho. A referência visual não é distribuída neste repositório, e o seed usa
apenas tarefas genéricas anonimizadas.

## Demonstração

Há uma demonstração interativa em
[`docs/recordings/personal-assistant-demo.cast`](docs/recordings/personal-assistant-demo.cast).
Ela percorre os comandos do Makefile e as funções centrais da TUI em uma base
temporária, sem modificar os dados locais. Para assisti-la:

```sh
asciinema play docs/recordings/personal-assistant-demo.cast
```

O comando `make record-demo` recria a gravação quando `asciinema` e `expect`
estiverem instalados. Veja as instruções completas em `docs/recordings/`.

## Recursos

- SQLite persistente em `data/personal_assistant.db`.
- Seed inicial com dez tarefas genéricas anonimizadas, somente na criação de uma
  base vazia.
- Tabela com status, data, tag e título.
- Filtros **Todos**, **Pendentes** e **Concluídos**.
- Ordenação de data crescente ou decrescente, persistida entre execuções.
- Criação, edição, consulta de detalhes e exclusão confirmada de tarefas.
- Status pendente (`○`) e concluído (`✓`) com alternância por teclado.
- Descrição longa de tarefa em `TextArea`, persistida no SQLite.
- Tela de detalhes em modo leitura, com título, tag, status, criação e
  descrição; ela permite abrir a edição sem perder a tarefa selecionada.
- Exportação de todas as tarefas para XLSX, incluindo descrição e data de
  conclusão.
- Relógio no cabeçalho da aplicação.
- Tema retrô padrão, temas nativos do Textual e persistência da seleção de tema.
- Layout responsivo: a TUI ocupa toda a largura do terminal e o rodapé quebra
  atalhos em linhas adicionais quando necessário.

## Requisitos e execução

É necessário Python 3.12+ e [uv](https://docs.astral.sh/uv/).

```sh
make install
make run
```

Dados ficam em `data/personal_assistant.db` e os arquivos XLSX em `exports/`.
Os dois caminhos são ignorados pelo Git e preservados por `make clear`.

Para inserir novamente as tarefas genéricas sem apagar ou duplicar tarefas já
existentes, execute:

```sh
make seed
```

Quando o SQLite já existir, esse comando cria antes uma cópia consistente em
`data/personal_assistant.backup-AAAAMMDD-HHMMSS.db`.

## Atalhos

| Atalho | Ação |
| --- | --- |
| `n` | Criar tarefa |
| `e` | Editar título, tag e descrição longa da tarefa selecionada |
| `Enter` | Abrir detalhes da tarefa selecionada |
| `e` nos detalhes | Abrir a edição da tarefa exibida |
| `d` | Excluir a selecionada, pedindo confirmação |
| `Space` | Alternar entre pendente e concluída |
| `o` | Alternar ordenação por data crescente/decrescente |
| `x` | Exportar todas as tarefas para XLSX |
| `t` | Aplicar o próximo tema disponível |
| `Ctrl+P` | Abrir a command palette nativa |
| `q` | Sair |
| `Esc` | Fechar modal, detalhes ou voltar |

Use `Tab` para chegar às abas. As setas navegam entre elas sem transferir o foco
para a tabela; pressione `Tab` novamente para mover para o próximo controle.
Na tabela, `↑`/`↓`, mouse e atalhos nativos do Textual funcionam normalmente.

Ao alterar o status, a seleção é restaurada na mesma tarefa quando ela continuar
visível no filtro atual. Isso evita o salto inesperado para a primeira linha.

## Temas

`Ctrl+P` abre a command palette do Textual. Use **Select theme** para escolher o
tema retrô padrão (`personal-assistant-retro`) ou outro tema disponível. A troca
é aplicada a toda a interface e gravada no SQLite para a próxima execução.

O atalho `t` avança pela mesma lista de temas e mostra uma notificação com o tema
escolhido.

## Arquitetura

```text
src/personal_assistant/
├── app.py       # TUI, modais, detalhes, atalhos e temas
├── database.py  # esquema, migrações SQLite e operações de tarefas
├── models.py    # tipos de domínio tipados
├── exporter.py  # geração de XLSX com openpyxl
├── seed.py      # tarefas iniciais genéricas e anonimizadas
└── personal_assistant.tcss  # aparência retrô e layout responsivo
```

O esquema de tarefas contém `title`, `tag`, `description`, `status`, `created_at`
e `completed_at`. A migração de `description` é aditiva: bases já existentes são
atualizadas sem apagar tarefas ou configurações.

## Desenvolvimento e qualidade

| Comando | Finalidade |
| --- | --- |
| `make install` | Instalar dependências bloqueadas no `uv.lock` |
| `make lint` | Executar Ruff, mypy e BasedPyright estritos |
| `make format` | Formatar com Ruff e Black |
| `make test` | Executar testes com pytest |
| `make check` | Validar formato, lint, tipos e testes sem editar arquivos |
| `make run` | Iniciar a TUI |
| `make seed` | Fazer backup e inserir tarefas genéricas ausentes no banco |
| `make clear` | Limpar apenas caches e relatórios gerados |

O gate `make check` é obrigatório. Ele cobre persistência, migração de SQLite,
exportação XLSX, atalhos, foco entre abas, preservação de seleção, detalhes,
temas e adaptação do rodapé.

### Limite de 80 colunas

Ruff e Black estão configurados para 80 colunas. O VS Code exibe régua na coluna
80, aplica formatação ao salvar e usa Pylance em modo estrito. O
`pyrightconfig.json` força os diagnósticos estritos de tipos parcialmente
desconhecidos, e BasedPyright os valida no `make lint` e no `make check`. As
tarefas, configurações e extensões recomendadas ficam em `.vscode/`.

No Codex Desktop, `.codex/environments/environment.toml` disponibiliza botões
para verificar, testar, formatar, lintar, executar a TUI e limpar caches.
