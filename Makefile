.DEFAULT_GOAL := help

.PHONY: help install lint format test check run seed clear

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
