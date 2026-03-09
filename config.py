"""
Configurações do Pomodoro - duração dos intervalos e preferências.
"""
import json
from pathlib import Path

CONFIG_DIR = Path(__file__).parent / "data"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULTS = {
    "work_minutes": 25,
    "short_break_minutes": 5,
    "long_break_minutes": 15,
    "pomodoros_before_long_break": 4,
    "auto_start_break": False,
    "auto_start_work": False,
    "sound_enabled": True,
}


def _ensure_data_dir():
    CONFIG_DIR.mkdir(exist_ok=True)


def load_config():
    """Carrega configuração do disco ou retorna padrões."""
    _ensure_data_dir()
    if not CONFIG_FILE.exists():
        return DEFAULTS.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Mescla com defaults para novas chaves
        out = DEFAULTS.copy()
        out.update(data)
        return out
    except (json.JSONDecodeError, IOError):
        return DEFAULTS.copy()


def save_config(config: dict):
    """Salva configuração no disco."""
    _ensure_data_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get(key: str, default=None):
    """Obtém um valor de configuração."""
    cfg = load_config()
    return cfg.get(key, default)


def set_value(key: str, value):
    """Define um valor e salva."""
    cfg = load_config()
    cfg[key] = value
    save_config(cfg)
