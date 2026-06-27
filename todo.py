"""Console task manager (To-Do list).

The application stores tasks in ``tasks.json`` and provides a simple
Russian-language console interface for adding, viewing, completing, deleting,
searching and exporting tasks.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Callable, Iterable

TASKS_FILE = Path("tasks.json")
PRIORITIES = ("высокий", "средний", "низкий")
PRIORITY_ORDER = {"высокий": 0, "средний": 1, "низкий": 2}
DATE_FORMAT = "%d.%m.%Y"
RED = "\033[31m"
RESET = "\033[0m"


@dataclass
class Task:
    """A single to-do item."""

    title: str
    description: str
    due_date: str
    priority: str
    completed: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Create a task from JSON data and validate required fields."""
        return cls(
            title=str(data["title"]),
            description=str(data.get("description", "")),
            due_date=str(data["due_date"]),
            priority=str(data["priority"]).lower(),
            completed=bool(data.get("completed", False)),
        )


def parse_due_date(value: str) -> date:
    """Validate a date in DD.MM.YYYY format and ensure it is not in the past."""
    try:
        parsed = datetime.strptime(value.strip(), DATE_FORMAT).date()
    except ValueError as exc:
        raise ValueError("Дата должна быть в формате ДД.ММ.ГГГГ.") from exc

    if parsed < date.today():
        raise ValueError("Дата срока выполнения не может быть прошедшей.")
    return parsed


def validate_title(title: str) -> str:
    """Return a non-empty task title or raise ValueError."""
    cleaned = title.strip()
    if not cleaned:
        raise ValueError("Название задачи не может быть пустым.")
    return cleaned


def validate_priority(priority: str) -> str:
    """Return a supported priority value or raise ValueError."""
    cleaned = priority.strip().lower()
    if cleaned not in PRIORITIES:
        raise ValueError("Приоритет должен быть: высокий, средний или низкий.")
    return cleaned


def load_tasks(path: Path = TASKS_FILE) -> list[Task]:
    """Load tasks from a JSON file without crashing on common file errors."""
    if not path.exists():
        return []

    try:
        with path.open("r", encoding="utf-8") as file:
            raw_tasks = json.load(file)
    except PermissionError:
        print(f"Ошибка: нет прав на чтение файла {path}.")
        return []
    except json.JSONDecodeError:
        print(f"Ошибка: файл {path} повреждён. Начат пустой список задач.")
        return []
    except OSError as exc:
        print(f"Ошибка чтения файла {path}: {exc}")
        return []

    if not isinstance(raw_tasks, list):
        print(f"Ошибка: файл {path} содержит данные неверного формата.")
        return []

    tasks: list[Task] = []
    for item in raw_tasks:
        try:
            task = Task.from_dict(item)
            validate_title(task.title)
            datetime.strptime(task.due_date, DATE_FORMAT)
            validate_priority(task.priority)
        except (KeyError, TypeError, ValueError) as exc:
            print(f"Пропущена некорректная задача: {exc}")
            continue
        tasks.append(task)
    return tasks


def save_tasks(tasks: Iterable[Task], path: Path = TASKS_FILE) -> bool:
    """Save tasks to JSON and report file-system errors to the user."""
    try:
        with path.open("w", encoding="utf-8") as file:
            json.dump(
                [asdict(task) for task in tasks], file, ensure_ascii=False, indent=2
            )
    except PermissionError:
        print(f"Ошибка: нет прав на запись в файл {path}.")
        return False
    except OSError as exc:
        print(f"Ошибка записи файла {path}: {exc}")
        return False
    return True


def sort_tasks(tasks: Iterable[Task]) -> list[Task]:
    """Sort by status, due date and priority."""
    return sorted(
        tasks,
        key=lambda task: (
            task.completed,
            datetime.strptime(task.due_date, DATE_FORMAT).date(),
            PRIORITY_ORDER[task.priority],
        ),
    )


def filter_tasks(tasks: Iterable[Task], mode: str) -> list[Task]:
    """Filter tasks by all/active/completed mode."""
    if mode == "2":
        return [task for task in tasks if not task.completed]
    if mode == "3":
        return [task for task in tasks if task.completed]
    return list(tasks)


def prompt_until_valid(prompt: str, validator: Callable[[str], str]) -> str:
    """Ask for input until the validator accepts it."""
    while True:
        try:
            return validator(input(prompt))
        except ValueError as exc:
            print(f"Ошибка: {exc}")


