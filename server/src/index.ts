import cors from "cors";
import express, { type Request, type Response } from "express";
import { randomUUID } from "node:crypto";

interface Todo {
  id: string;
  title: string;
  completed: boolean;
  createdAt: string;
}

const PORT = Number(process.env.PORT ?? 3001);

const todos = new Map<string, Todo>();

function seed(): void {
  const initial = ["Set up the Cloud Agent environment", "Run the app end to end"];
  for (const title of initial) {
    const id = randomUUID();
    todos.set(id, { id, title, completed: false, createdAt: new Date().toISOString() });
  }
}
seed();

const app = express();
app.use(cors());
app.use(express.json());

app.get("/api/health", (_req: Request, res: Response) => {
  res.json({ status: "ok", uptime: process.uptime() });
});

app.get("/api/todos", (_req: Request, res: Response) => {
  const all = [...todos.values()].sort((a, b) => a.createdAt.localeCompare(b.createdAt));
  res.json(all);
});

app.post("/api/todos", (req: Request, res: Response) => {
  const title = typeof req.body?.title === "string" ? req.body.title.trim() : "";
  if (!title) {
    res.status(400).json({ error: "title is required" });
    return;
  }
  const todo: Todo = { id: randomUUID(), title, completed: false, createdAt: new Date().toISOString() };
  todos.set(todo.id, todo);
  res.status(201).json(todo);
});

app.patch("/api/todos/:id", (req: Request, res: Response) => {
  const todo = todos.get(req.params.id);
  if (!todo) {
    res.status(404).json({ error: "not found" });
    return;
  }
  if (typeof req.body?.completed === "boolean") {
    todo.completed = req.body.completed;
  }
  if (typeof req.body?.title === "string" && req.body.title.trim()) {
    todo.title = req.body.title.trim();
  }
  todos.set(todo.id, todo);
  res.json(todo);
});

app.delete("/api/todos/:id", (req: Request, res: Response) => {
  const existed = todos.delete(req.params.id);
  res.status(existed ? 204 : 404).end();
});

app.listen(PORT, () => {
  console.log(`API listening on http://localhost:${PORT}`);
});
