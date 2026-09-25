# Demonstração gravada

`personal-assistant-demo.cast` é uma gravação Asciinema do uso do Makefile e da
TUI. Ela executa `make help`, `make format` e `make check` e, em uma base SQLite
temporária, demonstra ordenação, criação, edição, detalhes, alternância de
status, navegação por abas, tema, exportação XLSX e exclusão confirmada.

Para reproduzir localmente, instale `asciinema` e `expect`, então execute:

```sh
make record-demo
asciinema play docs/recordings/personal-assistant-demo.cast
```

O roteiro em `scripts/record_demo.expect` cria e remove seu próprio diretório
temporário. Ele não altera `data/` nem `exports/` do projeto.