def add_task(tasks: list[Task]) -> None:
    """Interactively add a task."""
    title = prompt_until_valid("Название: ", validate_title)
    description = input("Описание: ").strip()
    due_date = prompt_until_valid(
        "Срок (ДД.ММ.ГГГГ): ", lambda value: parse_due_date(value).strftime(DATE_FORMAT)
    )
    priority = prompt_until_valid(
        "Приоритет (высокий/средний/низкий): ", validate_priority
    )
    tasks.append(
        Task(title=title, description=description, due_date=due_date, priority=priority)
    )
    save_tasks(tasks)
    print("Задача добавлена.")


def format_task(task: Task, index: int) -> str:
    """Return a display string for a task, highlighting overdue active tasks."""
    status = "✓" if task.completed else " "
    text = f"{index}. [{status}] {task.due_date} | {task.priority:<7} | {task.title}"
    due_date = datetime.strptime(task.due_date, DATE_FORMAT).date()
    if due_date < date.today() and not task.completed:
        return f"{RED}{text}{RESET}"
    return text


def show_tasks(tasks: list[Task]) -> list[Task]:
    """Show sorted tasks and return the currently displayed list."""
    print("\nФильтр: 1 — все, 2 — активные, 3 — выполненные")
    mode = input("Выберите фильтр [1]: ").strip() or "1"
    displayed = sort_tasks(filter_tasks(tasks, mode))
    if not displayed:
        print("Задач нет.")
        return []

    print("\nСписок задач:")
    for index, task in enumerate(displayed, start=1):
        print(format_task(task, index))
        if task.description:
            print(f"   Описание: {task.description}")
    return displayed


def choose_task(tasks: list[Task], action: str) -> Task | None:
    """Display tasks and ask the user to choose one by visible number."""
    displayed = show_tasks(tasks)
    if not displayed:
        return None
    while True:
        raw_number = input(f"Введите номер задачи, которую нужно {action}: ").strip()
        try:
            number = int(raw_number)
            if 1 <= number <= len(displayed):
                return displayed[number - 1]
        except ValueError:
            pass
        print("Ошибка: введите корректный номер из списка.")


def complete_task(tasks: list[Task]) -> None:
    """Mark a selected task as completed."""
    task = choose_task(tasks, "отметить выполненной")
    if task is None:
        return
    task.completed = True
    save_tasks(tasks)
    print("Задача отмечена как выполненная.")


def confirm_deletion(title: str) -> bool:
    """Ask for deletion confirmation."""
    answer = input(f"Удалить задачу '{title}'? (да/нет): ").strip().lower()
    return answer in {"да", "д", "yes", "y"}


def delete_task(tasks: list[Task]) -> None:
    """Delete a selected task after confirmation."""
    task = choose_task(tasks, "удалить")
    if task is None:
        return
    if confirm_deletion(task.title):
        tasks.remove(task)
        save_tasks(tasks)
        print("Задача удалена.")
    else:
        print("Удаление отменено.")


def search_tasks(tasks: list[Task]) -> None:
    """Search tasks by keyword in title."""
    keyword = input("Ключевое слово в названии: ").strip().lower()
    found = [task for task in tasks if keyword in task.title.lower()]
    for index, task in enumerate(sort_tasks(found), start=1):
        print(format_task(task, index))
    if not found:
        print("Ничего не найдено.")


def export_to_csv(tasks: list[Task], path: Path = Path("tasks_export.csv")) -> None:
    """Export tasks to a CSV file."""
    try:
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "title",
                    "description",
                    "due_date",
                    "priority",
                    "completed",
                ],
            )
            writer.writeheader()
            writer.writerows(asdict(task) for task in sort_tasks(tasks))
    except OSError as exc:
        print(f"Ошибка экспорта: {exc}")
        return
    print(f"Экспортировано в {path}.")


def main() -> None:
    """Run the console menu."""
    tasks = load_tasks()
    actions = {
        "1": add_task,
        "2": show_tasks,
        "3": complete_task,
        "4": delete_task,
        "5": search_tasks,
        "6": export_to_csv,
    }

    while True:
        print(
            "\nМеню:\n"
            "1. Добавить задачу\n"
            "2. Показать задачи\n"
            "3. Отметить выполненной\n"
            "4. Удалить задачу\n"
            "5. Найти задачу\n"
            "6. Экспорт в CSV\n"
            "0. Выход"
        )
        choice = input("Выберите пункт: ").strip()
        if choice == "0":
            print("До свидания!")
            break
        action = actions.get(choice)
        if action is None:
            print("Ошибка: выберите пункт меню от 0 до 6.")
            continue
        action(tasks)


if __name__ == "__main__":
    main()
