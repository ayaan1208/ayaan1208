export interface Todo {
  id: string;
  title: string;
  completed: boolean;
  createdAt: string;
}

const BASE = "/api";

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  list: () => fetch(`${BASE}/todos`).then((r) => json<Todo[]>(r)),
  create: (title: string) =>
    fetch(`${BASE}/todos`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title }),
    }).then((r) => json<Todo>(r)),
  toggle: (id: string, completed: boolean) =>
    fetch(`${BASE}/todos/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ completed }),
    }).then((r) => json<Todo>(r)),
  remove: (id: string) => fetch(`${BASE}/todos/${id}`, { method: "DELETE" }),
};
