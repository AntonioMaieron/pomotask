# PomoTask

Pomodoro com tarefas configuráveis em Python. Use a técnica Pomodoro (intervalos de foco e pausas) e vincule cada sessão a uma tarefa.

## Requisitos

- Python 3.8+
- [Rich](https://github.com/Textualize/rich) (interface no terminal)

## Instalação

```bash
cd pomotask
pip install -r requirements.txt
```

## Uso

**Interface gráfica (recomendado):**

```bash
python gui.py
```

**Interface no terminal:**

```bash
python main.py
```

Na interface gráfica você pode ver e gerenciar tarefas, iniciar o Pomodoro (selecione uma tarefa e clique em "Iniciar Pomodoro"), cancelar o timer e abrir Configurações. No terminal, no menu você pode:

1. **Ver tarefas** – Lista tarefas com ID, nome, pomodoros feitos/estimados, prioridade e notas.
2. **Adicionar tarefa** – Cria tarefa com nome, pomodoros estimados, prioridade e notas.
3. **Editar tarefa** – Altera nome, estimativa, prioridade e notas de uma tarefa.
4. **Excluir tarefa** – Remove uma tarefa.
5. **Iniciar Pomodoro** – Escolhe uma tarefa e roda uma sessão (4 pomodoros de trabalho com pausas curtas e uma pausa longa ao final).
6. **Configurações** – Ajusta duração do trabalho, pausa curta, pausa longa e quantos pomodoros até a pausa longa.
0. **Sair**

Durante o timer, use **Ctrl+C** para cancelar.

## Configurações padrão

- Trabalho: 25 minutos  
- Pausa curta: 5 minutos  
- Pausa longa: 15 minutos  
- Pomodoros até pausa longa: 4  

Tudo isso pode ser alterado em **Configurações** no menu. Os dados são gravados na pasta `data/` (configuração e lista de tarefas em JSON).

## Estrutura do projeto

```
pomotask/
├── gui.py       # Interface gráfica (tkinter)
├── main.py      # Entrada e menu CLI
├── pomodoro.py  # Timer e duração dos intervalos
├── tasks.py     # CRUD de tarefas
├── config.py    # Carregar/salvar configuração
├── data/        # config.json e tasks.json (criados ao usar)
├── requirements.txt
└── README.md
```

## Licença

Uso livre.
