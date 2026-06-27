"""Local browser interface for the To-Do list application.

Run ``python3 web_todo.py`` and open http://127.0.0.1:8000 in a browser.
The module intentionally uses only the Python standard library so the project
works without installing web-framework dependencies.
"""

from __future__ import annotations

from datetime import date, datetime
from html import escape
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

from todo import (
    DATE_FORMAT,
    PRIORITIES,
    PRIORITY_ORDER,
    Task,
    load_tasks,
    parse_due_date,
    save_tasks,
    validate_priority,
    validate_title,
)

HOST = "127.0.0.1"
PORT = 8000

STYLE = """
:root {
  --bg: #f7f1ea;
  --panel: #fffaf3;
  --panel-strong: #f0e4da;
  --text: #4d4650;
  --muted: #7e7481;
  --accent: #91b7a8;
  --accent-dark: #5f8f7c;
  --rose: #e6a6a6;
  --rose-dark: #bf6f72;
  --lavender: #d7c8ea;
  --yellow: #f1d99b;
  --shadow: 0 18px 45px rgba(105, 89, 74, 0.12);
}

* { box-sizing: border-box; }

body {
  margin: 0;
  min-height: 100vh;
  background:
    radial-gradient(circle at top left, rgba(215, 200, 234, 0.55), transparent 34rem),
    radial-gradient(circle at top right, rgba(145, 183, 168, 0.45), transparent 30rem),
    var(--bg);
  color: var(--text);
  font-family: Inter, "Segoe UI", Arial, sans-serif;
}

a { color: inherit; text-decoration: none; }

.page {
  width: min(1120px, calc(100% - 32px));
  margin: 0 auto;
  padding: 36px 0 54px;
}

.hero {
  display: grid;
  gap: 14px;
  margin-bottom: 24px;
}

.eyebrow {
  color: var(--accent-dark);
  font-size: 0.82rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

h1, h2, h3 { margin: 0; }

h1 {
  font-size: clamp(2rem, 5vw, 4rem);
  line-height: 1;
}

.hero p {
  max-width: 740px;
  color: var(--muted);
  font-size: 1.05rem;
  line-height: 1.6;
  margin: 0;
}

.grid {
  display: grid;
  grid-template-columns: minmax(280px, 380px) 1fr;
  gap: 22px;
  align-items: start;
}

.card {
  background: rgba(255, 250, 243, 0.88);
  border: 1px solid rgba(255, 255, 255, 0.7);
  border-radius: 28px;
  box-shadow: var(--shadow);
  padding: 24px;
  backdrop-filter: blur(12px);
}

.stack { display: grid; gap: 14px; }

label {
  display: grid;
  gap: 7px;
  color: var(--muted);
  font-size: 0.92rem;
  font-weight: 700;
}

input, textarea, select {
  width: 100%;
  border: 1px solid #eaded4;
  border-radius: 16px;
  background: #fffdf9;
  color: var(--text);
  font: inherit;
  padding: 12px 14px;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}

textarea { min-height: 96px; resize: vertical; }

input:focus, textarea:focus, select:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 4px rgba(145, 183, 168, 0.22);
}

button, .button {
  border: 0;
  border-radius: 999px;
  background: var(--accent);
  color: #fff;
  cursor: pointer;
  display: inline-flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  font: inherit;
  font-weight: 800;
  padding: 12px 18px;
  transition: transform 0.2s, box-shadow 0.2s, background 0.2s;
}

button:hover, .button:hover {
  background: var(--accent-dark);
  box-shadow: 0 10px 24px rgba(95, 143, 124, 0.25);
  transform: translateY(-1px);
}

.button.secondary { background: var(--lavender); }
.button.danger, button.danger { background: var(--rose); }
.button.danger:hover, button.danger:hover { background: var(--rose-dark); }

.message {
  border-radius: 18px;
  margin-bottom: 18px;
  padding: 13px 16px;
  font-weight: 700;
}

.message.success { background: #dceee5; color: #477766; }
.message.error { background: #f7dddd; color: #a04f54; }

.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: space-between;
  margin-bottom: 16px;
}

.filters { display: flex; flex-wrap: wrap; gap: 8px; }

.filter-pill {
  background: #fffdf9;
  border: 1px solid #eaded4;
  border-radius: 999px;
  color: var(--muted);
  font-weight: 800;
  padding: 10px 14px;
}

.filter-pill.active {
  background: var(--panel-strong);
  color: var(--text);
}

.search { display: flex; gap: 8px; min-width: min(100%, 310px); }

.search input { min-width: 0; }

.task-list { display: grid; gap: 12px; }

.task {
  background: #fffdf9;
  border: 1px solid #eaded4;
  border-left: 8px solid var(--accent);
  border-radius: 22px;
  display: grid;
  gap: 12px;
  padding: 16px;
}

.task.completed { opacity: 0.68; border-left-color: var(--lavender); }
.task.overdue { border-left-color: var(--rose); }

.task-header {
  align-items: start;
  display: flex;
  gap: 12px;
  justify-content: space-between;
}

.task-title { font-size: 1.12rem; font-weight: 900; }
.task.completed .task-title { text-decoration: line-through; }

.meta { display: flex; flex-wrap: wrap; gap: 8px; }

.badge {
  background: var(--panel-strong);
  border-radius: 999px;
  color: var(--muted);
  font-size: 0.82rem;
  font-weight: 800;
  padding: 7px 10px;
}

.priority-high { background: #f7dddd; color: #a04f54; }
.priority-medium { background: #fff0c7; color: #8b6b22; }
.priority-low { background: #dceee5; color: #477766; }

.actions { display: flex; flex-wrap: wrap; gap: 8px; }

.inline-form { display: inline; }

.empty {
  border: 2px dashed #dfd2c8;
  border-radius: 24px;
  color: var(--muted);
  padding: 34px;
  text-align: center;
}

@media (max-width: 820px) {
  .grid { grid-template-columns: 1fr; }
  .toolbar { display: grid; }
  .search { width: 100%; }
}
"""


