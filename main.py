#!/usr/bin/env python3
"""
PomoTask - Pomodoro com tarefas configuráveis.
Interface em linha de comando.
"""
import sys
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich import box

from config import load_config, save_config, DEFAULTS
from tasks import (
    get_all_tasks,
    add_task,
    get_task_by_id,
    update_task,
    delete_task,
    increment_pomodoro,
    complete_task,
    Task,
)
from pomodoro import (
    run_timer,
    get_work_seconds,
    get_short_break_seconds,
    get_long_break_seconds,
    get_pomodoros_before_long_break,
    format_time,
)

console = Console()

# Estado global para cancelar o timer (Ctrl+C ou opção)
_cancel_timer = False


def set_cancel_timer(value: bool):
    global _cancel_timer
    _cancel_timer = value


def check_cancel() -> bool:
    return _cancel_timer


def show_tasks(include_completed: bool = False):
    """Exibe tabela de tarefas."""
    tasks = get_all_tasks(include_completed=include_completed)
    if not tasks:
        console.print("[dim]Nenhuma tarefa. Adicione uma no menu.[/dim]")
        return

    table = Table(title="Tarefas", box=box.ROUNDED)
    table.add_column("ID", style="cyan", width=4)
    table.add_column("Nome", style="white")
    table.add_column("Pomodoros", justify="center", width=10)
    table.add_column("Prioridade", justify="center", width=8)
    table.add_column("Notas", style="dim", max_width=30)

    for t in tasks:
        pomo = f"{t.completed_pomodoros}"
        if t.estimated_pomodoros > 0:
            pomo += f"/{t.estimated_pomodoros}"
        prio = ["", "Baixa", "Média", "Alta"][min(t.priority, 3)]
        status = " ✓" if t.completed else ""
        table.add_row(
            t.id,
            t.name + status,
            pomo,
            prio,
            (t.notes[:27] + "...") if len(t.notes) > 30 else t.notes,
        )
    console.print(table)


def do_add_task():
    """Fluxo para adicionar tarefa."""
    name = Prompt.ask("Nome da tarefa")
    if not name.strip():
        console.print("[red]Nome não pode ser vazio.[/red]")
        return
    est = IntPrompt.ask("Pomodoros estimados (0 = sem estimativa)", default=0)
    if est < 0:
        est = 0
    prio = IntPrompt.ask("Prioridade (1=baixa, 2=média, 3=alta)", default=2)
    prio = max(1, min(3, prio))
    notes = Prompt.ask("Notas (opcional)", default="")
    task = add_task(name=name.strip(), estimated_pomodoros=est, priority=prio, notes=notes.strip())
    console.print(f"[green]Tarefa #{task.id} criada.[/green]")


def do_edit_task():
    """Fluxo para editar tarefa."""
    show_tasks()
    task_id = Prompt.ask("ID da tarefa para editar")
    task = get_task_by_id(task_id)
    if not task:
        console.print("[red]Tarefa não encontrada.[/red]")
        return
    name = Prompt.ask("Nome", default=task.name)
    est = IntPrompt.ask("Pomodoros estimados", default=task.estimated_pomodoros)
    prio = IntPrompt.ask("Prioridade (1-3)", default=task.priority)
    prio = max(1, min(3, prio))
    notes = Prompt.ask("Notas", default=task.notes)
    update_task(task_id, name=name.strip(), estimated_pomodoros=est, priority=prio, notes=notes.strip())
    console.print("[green]Tarefa atualizada.[/green]")


def do_delete_task():
    """Fluxo para excluir tarefa."""
    show_tasks()
    task_id = Prompt.ask("ID da tarefa para excluir")
    if delete_task(task_id):
        console.print("[green]Tarefa excluída.[/green]")
    else:
        console.print("[red]Tarefa não encontrada.[/red]")


