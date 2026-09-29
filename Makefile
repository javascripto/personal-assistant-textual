.DEFAULT_GOAL := help

.PHONY: help install lint format test check run seed clear record-demo play-demo
.PHONY: build-demo render-demo demo-check

help: ## Lista os comandos disponíveis.

	@awk 'BEGIN {FS = ":.*##"}; /^[a-zA-Z_-]+:.*##/ {printf "  \033[36m%-8s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Instala as dependências bloqueadas pelo uv.

	uv sync --all-groups

lint: ## Executa análise estática com Ruff, mypy e BasedPyright.

	uv run ruff check .
	uv run mypy
	uv run basedpyright

format: ## Formata o código com Ruff e Black.

	uv run ruff format .
	uv run black .

test: ## Executa os testes automatizados.

	uv run pytest

check: ## Valida formatação, lint, tipos e testes sem alterar arquivos.

	uv run ruff format --check .
	uv run black --check .
	uv run ruff check .
	uv run mypy
	uv run basedpyright
	uv run pytest

run: ## Inicia a interface Textual.

	uv run personal-assistant

seed: ## Faz backup e insere tarefas genéricas ausentes no banco SQLite local.

	uv run personal-assistant-seed

clear: ## Remove somente caches e relatórios gerados; preserva SQLite e exports.

	rm -rf .mypy_cache .pytest_cache .ruff_cache .coverage coverage.xml htmlcov

record-demo: ## Inicia a gravação interativa em docs/recordings/.

	asciinema rec --overwrite --idle-time-limit 1 --window-size 100x32 \
		--title "Personal Assistant TUI walkthrough" \
		docs/recordings/personal-assistant-demo.cast

play-demo: ## Reproduz a demonstração asciinema no terminal.

	asciinema play docs/recordings/personal-assistant-demo.cast

build-demo: ## Grava a demo validada em base isolada e gera o vídeo MP4.

	uv run --group demo python scripts/capture_demo.py
	$(MAKE) render-demo

render-demo: ## Converte a captura real em MP4 1080p com capítulos.

	uv run --group demo python scripts/render_demo.py

demo-check: ## Valida os scripts de gravação e renderização com tipos estritos.

	uv run --group demo mypy scripts/*.py
	uv run --group demo basedpyright scripts/*.py
