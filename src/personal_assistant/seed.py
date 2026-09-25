"""Anonymous generic tasks used to populate a new local database."""

from datetime import datetime

from personal_assistant.models import TaskStatus

SeedTask = tuple[datetime, str, str, TaskStatus]

SEED_TASKS: tuple[SeedTask, ...] = (
    (
        datetime(2026, 9, 23, 17, 8),
        "tarefa",
        "Revisar documentação do projeto",
        TaskStatus.PENDING,
    ),
    (
        datetime(2026, 9, 18, 15, 21),
        "tarefa",
        "Atualizar checklist de publicação",
        TaskStatus.COMPLETED,
    ),
    (
        datetime(2026, 9, 18, 9, 47),
        "planejamento",
        "Organizar tarefas da semana",
        TaskStatus.COMPLETED,
    ),
    (
        datetime(2026, 9, 18, 9, 47),
        "qualidade",
        "Preparar ambiente de testes",
        TaskStatus.COMPLETED,
    ),
    (
        datetime(2026, 9, 18, 9, 7),
        "tarefa",
        "Revisar solicitações de suporte",
        TaskStatus.COMPLETED,
    ),
    (
        datetime(2026, 9, 1, 10, 38),
        "tarefa",
        "Validar o fluxo principal da aplicação",
        TaskStatus.PENDING,
    ),
    (
        datetime(2026, 8, 13, 12, 32),
        "tarefa",
        "Configurar acesso para ambiente de teste",
        TaskStatus.PENDING,
    ),
    (
        datetime(2026, 8, 13, 12, 24),
        "custos",
        "Revisar custos de recursos",
        TaskStatus.COMPLETED,
    ),
    (
        datetime(2026, 5, 11, 17, 22),
        "bug",
        "Corrigir falha no carregamento de dados",
        TaskStatus.COMPLETED,
    ),
    (
        datetime(2026, 5, 11, 17, 17),
        "custos",
        "Revisar configuração de cache",
        TaskStatus.PENDING,
    ),
)
