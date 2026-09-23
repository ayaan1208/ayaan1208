import { useEffect, useMemo, useState } from "react";
import { api, type Todo } from "./api";

export default function App() {
  const [todos, setTodos] = useState<Todo[]>([]);
  const [title, setTitle] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const remaining = useMemo(() => todos.filter((t) => !t.completed).length, [todos]);

  async function refresh() {
    try {
      setTodos(await api.list());
      setError(null);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function addTodo(e: React.FormEvent) {
    e.preventDefault();
    const value = title.trim();
    if (!value) return;
    setTitle("");
    try {
      const created = await api.create(value);
      setTodos((prev) => [...prev, created]);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function toggle(todo: Todo) {
    const updated = await api.toggle(todo.id, !todo.completed);
    setTodos((prev) => prev.map((t) => (t.id === updated.id ? updated : t)));
  }

  async function remove(todo: Todo) {
    await api.remove(todo.id);
    setTodos((prev) => prev.filter((t) => t.id !== todo.id));
  }

  return (
    <div className="app">
      <div className="card">
        <header className="header">
          <h1>Todo</h1>
          <p className="subtitle">
            {loading ? "Loading…" : `${remaining} of ${todos.length} remaining`}
          </p>
        </header>

        <form className="add-form" onSubmit={addTodo}>
          <input
            aria-label="New todo"
            className="input"
            placeholder="What needs doing?"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
          <button className="btn" type="submit">
            Add
          </button>
        </form>

        {error && <p className="error">⚠️ {error}</p>}

        <ul className="list">
          {todos.map((todo) => (
            <li key={todo.id} className={`item ${todo.completed ? "done" : ""}`}>
              <label className="item-main">
                <input
                  type="checkbox"
                  checked={todo.completed}
                  onChange={() => toggle(todo)}
                />
                <span className="item-title">{todo.title}</span>
              </label>
              <button
                className="delete"
                aria-label={`Delete ${todo.title}`}
                onClick={() => remove(todo)}
              >
                ✕
              </button>
            </li>
          ))}
          {!loading && todos.length === 0 && (
            <li className="empty">Nothing here yet — add your first task above.</li>
          )}
        </ul>
      </div>
      <footer className="footer">Full-stack demo · React + Express + TypeScript</footer>
    </div>
  );
}
