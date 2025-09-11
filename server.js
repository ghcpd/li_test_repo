import express from 'express';
import http from 'http';
import { Server as SocketIOServer } from 'socket.io';

const app = express();
const server = http.createServer(app);
const io = new SocketIOServer(server);

app.use(express.json());
app.use(express.static('public'));

let tasks = [];
let nextId = 1;

io.on('connection', (socket) => {
  socket.emit('init', tasks);
  socket.on('move', ({ id, status }) => {
    const t = tasks.find((x) => x.id === id);
    if (t) {
      t.status = status;
      io.emit('task_updated', t);
    }
  });
});

app.get('/api/tasks', (req, res) => {
  res.json(tasks);
});

app.post('/api/tasks', (req, res) => {
  const { title, description, dueDate, assignee } = req.body;
  if (!title) return res.status(400).json({ error: 'title required' });
  const task = { id: nextId++, title, description: description || '', dueDate: dueDate || '', assignee: assignee || '', status: 'todo' };
  tasks.push(task);
  io.emit('task_created', task);
  res.status(201).json(task);
});

app.put('/api/tasks/:id', (req, res) => {
  const id = Number(req.params.id);
  const t = tasks.find((x) => x.id === id);
  if (!t) return res.status(404).json({ error: 'not found' });
  const { title, description, dueDate, assignee, status } = req.body;
  if (title !== undefined) t.title = title;
  if (description !== undefined) t.description = description;
  if (dueDate !== undefined) t.dueDate = dueDate;
  if (assignee !== undefined) t.assignee = assignee;
  if (status !== undefined) t.status = status;
  io.emit('task_updated', t);
  res.json(t);
});

app.delete('/api/tasks/:id', (req, res) => {
  const id = Number(req.params.id);
  const idx = tasks.findIndex((x) => x.id === id);
  if (idx === -1) return res.status(404).json({ error: 'not found' });
  const [removed] = tasks.splice(idx, 1);
  io.emit('task_deleted', removed);
  res.json({ ok: true });
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => console.log(`Task board server running on http://localhost:${PORT}`));
