from datetime import date, timedelta
from pathlib import Path

import web_todo
from todo import Task, load_tasks, save_tasks

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def future_date(days: int) -> str:
    return (date.today() + timedelta(days=days)).strftime("%d.%m.%Y")


def test_render_app_contains_browser_controls(monkeypatch, tmp_path):
    data_file = tmp_path / "tasks.json"
    save_tasks([Task("Встреча", "Описание", future_date(1), "высокий")], data_file)
    monkeypatch.setattr(
        web_todo, "load_tasks", lambda path=data_file: load_tasks(data_file)
    )

    html = web_todo.render_app({}).decode("utf-8")

    assert "Спокойный список дел" in html
    assert "Добавить задачу" in html
    assert "Активные" in html
    assert "Встреча" in html
    assert "Удалить" in html


def test_standalone_html_app_opens_without_python_server():
    html = (PROJECT_ROOT / "todo_app.html").read_text(encoding="utf-8")

    assert "откройте этот HTML-файл" in html
    assert "localStorage" in html
    assert "Экспорт JSON" in html
    assert "Импорт JSON" in html
    assert "python3" not in html.lower()