def html_page(content: str, message: str = "", message_type: str = "success") -> bytes:
    """Wrap body content into a full HTML page."""
    safe_message = escape(message)
    banner = (
        f'<div class="message {message_type}">{safe_message}</div>' if message else ""
    )
    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Мой To-Do list</title>
  <style>{STYLE}</style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <div class="eyebrow">локальный менеджер задач</div>
      <h1>Спокойный список дел</h1>
      <p>Добавляйте задачи, выбирайте фильтры кнопками, отмечайте выполнение и удаляйте записи прямо в браузере. Данные сохраняются локально в файле <strong>tasks.json</strong>.</p>
    </section>
    {banner}
    {content}
  </main>
</body>
</html>""".encode("utf-8")


def redirect_url(
    message: str = "", message_type: str = "success", **params: str
) -> str:
    """Build a redirect URL with optional user-facing message."""
    query = {key: value for key, value in params.items() if value}
    if message:
        query["message"] = message
        query["type"] = message_type
    return "/" + ("?" + urlencode(query) if query else "")


def task_matches_filter(task: Task, filter_name: str) -> bool:
    """Return True if task belongs to the selected browser filter."""
    if filter_name == "active":
        return not task.completed
    if filter_name == "completed":
        return task.completed
    return True


def sorted_tasks(tasks: list[Task]) -> list[Task]:
    """Sort tasks for the browser view."""
    return sorted(
        tasks,
        key=lambda task: (
            task.completed,
            datetime.strptime(task.due_date, DATE_FORMAT).date(),
            PRIORITY_ORDER[task.priority],
        ),
    )


def render_filters(current_filter: str, search: str) -> str:
    """Render clickable filter buttons."""
    labels = {"all": "Все", "active": "Активные", "completed": "Выполненные"}
    links = []
    for key, label in labels.items():
        class_name = "filter-pill active" if key == current_filter else "filter-pill"
        query = (
            urlencode({"filter": key, "search": search})
            if search
            else urlencode({"filter": key})
        )
        links.append(f'<a class="{class_name}" href="/?{query}">{label}</a>')
    return "".join(links)


def render_task(task: Task, index: int) -> str:
    """Render one task card."""
    due_date = datetime.strptime(task.due_date, DATE_FORMAT).date()
    classes = ["task"]
    if task.completed:
        classes.append("completed")
    if due_date < date.today() and not task.completed:
        classes.append("overdue")

    priority_class = {
        "высокий": "priority-high",
        "средний": "priority-medium",
        "низкий": "priority-low",
    }[task.priority]
    status = "Выполнена" if task.completed else "Активна"
    complete_button = ""
    if not task.completed:
        complete_button = f"""
        <form class="inline-form" method="post" action="/complete">
          <input type="hidden" name="index" value="{index}">
          <button type="submit">✓ Выполнить</button>
        </form>"""

    return f"""
    <article class="{' '.join(classes)}">
      <div class="task-header">
        <div>
          <div class="task-title">{escape(task.title)}</div>
          <div class="meta">
            <span class="badge">№ {index + 1}</span>
            <span class="badge">{status}</span>
            <span class="badge">Срок: {escape(task.due_date)}</span>
            <span class="badge {priority_class}">{escape(task.priority)}</span>
          </div>
        </div>
      </div>
      <p>{escape(task.description) if task.description else 'Без описания'}</p>
      <div class="actions">
        {complete_button}
        <form class="inline-form" method="post" action="/delete" onsubmit="return confirm('Удалить задачу «{escape(task.title)}»?');">
          <input type="hidden" name="index" value="{index}">
          <button class="danger" type="submit">Удалить</button>
        </form>
      </div>
    </article>"""


def render_app(query: dict[str, list[str]]) -> bytes:
    """Render the main application screen."""
    tasks = load_tasks()
    current_filter = query.get("filter", ["all"])[0]
    search = query.get("search", [""])[0].strip()
    message = query.get("message", [""])[0]
    message_type = query.get("type", ["success"])[0]

    visible_pairs = [
        (index, task)
        for index, task in enumerate(tasks)
        if task_matches_filter(task, current_filter)
    ]
    if search:
        visible_pairs = [
            (index, task)
            for index, task in visible_pairs
            if search.lower() in task.title.lower()
        ]
    visible_pairs = sorted(
        visible_pairs,
        key=lambda item: (
            item[1].completed,
            datetime.strptime(item[1].due_date, DATE_FORMAT).date(),
            PRIORITY_ORDER[item[1].priority],
        ),
    )
    rendered_tasks = "".join(
        render_task(task, original_index) for original_index, task in visible_pairs
    )
    if not rendered_tasks:
        rendered_tasks = (
            '<div class="empty">Пока нет задач для выбранных условий.</div>'
        )

    today = date.today().strftime(DATE_FORMAT)
    content = f"""
    <section class="grid">
      <aside class="card">
        <h2>Новая задача</h2>
        <form class="stack" method="post" action="/add">
          <label>Название
            <input name="title" placeholder="Например: подготовить отчёт" required>
          </label>
          <label>Описание
            <textarea name="description" placeholder="Короткое описание задачи"></textarea>
          </label>
          <label>Срок выполнения
            <input name="due_date" value="{today}" placeholder="ДД.ММ.ГГГГ" required>
          </label>
          <label>Приоритет
            <select name="priority">
              {''.join(f'<option value="{priority}">{priority.title()}</option>' for priority in PRIORITIES)}
            </select>
          </label>
          <button type="submit">Добавить задачу</button>
        </form>
      </aside>

      <section class="card">
        <div class="toolbar">
          <div class="filters">{render_filters(current_filter, search)}</div>
          <form class="search" method="get" action="/">
            <input type="hidden" name="filter" value="{escape(current_filter)}">
            <input name="search" value="{escape(search)}" placeholder="Поиск по названию">
            <button type="submit">Найти</button>
          </form>
        </div>
        <div class="task-list">{rendered_tasks}</div>
      </section>
    </section>"""
    return html_page(content, message, message_type)


def first_form_value(data: dict[str, list[str]], key: str) -> str:
    """Extract one value from parsed form data."""
    return data.get(key, [""])[0]


class TodoRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the local To-Do application."""

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        """Keep the terminal clean during normal local use."""

    def send_html(self, body: bytes, status: HTTPStatus = HTTPStatus.OK) -> None:
        """Send an HTML response."""
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def redirect(self, location: str) -> None:
        """Redirect the browser after a form action."""
        self.send_response(HTTPStatus.SEE_OTHER)
        self.send_header("Location", location)
        self.end_headers()

    def read_form(self) -> dict[str, list[str]]:
        """Read urlencoded form data from a POST request."""
        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length).decode("utf-8")
        return parse_qs(raw_body)

    def do_GET(self) -> None:  # noqa: N802
        """Handle the main page."""
        parsed = urlparse(self.path)
        if parsed.path != "/":
            self.send_error(HTTPStatus.NOT_FOUND, "Страница не найдена")
            return
        self.send_html(render_app(parse_qs(parsed.query)))

    def do_POST(self) -> None:  # noqa: N802
        """Handle browser form actions."""
        parsed = urlparse(self.path)
        form = self.read_form()
        if parsed.path == "/add":
            self.handle_add(form)
        elif parsed.path == "/complete":
            self.handle_complete(form)
        elif parsed.path == "/delete":
            self.handle_delete(form)
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "Действие не найдено")

    def handle_add(self, form: dict[str, list[str]]) -> None:
        """Validate and add a task from browser form data."""
        try:
            title = validate_title(first_form_value(form, "title"))
            description = first_form_value(form, "description").strip()
            due_date = parse_due_date(first_form_value(form, "due_date")).strftime(
                DATE_FORMAT
            )
            priority = validate_priority(first_form_value(form, "priority"))
        except ValueError as exc:
            self.redirect(redirect_url(str(exc), "error"))
            return

        tasks = load_tasks()
        tasks.append(Task(title, description, due_date, priority))
        save_tasks(tasks)
        self.redirect(redirect_url("Задача добавлена."))

    def handle_complete(self, form: dict[str, list[str]]) -> None:
        """Mark the selected task as completed."""
        tasks = load_tasks()
        try:
            index = int(first_form_value(form, "index"))
            tasks[index].completed = True
        except (ValueError, IndexError):
            self.redirect(redirect_url("Не удалось найти задачу.", "error"))
            return
        save_tasks(tasks)
        self.redirect(redirect_url("Задача отмечена как выполненная."))

    def handle_delete(self, form: dict[str, list[str]]) -> None:
        """Delete the selected task after browser-side confirmation."""
        tasks = load_tasks()
        try:
            index = int(first_form_value(form, "index"))
            del tasks[index]
        except (ValueError, IndexError):
            self.redirect(redirect_url("Не удалось найти задачу.", "error"))
            return
        save_tasks(tasks)
        self.redirect(redirect_url("Задача удалена."))


def run_server(host: str = HOST, port: int = PORT) -> None:
    """Start the local browser application."""
    server = ThreadingHTTPServer((host, port), TodoRequestHandler)
    url = f"http://{host}:{port}"
    print(f"Откройте приложение в браузере: {url}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен.")
    finally:
        server.server_close()


if __name__ == "__main__":
    run_server()
