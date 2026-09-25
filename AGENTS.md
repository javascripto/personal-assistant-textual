# AGENTS.md

## Desenvolvimento

- Use `uv` para executar ferramentas Python; os comandos de trabalho ficam no
  `Makefile`.
- Uma alteração só está concluída depois de `make check` passar.
- Mantenha código Python formatado em, no máximo, 80 colunas. Ruff e Black são
  a fonte de verdade; o VS Code mostra uma régua na coluna 80.
- Preserve tipagem estrita: `mypy`, Pylance e BasedPyright devem continuar sem
  erros, inclusive de tipos parcialmente desconhecidos.

## Tipagem explícita

- Anote parâmetros, retornos, atributos de classe e variáveis cujo tipo não seja
  evidente para o analisador estático. Prefira `str | None` a `Optional[str]`.
- Não introduza `Any`, `# type: ignore` ou `cast` para silenciar diagnósticos.
  Um `cast` só é aceitável em uma fronteira dinâmica de biblioteca, com o tipo
  concreto declarado e uma justificativa curta no código.
- Modele dados persistidos com tipos de domínio explícitos. Para payloads com
  formato conhecido, use `TypedDict`; para entidades, use dataclasses tipadas.
- Preserve genéricos nas coleções e widgets. Não aceite tipos `Unknown`,
  parcialmente desconhecidos ou argumentos de tipo implícitos.
- Mantenha os testes tão tipados quanto o código de produção; eles também são
  verificados por mypy e BasedPyright.

## Dados e comportamento

- A base SQLite local em `data/` é dado do usuário: não a apague nem a recrie
  para aplicar mudanças de esquema. Faça migrações compatíveis.
- Preserve o tema retrô, o fluxo prioritário por teclado e os atalhos já
  documentados.
- `exports/` e os caches podem ser limpos com `make clear`; o comando não deve
  remover banco SQLite nem exportações XLSX.
- `make seed` deve permanecer idempotente: pode adicionar somente as tarefas
  genéricas ausentes, sem apagar nem duplicar dados locais, e deve criar backup
  SQLite com timestamp antes de modificar uma base existente.

## Mudanças e manutenção

- Toda mudança de comportamento deve incluir ou atualizar um teste automatizado
  que descreva o resultado esperado.
- Ao alterar persistência, crie migrações aditivas e testes de compatibilidade
  para bancos existentes.
- Mantenha README, atalhos, `Makefile`, tarefas do VS Code e ações do Codex
  consistentes quando uma mudança afetar o uso ou o fluxo de desenvolvimento.
- Prefira alterações pequenas e reversíveis; não altere funcionalidades já
  validadas sem uma necessidade explícita.

## Verificação

```sh
make format
make check
```
