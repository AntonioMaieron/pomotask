#!/usr/bin/env python3
"""
PomoTask - Interface gráfica com tkinter.
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Optional

from config import load_config, save_config
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
    get_work_seconds,
    get_short_break_seconds,
    get_long_break_seconds,
    get_pomodoros_before_long_break,
    format_time,
)


class PomodoroTimer:
    """Timer não-bloqueante para a GUI."""

    def __init__(self, root: tk.Tk, on_finish):
        self.root = root
        self.on_finish = on_finish
        self.remaining = 0
        self.total = 0
        self._job: Optional[str] = None
        self.cancelled = False

    def start(self, total_seconds: int, on_tick):
        self.total = total_seconds
        self.remaining = total_seconds
        self.cancelled = False
        self._on_tick = on_tick

        def tick():
            if self.cancelled:
                self._job = None
                return
            self._on_tick(self.remaining, self.total)
            if self.remaining <= 0:
                self._job = None
                self.on_finish()
                return
            self.remaining -= 1
            self._job = self.root.after(1000, tick)

        self._job = self.root.after(1000, tick)

    def cancel(self):
        self.cancelled = True
        if self._job:
            self.root.after_cancel(self._job)
            self._job = None


class SettingsWindow:
    """Janela de configurações do Pomodoro."""

    def __init__(self, parent, on_save):
        self.on_save = on_save
        self.win = tk.Toplevel(parent)
        self.win.title("Configurações")
        self.win.transient(parent)
        self.win.grab_set()

        cfg = load_config()
        f = ttk.Frame(self.win, padding=12)
        f.pack(fill=tk.BOTH, expand=True)

        ttk.Label(f, text="Minutos de trabalho:").grid(row=0, column=0, sticky=tk.W, pady=4)
        self.work_var = tk.IntVar(value=cfg.get("work_minutes", 25))
        tk.Spinbox(f, from_=1, to=60, textvariable=self.work_var, width=6).grid(row=0, column=1, padx=8, pady=4)

        ttk.Label(f, text="Pausa curta (min):").grid(row=1, column=0, sticky=tk.W, pady=4)
        self.short_var = tk.IntVar(value=cfg.get("short_break_minutes", 5))
        tk.Spinbox(f, from_=0, to=30, textvariable=self.short_var, width=6).grid(row=1, column=1, padx=8, pady=4)

        ttk.Label(f, text="Pausa longa (min):").grid(row=2, column=0, sticky=tk.W, pady=4)
        self.long_var = tk.IntVar(value=cfg.get("long_break_minutes", 15))
        tk.Spinbox(f, from_=0, to=60, textvariable=self.long_var, width=6).grid(row=2, column=1, padx=8, pady=4)

        ttk.Label(f, text="Pomodoros até pausa longa:").grid(row=3, column=0, sticky=tk.W, pady=4)
        self.before_long_var = tk.IntVar(value=cfg.get("pomodoros_before_long_break", 4))
        tk.Spinbox(f, from_=1, to=10, textvariable=self.before_long_var, width=6).grid(row=3, column=1, padx=8, pady=4)

        btn_f = ttk.Frame(f)
        btn_f.grid(row=4, column=0, columnspan=2, pady=12)
        ttk.Button(btn_f, text="Salvar", command=self._save).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_f, text="Cancelar", command=self.win.destroy).pack(side=tk.LEFT, padx=4)

    def _save(self):
        cfg = load_config()
        cfg["work_minutes"] = max(1, self.work_var.get())
        cfg["short_break_minutes"] = max(0, self.short_var.get())
        cfg["long_break_minutes"] = max(0, self.long_var.get())
        cfg["pomodoros_before_long_break"] = max(1, self.before_long_var.get())
        save_config(cfg)
        self.on_save()
        self.win.destroy()
        messagebox.showinfo("Configurações", "Configurações salvas.")


class TaskDialog:
    """Diálogo para adicionar/editar tarefa."""

    def __init__(self, parent, title: str, task: Optional[Task] = None, on_ok=None):
        self.on_ok = on_ok
        self.win = tk.Toplevel(parent)
        self.win.title(title)
        self.win.transient(parent)
        self.win.grab_set()

        f = ttk.Frame(self.win, padding=12)
        f.pack(fill=tk.BOTH, expand=True)

        ttk.Label(f, text="Nome:").grid(row=0, column=0, sticky=tk.W, pady=4)
        self.name_var = tk.StringVar(value=task.name if task else "")
        ttk.Entry(f, textvariable=self.name_var, width=35).grid(row=0, column=1, padx=8, pady=4)

        ttk.Label(f, text="Pomodoros estimados:").grid(row=1, column=0, sticky=tk.W, pady=4)
        self.est_var = tk.IntVar(value=task.estimated_pomodoros if task else 0)
        tk.Spinbox(f, from_=0, to=20, textvariable=self.est_var, width=6).grid(row=1, column=1, padx=8, pady=4)

        ttk.Label(f, text="Prioridade (1-3):").grid(row=2, column=0, sticky=tk.W, pady=4)
        self.prio_var = tk.IntVar(value=task.priority if task else 2)
        tk.Spinbox(f, from_=1, to=3, textvariable=self.prio_var, width=6).grid(row=2, column=1, padx=8, pady=4)

        ttk.Label(f, text="Notas:").grid(row=3, column=0, sticky=tk.W, pady=4)
        self.notes_var = tk.StringVar(value=task.notes if task else "")
        ttk.Entry(f, textvariable=self.notes_var, width=35).grid(row=3, column=1, padx=8, pady=4)

        btn_f = ttk.Frame(f)
        btn_f.grid(row=4, column=0, columnspan=2, pady=12)
        ttk.Button(btn_f, text="OK", command=self._ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_f, text="Cancelar", command=self.win.destroy).pack(side=tk.LEFT, padx=4)

        self.task = task

    def _ok(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Tarefa", "Informe o nome da tarefa.")
            return
        if self.on_ok:
            est = max(0, self.est_var.get())
            prio = max(1, min(3, self.prio_var.get()))
            self.on_ok(
                name=name,
                estimated_pomodoros=est,
                priority=prio,
                notes=self.notes_var.get().strip(),
                task_id=self.task.id if self.task else None,
            )
        self.win.destroy()


class PomoTaskApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PomoTask")
        self.root.minsize(420, 380)
        self.root.geometry("480x420")

        self.timer = PomodoroTimer(self.root, on_finish=self._timer_finish)
        self.timer_running = False
        self.timer_label_text = ""
        self.current_task_id: Optional[str] = None
        self.pomodoro_count = 0
        self.pomodoros_before_long = 4
        self.is_work_phase = True
        self.phase_index = 0

        self._build_ui()

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        # Área do timer (visível principalmente quando rodando)
        self.timer_frame = ttk.LabelFrame(main, text="Timer", padding=8)
        self.timer_frame.pack(fill=tk.X, pady=(0, 10))
        self.timer_label = ttk.Label(self.timer_frame, text="Pronto. Selecione uma tarefa e inicie.", font=("Segoe UI", 14))
        self.timer_label.pack(pady=4)
        self.progress = ttk.Progressbar(self.timer_frame, mode="determinate", length=300)
        self.progress.pack(pady=4, fill=tk.X)
        self.timer_btn_frame = ttk.Frame(self.timer_frame)
        self.timer_btn_frame.pack(pady=4)
        self.start_btn = ttk.Button(self.timer_btn_frame, text="Iniciar Pomodoro", command=self._start_pomodoro)
        self.start_btn.pack(side=tk.LEFT, padx=4)
        self.cancel_btn = ttk.Button(self.timer_btn_frame, text="Cancelar", command=self._cancel_timer, state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.LEFT, padx=4)

        # Lista de tarefas
        task_frame = ttk.LabelFrame(main, text="Tarefas", padding=8)
        task_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("nome", "pomo", "prioridade")
        self.tree = ttk.Treeview(task_frame, columns=columns, show="headings", height=8, selectmode="browse")
        self.tree.heading("nome", text="Nome")
        self.tree.heading("pomo", text="Pomodoros")
        self.tree.heading("prioridade", text="Prioridade")
        self.tree.column("nome", width=220)
        self.tree.column("pomo", width=80)
        self.tree.column("prioridade", width=80)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll = ttk.Scrollbar(task_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scroll.set)

        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=8)
        ttk.Button(btn_frame, text="Adicionar tarefa", command=self._add_task).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Editar tarefa", command=self._edit_task).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Excluir tarefa", command=self._delete_task).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Configurações", command=self._settings).pack(side=tk.RIGHT, padx=4)

        self._refresh_tasks()

    def _refresh_tasks(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for t in get_all_tasks(include_completed=True):
            pomo = f"{t.completed_pomodoros}"
            if t.estimated_pomodoros > 0:
                pomo += f"/{t.estimated_pomodoros}"
            prio = ["", "Baixa", "Média", "Alta"][min(t.priority, 3)]
            nome = f"{t.name} ✓" if t.completed else t.name
            self.tree.insert("", tk.END, iid=t.id, values=(nome, pomo, prio))

    def _get_selected_task_id(self) -> Optional[str]:
        sel = self.tree.selection()
        if not sel:
            return None
        return sel[0]

    def _add_task(self):
        def on_ok(name, estimated_pomodoros, priority, notes, task_id=None):
            add_task(name=name, estimated_pomodoros=estimated_pomodoros, priority=priority, notes=notes)
            self._refresh_tasks()

        TaskDialog(self.root, "Nova tarefa", on_ok=on_ok)

    def _edit_task(self):
        tid = self._get_selected_task_id()
        if not tid:
            messagebox.showinfo("Editar", "Selecione uma tarefa na lista.")
            return
        task = get_task_by_id(tid)
        if not task:
            return

        def on_ok(name, estimated_pomodoros, priority, notes, task_id=None):
            update_task(tid, name=name, estimated_pomodoros=estimated_pomodoros, priority=priority, notes=notes)
            self._refresh_tasks()

        TaskDialog(self.root, "Editar tarefa", task=task, on_ok=on_ok)

    def _delete_task(self):
        tid = self._get_selected_task_id()
        if not tid:
            messagebox.showinfo("Excluir", "Selecione uma tarefa na lista.")
            return
        if messagebox.askyesno("Excluir", "Excluir esta tarefa?"):
            delete_task(tid)
            self._refresh_tasks()

    def _settings(self):
        SettingsWindow(self.root, on_save=lambda: None)

    def _start_pomodoro(self):
        tid = self._get_selected_task_id()
        if not tid:
            messagebox.showinfo("Pomodoro", "Selecione uma tarefa na lista.")
            return
        task = get_task_by_id(tid)
        if not task:
            return
        if task.completed:
            messagebox.showinfo("Pomodoro", "Esta tarefa já está concluída. Escolha outra.")
            return

        self.current_task_id = tid
        self.pomodoros_before_long = get_pomodoros_before_long_break()
        self.pomodoro_count = 0
        self.is_work_phase = True
        self.phase_index = 0
        self._run_next_phase()

    def _run_next_phase(self):
        if self.is_work_phase:
            sec = get_work_seconds()
            self.timer_label_text = f"Trabalho – {get_task_by_id(self.current_task_id).name if self.current_task_id else '?'}"
        else:
            is_long = self.phase_index >= self.pomodoros_before_long - 1
            sec = get_long_break_seconds() if is_long else get_short_break_seconds()
            self.timer_label_text = "Pausa longa" if is_long else "Pausa curta"

        self.timer_running = True
        self.start_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.progress["maximum"] = sec
        self.progress["value"] = 0

        def on_tick(remaining, total):
            self.timer_label.config(text=f"{self.timer_label_text}  {format_time(remaining)}")
            self.progress["value"] = total - remaining
            self.root.update_idletasks()

        self.timer.start(sec, on_tick)

    def _cancel_timer(self):
        self.timer.cancel()
        self._timer_stopped(cancelled=True)

    def _timer_finish(self):
        self._timer_stopped(cancelled=False)

    def _timer_stopped(self, cancelled: bool):
        self.timer_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)

        if cancelled:
            self.timer_label.config(text="Cancelado. Selecione uma tarefa e inicie novamente.")
            self.progress["value"] = 0
            return

        if self.is_work_phase:
            if self.current_task_id:
                increment_pomodoro(self.current_task_id)
                self._refresh_tasks()
            self.pomodoro_count += 1
            self.is_work_phase = False
            self._run_next_phase()  # inicia pausa
        else:
            self.is_work_phase = True
            self.phase_index += 1
            if self.phase_index >= self.pomodoros_before_long:
                # Fim da sessão (4 pomodoros + pausas)
                self.timer_label.config(text="Sessão concluída! Parabéns.")
                self.progress["value"] = self.progress["maximum"]
                if self.current_task_id and messagebox.askyesno("Concluir", "Marcar esta tarefa como concluída?"):
                    complete_task(self.current_task_id)
                    self._refresh_tasks()
                self.current_task_id = None
                self.phase_index = 0
                return
            self._run_next_phase()  # próximo trabalho

    def run(self):
        self.root.mainloop()


def main():
    app = PomoTaskApp()
    app.run()


if __name__ == "__main__":
    main()
