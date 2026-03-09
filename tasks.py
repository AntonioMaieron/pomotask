"""
Gerenciamento de tarefas - criar, editar, listar e concluir.
"""
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional
from datetime import datetime

from config import CONFIG_DIR

TASKS_FILE = CONFIG_DIR / "tasks.json"


@dataclass
class Task:
    """Uma tarefa com nome, pomodoros estimados e estado."""
    id: str
    name: str
    estimated_pomodoros: int  # 0 = sem estimativa
    completed_pomodoros: int
    priority: int  # 1=baixa, 2=média, 3=alta
    notes: str
    created_at: str
    completed: bool

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Task":
        return cls(
            id=d.get("id", ""),
            name=d.get("name", ""),
            estimated_pomodoros=d.get("estimated_pomodoros", 0),
            completed_pomodoros=d.get("completed_pomodoros", 0),
            priority=d.get("priority", 2),
            notes=d.get("notes", ""),
            created_at=d.get("created_at", datetime.now().isoformat()),
            completed=d.get("completed", False),
        )


def _ensure_data_dir():
    CONFIG_DIR.mkdir(exist_ok=True)


def _load_tasks_raw() -> list:
    _ensure_data_dir()
    if not TASKS_FILE.exists():
        return []
    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_tasks(tasks: List[Task]):
    _ensure_data_dir()
    data = [t.to_dict() for t in tasks]
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _new_id(tasks: List[Task]) -> str:
    if not tasks:
        return "1"
    ids = [int(t.id) for t in tasks if t.id.isdigit()]
    return str(max(ids, default=0) + 1)


def get_all_tasks(include_completed: bool = False) -> List[Task]:
    """Lista todas as tarefas. Por padrão exclui concluídas."""
    raw = _load_tasks_raw()
    tasks = [Task.from_dict(d) for d in raw]
    if not include_completed:
        tasks = [t for t in tasks if not t.completed]
    return sorted(tasks, key=lambda t: (-t.priority, t.created_at))


def add_task(
    name: str,
    estimated_pomodoros: int = 0,
    priority: int = 2,
    notes: str = "",
) -> Task:
    """Adiciona uma nova tarefa."""
    tasks = [Task.from_dict(d) for d in _load_tasks_raw()]
    task = Task(
        id=_new_id(tasks),
        name=name,
        estimated_pomodoros=estimated_pomodoros,
        completed_pomodoros=0,
        priority=priority,
        notes=notes,
        created_at=datetime.now().isoformat(),
        completed=False,
    )
    tasks.append(task)
    _save_tasks(tasks)
    return task


def get_task_by_id(task_id: str) -> Optional[Task]:
    """Retorna tarefa por ID ou None."""
    tasks = [Task.from_dict(d) for d in _load_tasks_raw()]
    for t in tasks:
        if t.id == task_id:
            return t
    return None


def update_task(
    task_id: str,
    name: Optional[str] = None,
    estimated_pomodoros: Optional[int] = None,
    priority: Optional[int] = None,
    notes: Optional[str] = None,
) -> Optional[Task]:
    """Atualiza campos de uma tarefa. None = não alterar."""
    tasks = [Task.from_dict(d) for d in _load_tasks_raw()]
    for t in tasks:
        if t.id == task_id:
            if name is not None:
                t.name = name
            if estimated_pomodoros is not None:
                t.estimated_pomodoros = estimated_pomodoros
            if priority is not None:
                t.priority = priority
            if notes is not None:
                t.notes = notes
            _save_tasks(tasks)
            return t
    return None


def increment_pomodoro(task_id: str) -> Optional[Task]:
    """Incrementa o contador de pomodoros completados da tarefa."""
    tasks = [Task.from_dict(d) for d in _load_tasks_raw()]
    for t in tasks:
        if t.id == task_id:
            t.completed_pomodoros += 1
            _save_tasks(tasks)
            return t
    return None


def complete_task(task_id: str) -> Optional[Task]:
    """Marca tarefa como concluída."""
    tasks = [Task.from_dict(d) for d in _load_tasks_raw()]
    for t in tasks:
        if t.id == task_id:
            t.completed = True
            _save_tasks(tasks)
            return t
    return None


def delete_task(task_id: str) -> bool:
    """Remove uma tarefa. Retorna True se existia."""
    tasks = [Task.from_dict(d) for d in _load_tasks_raw()]
    new_tasks = [t for t in tasks if t.id != task_id]
    if len(new_tasks) == len(tasks):
        return False
    _save_tasks(new_tasks)
    return True
