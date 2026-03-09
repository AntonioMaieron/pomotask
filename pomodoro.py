"""
Lógica do timer Pomodoro - ciclos de trabalho e pausas.
"""
import time
from typing import Callable, Optional

from config import load_config


def run_timer(
    total_seconds: int,
    on_tick: Optional[Callable[[int, int], None]] = None,
    on_finish: Optional[Callable[[], None]] = None,
    check_cancel: Optional[Callable[[], bool]] = None,
) -> bool:
    """
    Roda um timer por total_seconds.
    on_tick(remaining_seconds, total_seconds) é chamado a cada segundo.
    on_finish() ao terminar.
    check_cancel() retorna True para interromper.
    Retorna True se completou, False se cancelado.
    """
    remaining = total_seconds
    while remaining > 0:
        if check_cancel and check_cancel():
            return False
        if on_tick:
            on_tick(remaining, total_seconds)
        time.sleep(1)
        remaining -= 1
    if on_finish:
        on_finish()
    return True


def get_work_seconds() -> int:
    """Duração do período de trabalho em segundos."""
    cfg = load_config()
    return cfg.get("work_minutes", 25) * 60


def get_short_break_seconds() -> int:
    """Duração da pausa curta em segundos."""
    cfg = load_config()
    return cfg.get("short_break_minutes", 5) * 60


def get_long_break_seconds() -> int:
    """Duração da pausa longa em segundos."""
    cfg = load_config()
    return cfg.get("long_break_minutes", 15) * 60


def get_pomodoros_before_long_break() -> int:
    """Quantos pomodoros antes de uma pausa longa."""
    cfg = load_config()
    return cfg.get("pomodoros_before_long_break", 4)


def format_time(seconds: int) -> str:
    """Formata segundos como MM:SS."""
    m = seconds // 60
    s = seconds % 60
    return f"{m:02d}:{s:02d}"