def do_settings():
    """Altera configurações do Pomodoro."""
    cfg = load_config()
    console.print(Panel("Configurações atuais", title="Pomodoro"))

    work = IntPrompt.ask("Minutos de trabalho", default=cfg.get("work_minutes", 25))
    short = IntPrompt.ask("Minutos de pausa curta", default=cfg.get("short_break_minutes", 5))
    long_break = IntPrompt.ask("Minutos de pausa longa", default=cfg.get("long_break_minutes", 15))
    before_long = IntPrompt.ask("Pomodoros até pausa longa", default=cfg.get("pomodoros_before_long_break", 4))

    cfg["work_minutes"] = max(1, work)
    cfg["short_break_minutes"] = max(0, short)
    cfg["long_break_minutes"] = max(0, long_break)
    cfg["pomodoros_before_long_break"] = max(1, before_long)
    save_config(cfg)
    console.print("[green]Configurações salvas.[/green]")


def run_pomodoro_cycle(task_id: Optional[str], is_work: bool, total_seconds: int, label: str):
    """Executa um ciclo (trabalho ou pausa) com barra de progresso."""
    set_cancel_timer(False)

    def on_tick(remaining: int, total: int):
        if check_cancel():
            return
        # Barra simples no console
        pct = (total - remaining) / total if total else 0
        bar_len = 30
        filled = int(bar_len * pct)
        bar = "█" * filled + "░" * (bar_len - filled)
        console.print(
            f"\r[bold]{label}[/bold] {bar} {format_time(remaining)} (Ctrl+C cancela)",
            end="",
        )

    completed = run_timer(
        total_seconds,
        on_tick=on_tick,
        on_finish=lambda: console.print(),
        check_cancel=check_cancel,
    )

    if completed and is_work and task_id:
        increment_pomodoro(task_id)
        console.print("[green]Pomodoro registrado na tarefa.[/green]")
    return completed


def do_start_pomodoro():
    """Inicia sequência de pomodoros com escolha de tarefa."""
    tasks = get_all_tasks()
    if not tasks:
        console.print("[yellow]Crie pelo menos uma tarefa antes de iniciar.[/yellow]")
        return

    show_tasks()
    task_id = Prompt.ask("ID da tarefa para trabalhar", default=tasks[0].id)
    task = get_task_by_id(task_id)
    if not task:
        console.print("[red]Tarefa não encontrada.[/red]")
        return

    cfg = load_config()
    work_sec = get_work_seconds()
    short_sec = get_short_break_seconds()
    long_sec = get_long_break_seconds()
    before_long = get_pomodoros_before_long_break()

    console.print(Panel(f"Tarefa: [bold]{task.name}[/bold]\nPomodoros: {before_long} (depois pausa longa)", title="Pomodoro"))

    try:
        for i in range(before_long):
            # Trabalho
            console.print()
            if not run_pomodoro_cycle(task_id, True, work_sec, "Trabalho"):
                console.print("[yellow]Timer cancelado.[/yellow]")
                set_cancel_timer(False)
                return

            if i < before_long - 1:
                # Pausa (curta ou longa)
                is_long = i == before_long - 2
                sec = long_sec if is_long else short_sec
                label = "Pausa longa" if is_long else "Pausa curta"
                if sec > 0:
                    run_pomodoro_cycle(None, False, sec, label)
                    console.print()

        console.print("[bold green]Sessão de 4 pomodoros concluída![/bold green]")
        if Confirm.ask("Marcar tarefa como concluída?"):
            complete_task(task_id)
            console.print("[green]Tarefa marcada como concluída.[/green]")
    except KeyboardInterrupt:
        set_cancel_timer(True)
        console.print("\n[yellow]Interrompido.[/yellow]")


def main():
    """Menu principal."""
    console.print(Panel.fit("[bold]PomoTask[/bold] – Pomodoro com tarefas", border_style="green"))

    while True:
        console.print()
        console.print("1. Ver tarefas")
        console.print("2. Adicionar tarefa")
        console.print("3. Editar tarefa")
        console.print("4. Excluir tarefa")
        console.print("5. Iniciar Pomodoro")
        console.print("6. Configurações")
        console.print("0. Sair")
        op = Prompt.ask("Opção", default="1")

        if op == "0":
            console.print("Até logo!")
            sys.exit(0)
        elif op == "1":
            show_tasks(include_completed=True)
        elif op == "2":
            do_add_task()
        elif op == "3":
            do_edit_task()
        elif op == "4":
            do_delete_task()
        elif op == "5":
            do_start_pomodoro()
        elif op == "6":
            do_settings()
        else:
            console.print("[red]Opção inválida.[/red]")


if __name__ == "__main__":
    main()
