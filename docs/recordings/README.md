# Demonstração gravada

São duas saídas da mesma sessão real de terminal:

- `personal-assistant-demo.cast`: captura reproduzível no Asciinema.
- `personal-assistant-youtube.mp4`: vídeo H.264, 1920×1080, 30 fps, com
  capítulos e atalhos em português, sem áudio. Renderiza as cores e o texto
  reais da captura; não é uma filmagem da janela nativa do Terminal.

A demo usa um workspace temporário e demonstra criação com descrição longa,
detalhes, edição, alternância de status, filtros, ordenação, temas, palette,
XLSX, cancelamento, exclusão e persistência. Depois mostra `make help`,
`make format`, `make check`, `make seed` com backup e `make clear`.

`demo-validation.json` registra as verificações de resultado. O roteiro
consulta SQLite e XLSX após as operações e exige que comandos e sessão
terminem com sucesso. `demo-chapters.json` contém os tempos usados no vídeo;
`youtube-chapters.txt` pode ser copiado para a descrição do YouTube.

Para reproduzir localmente, instale `asciinema` e execute:

```sh
make play-demo
```

Para gerar os dois arquivos novamente, instale `asciinema` e `ffmpeg` e use:

```sh
make build-demo
```

O `uv` instala as dependências opcionais do grupo `demo`. A renderização usa
a fonte Menlo do macOS. Para outros sistemas, adapte `FONT_PATH` em
`scripts/render_demo.py` para uma fonte monoespaçada local.

`make render-demo` refaz apenas o MP4; `make demo-check` valida os scripts com
mypy e BasedPyright estritos. MP4 e imagens de revisão são ignorados pelo Git.
Nenhum arquivo é enviado automaticamente ao YouTube ou ao asciinema.org.

### Versão com música

`personal-assistant-youtube-music.mp4` mantém o vídeo original e acrescenta
uma trilha instrumental retrô sintetizada localmente, sem samples ou músicas
de terceiros. O áudio tem volume discreto (-24 LUFS como alvo), estéreo AAC,
fade de entrada e saída. A versão sem áudio permanece intacta.

Para refazer essa versão após renderizar o vídeo:

```sh
uv run python scripts/add_demo_music.py
```

Requer `ffmpeg` e `ffprobe`; a composição usa apenas a biblioteca padrão do
Python e é determinística. O arquivo Asciinema continua sem áudio.

Os scripts antigos `.expect` são aliases do gravador validado em Python.
A sessão lê continuamente a saída do PTY para evitar bloqueios e usa
`TERM=xterm-256color`, `COLORTERM=truecolor`, removendo `NO_COLOR`.
Não use RTK entre o gravador e a aplicação.

Para uma captura manual, `make record-demo` abre uma sessão que substitui
o `.cast` existente. Nesse modo você é responsável por usar uma base isolada:

```sh
demo_dir="$(mktemp -d /tmp/personal-assistant-demo.XXXXXX)"
cd "$demo_dir"
uv run --project /caminho/para/personal-assistant-textual personal-assistant
```

Saia da TUI antes de voltar ao projeto para rodar os comandos do Makefile. Ao
terminar a captura, remova `"$demo_dir"`. Assim, a demonstração não altera
`data/` nem `exports/` do projeto.
